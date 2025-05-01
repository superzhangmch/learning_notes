# qianwen-2-audio https://arxiv.org/pdf/2407.10759 2024.07
qianwen-2-audio 相比一般 LLM，只是 input 增加了 audio（不支持 image)， output 只有 text。

qianwen-2-audio 相比 qianwen-1-audio，在于把固定格式的训练 sequence 数据，变成了自然语言描述。

### 参数量: 
基于 qwen-7B, 总参数量 8.2B

### audio-encoder

audio-encoder：基于 Whisperlarge-v3，并用它初始化。注意 audio encoder 并不同于 audio tokenizer，后者是把语音离散成 token id list，然后再作 embedding。

音频处理：音频先整成 16kHz，再转成 128-channel mel-spectrogram（25ms窗，10ms hop），再经某些操作，最终每帧 40ms

![image](https://github.com/user-attachments/assets/58693b8e-3125-4755-8267-15d8ecaf7b35)

# qianwen-2.5-omni https://arxiv.org/pdf/2503.20215 2025.03

全模态，支持 image、video、audio 作为 input，还支持 audio 作为 output。不过还不能像最新的 gpt-4o 那样支持输出图片。

### 参数量：
开源版 7B。阿里云的闭源版不知多大。

### encoder
- audio-encoder：和 qianwen-2-audio 一样。
- vision-encoder：和 qianwen-2.5-VL 一样， Whisper-large-v3 based, 0.675B。

### 位置编码

LLM 主干上的位置编码：乃 qw-2.5-VL 所用的 3D = (time, height, weight) M-RoPE 位置编码的扩展，名之为 TMRoPE（增加了音频支持）。M-RoPE 中 text token 的位置 id 编码方式是 time=height=weight=pos_id，而对于音频仍同样处理。

一个音频 frame 是 40ms，但是有重叠，hop 长是10ms，所以其实一秒是 100 frame。但是从代码看，会对这100帧下采样到25帧。对audio来说，1 秒就会有 25 个位置 id。

如果是无声video，那么上述位置编码仅仅是把 audio 单作 text 一样，那么和 qw-2.5-VL 的 M-RoPE 就没任何区别了。

video 可能带声音。这时才体现出 TMRoPE 和 M-RoPE 的区别。video 的声音需要和视频同步的，为了保持同步，TMRoPE 的处理方式是，把视频切成 2 秒的片段(chunk)：每个片段先是这两秒的 video frames，紧跟着是伴随声音的 audio frames。为了对齐 video 与 audio，每个 video 的位置id代表的时长也是 40ms。如下图。注意视频帧率不固定，所以 video frame_idx 可能是跳变的，而音频 pos_id 是连续的，但是每个片段的起始 audio pos id 与起始 video pos id 是对齐一致的。

![image](https://github.com/user-attachments/assets/cf4cc581-165c-4585-a203-feb05d1e744a)

一个例子（这里只关注带 audio 的 video 的情形）：
```
[
    {"role": "system", "content": [{"type": "text", "text": "You are Qwen, a virtual human developed by the Qwen Team, Alibaba Group, capable of perceiving auditory and visual inputs, as well as generating text and speech."}]},
    {"role": "user", "content": [{"type": "text", "text": "hello, how are you"}]},
    {"role": "user", "content": [{"type": "video", "video": "aaa.mp4"}] },
]
```
转化成了：
```
==== text: "you are Qwen, a virtual ..., ... hello, how are you "
0: 0 0 0 # 行格式说明: idx: time, height, width. （idx表示同一个  time下的第几个）
0: 1 1 1 # 对于text，time=height=width
0: 2 2 2
...
0: 50 50 50
0: 51 51 51
0: 52 52 52
0: 53 53 53
1: 53 53 53 

==== video： aaa.mp4
# <<< chunk: 按paper是每2秒切一个 token。这里一个chunk 内部抽了2帧，也就是每秒一个frame
# frame 0
0: 54 54 54 # 54 = max(53, 53, 53)
1: 54 54 55
2: 54 54 56
...
741 54 77 82
742 54 77 83
743 54 77 84

# frame 1
0: 79 54 54 # 79=54+25. 而每 25 个连续位置 id 表示 1 秒
1: 79 54 55
2: 79 54 56
...
741 79 77 82
742 79 77 83
743 79 77 84

# audio：这一个 chunk 的视频对应的音频。音频并没像video frame 那样跳着抽一些，而是用了所有，是连续排布下去的
0: 54 54 54 # 对于 time 列来说, chunk内 遇到音频后，发生了取值的后退，从 79 后退到了 54
0: 55 55 55
0: 56 56 56
...
0: 101 101 101
0: 102 102 102
0: 103 103 103

# >>>

# <<< another chunk
# frame 3
0: 104 54 54 # note：其实第一个的h=w=54，保持和video的第一帧的第一个位置一样。
1: 104 54 55
...
742 104 77 83
743 104 77 84

# frame 4
0: 129 54 54
1: 129 54 55
2: 129 54 56
...
741 129 77 82
742 129 77 83
743 129 77 84

# audio
0: 104 104 104
0: 105 105 105
0: 106 106 106
...
0: 151 151 151
0: 152 152 152
0: 153 153 153
# >>>

# <<< another chunk
...
# >>>

# <<< another chunk
...
# >>>
```

以上位置编码方式在 thinker、 talker 上都有应用。

### thinker-talker 两阶段生成

（1）、 当生成 audio output 时，一共需要 4 个 model 参与：
- thinker：transformer结构。用于根据用户的多模态输入生成 text output
- talker：transformer结构。 基于原始 user input 以及 thinker output，生成 speech token ids
- 语音解码：用 flow matching model （类扩散模型）把 speech token ids 转成 mel 谱，再经一个 gan 模型（bigGAN) 把 mel-spectrogram 生成声波。这一步需要两个 model。

关于 talker：除了 user 的原始多模态 input 作为输入，还要把 thinker 的 hidden state 以及据之而得的 sample text 都作为 input。这样看 "talker + 语音解码" 二者大体上就是个 tts 文字转语音的模块。它所生成的语音，和 thinker 的 text output 会基本一致。

不同说话人身份怎么设定的：作为 flow matching model 的一个生成 condition。

（2）、当只需要生成 text output时，只需要 thinker 一个 model 即可

### thinker-talker 实现细节

![image](https://github.com/user-attachments/assets/133b0778-9844-4c8c-a136-95729fe7b1a8)

或者对原图作一些变动后：

![image](https://github.com/user-attachments/assets/02b42d17-0b87-4e30-a4a8-1e4450806e68)

thinker 没啥特别。talker 的 input embs 由三种 embs 求和得到：
- thinker 的 token （包括 user input tokens 与自回归采样出的 tokens） 的 embs
- thinker 的 token 的最后一层的 hidden state 
- talker 的自回归 speech token 的 emb.

解释：这三者求和后当做 speech token 的新 emb 传给 talker transformer。talker 生成的token 数量可能远多余 thinker 的生成token。当前者超过后者后，所拼的thinker 的两项内容就不存在了，这时候只能取一个 padding token 的 emb（即图中白色块的 pad token）。talker 的 "prompt" input 部分并没有speech token 可以对应，这时候 speech token emb 也是取某一特殊 token 的 emb。

二者怎么配合：thinker 与 talker 是在用户input 处理结束后，同步开始生成的：thinker 生成 text，talker 生成 audio，但是 audio 结果的token 数比 text 结果的 token 多，所以 talker 虽然要用到thinker 的tex他output，但基本上不用等待。

为什么 talker 同时需要 thinker 的 token embs 与 token hidden state：
- 有后者，talker 才能及时掌握真正语义，从而知道生成的 audio 应该是怎样的语气语调（tone and attitude）。若只靠 token embs，则只有 thinker 生成结束后才能获得这种信息，那么时延太大。
- 若只用 hidden，不用 token embs 呢？作者说，hidden 只有语义，没有语音，所以需要用 token embs 来确定同一个语义到底用的哪个读音的词（按说 hidden 也蕴含了这点，相比作者试验了这点蕴含还不够？）

### 流式支持

audio encoder：改造成了分块渐进处理音频（这样才不会你巴拉巴拉说一通，等到最后才 encode）。2 秒一个块。

从 speech token 到语音生成（codec generation）：DiT 结构的 flow-matching model 内，有沿时间维度的 transformer(DiT=Diffusion Transformer)。对时间切分block后，以滑窗方式，只关注当前时间邻域内的几个block。attention mask 如下图：

![image](https://github.com/user-attachments/assets/7cdd9c6d-ec28-46fb-abe7-b33b33232858)

### 怎么训练的

pretraining：先有有训好的 LLM，先冻结 LLM 训练 vision、audio encoder，然后解冻 LLM 后在 大规模 text+vision + audio 数据上继续训。这时候，训 talker 吗（文中所 qw2.5-omini 是一个 unified end-to-end model）？

post-training：对于 talker，三阶段训练：
- In-Context Learning (ICL) to learn context continuation：除了 speech token 接龙，还要有 text supervision（这个是说text token 接龙训练吗？这这点对应图中 talker 的 text output 吗？pretraiing 的时候，是否要训 talker？从这里看，感觉不！）
- 类 RLHF 的 DPO 算法来提升 speech generation 稳定性
- multi-speaker instruction fine-tuning 提升自然度与可控性。

### 关于 token id
text 自然有 text token id。作为 input 的 audio、vision，并没用先离散出 token id，然后 token id => embedding 后才feed LLM，而是提取的特征向量直接 feed LLM。但是在输出 audio 的时候，是经过了 audio token id 一步的。也就是说 input audio 和 output audio 并没共享同样的 token id 空间。
