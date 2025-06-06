# 《Step-Audio: Unified Understanding and Generation in Intelligent Speech Interaction》 https://arxiv.org/pdf/2502.11946

### 参数量
LLM 部分是 130B。比其他各家的不到 10B 大很多。

### 支持哪些模态
paper 中：整个 model 是支持 audio、vision input，以及 audio output 的。

开源出的 model 里：不支持 vision，而且即使 audio，也只是先生成 text，然后经 tts 步骤变成语音。

### audio 怎么处理

首先它对于 audio 的input、output，都是 tokenize 成 audio tokens 来处理，且 input、output 用同一个 tokens 空间。

glm-4-voice 中就提到 audio 的声学(acoustic)与语义(sementic)特征的矛盾与权衡问题。step-audio 也面临差不多问题（不过不是简单平衡这两者）。它经过实验，最终选用方法是，同时采用两种tokenizer：把两者获得的 tokens 交错排布到一个数组里。

具体说来：
- linguistic tokenization（编码语音phonemic、语言结构等）：Paraformer encoder 结果量化成 16.7 Hz token 率，codebook size=1024。
- semantic tokenization（编码语义与粗粒度声学特征）：直接用 CosyVoice 的 tokenizer，25 Hz 的 token 率。codebook size=4096。

16.7 HZ : 25 HZ = 2:3, 为了平衡两者 tokenizer 不同的每秒token数，于是按 2:3 的比例把两种 tokens 交错混合。在生成 audio 的时候，也是从交错的 audio tokens 中解码出音波（ audio tokens => wave, 经过 flow_matching 等，和别家 model 方式就是一样的了）。

### 整体怎样工作

理想情况下的流程还是比较直接的：

![image](https://github.com/user-attachments/assets/e8756678-78d2-43f9-8751-e7869bd48f88)

但是，实际采用的是 130B 大模型 audio/text => text, 再由 3B 的 tts model 把 text => audio 的流程。别家 audio model，也是跟着 text 读，照读的时候 model 会看到 audio 特征，step-audio 的最终方案是完全独立的 tts。

它这样选择，paper中说是高质训练数据稀缺，以及独立tts的生成可控性高。但是原则上，是可以不用外接 tts 而直接完成audio 生成的。

另外，虽然支持 audio 作为input，但是只有当前轮的语音是原始 audio，历史轮用的是 asr 的 text。

### 开源出的 model 和 paper 差异

**（1）、130B model 能不能直接生成 audio tokens**

paper 中提到，他们用 130B model 蒸馏出了的 3B 的 Step-Audio-TTS-3B。但是开源出的 130B model 本身只能生成 text，后面接的 tts 所用的 model 反而正好是这个 Step-Audio-TTS-3B。且 130B model 与 3B model 网络结构一样（只是层数等超参数不同），经实验把作 tts 的 3b model 换成 130B model，并不能作 tts。那么这个 130B model，到底能不能直接生成 audio tokens？

- https://github.com/stepfun-ai/Step-Audio/issues/114
- https://github.com/stepfun-ai/Step-Audio/issues/104
- https://github.com/stepfun-ai/Step-Audio/issues/55 （这里有 stepFunc 的人的回复：如果是 130B model 直接输出 audio tokens，则 16.7+25=41.7Hz 的token率生成，没法实时完成）

从以上几个看，130B 是可以直接生成 audio tokens。但是大概故意微调屏蔽了这个功能，或者需要恰当 prompt 激活。

**（2）、3B 的 model，怎么做 tts 生成的？**

3B 的 Step-Audio-TTS-3B，内部也有一个 LM——且就是 130B 缩小版而已。所以做tts 生成时，是像使用一个小型的 audio-LLM 一样的方式：直接用 prompt（text + audio prompt）驱动。它的prompt, 大体长这样：
```
[system]

作为一名卓越的声优演员，你的任务是根据文本中（）或()括号内标注的情感、语种或方言、音乐哼唱、语音调整等标签，以丰富细腻的情感和自然顺畅的语调来朗读文本。
# 情感标签涵盖了多种情绪状态，包括但不限于：
- "高兴1"
- "高兴2"
- "生气1"
- "生气2"
- "悲伤1"
- "撒娇1"

# 语种或方言标签包含多种语言或方言，包括但不限于：
- "中文"
- "英文"
- "韩语"
- "日语"
- "四川话"
- "粤语"
- "广东话"

# 音乐哼唱标签包含多种类型歌曲哼唱，包括但不限于：
- "RAP"
- "哼唱"

# 语音调整标签，包括但不限于：
- "慢速1"
- "慢速2"
- "快速1"
- "快速2"

请在朗读时，使用[{}]的声音，根据这些情感标签的指示，调整你的情感、语气、语调和哼唱节奏，以确保文本的情感和意义得到准确而生动的传达，如果没有()或（）括号，则根据文本语义内容自由演绎。

[human]
那等我们到海洋馆之后，给妈妈买个礼物，好不好呀？ # 示例 tts text
[assistant]
xxxx.wav                                 # 示例 text="那等我们到海洋馆之后，给妈妈买个礼物，好不好呀？" 的 audio

[human]
我有一座房子面朝大海春暖花开                  #  希望作 tts 生成的 text
[assistant]
```

130B model 的 text 结果里，实测发现：如果用原始代码中的system-prompt "适配用户的语言，用简短口语化的文字回答。", 并不会触发 130B model 产生上面那些标签。如果修改 130B 的 system prompt引导model输出这些标签，则会有。比如改成:
```
适配用户的语言，用简短口语化的文字回答。在回答时，要在文本中用括号（）或()标注出text 的朗读情感、语种或方言、音乐哼唱、语音调整等标签。

# 情感标签涵盖了多种情绪状态，包括但不限于：
- "高兴1"
- "高兴2"
- "生气1"
- "生气2"
- "悲伤1"
- "撒娇1"

# 语种或方言标签包含多种语言或方言，包括但不限于：
- "中文"
- "英文"
- "韩语"
- "日语"
- "四川话"
- "粤语"
- "广东话"

# 音乐哼唱标签包含多种类型歌曲哼唱，包括但不限于：
- "RAP"
- "哼唱"

# 语音调整标签，包括但不限于：
- "慢速1"
- "慢速2"
- "快速1"
- "快速2"

note: 对于音乐标签，应该出现在输出文本的最前面。
```

### 关于唱歌

step-audio 是目前几个同类model中唯一一个提到自己唱歌能力的。它的实现是通过弄了额外的带歌词唱歌数据来加强训练训出来的。
