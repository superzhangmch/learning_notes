# qianwen-2-audio https://arxiv.org/pdf/2407.10759 2024.07
更早的 qianwen-1-audio 就不论了。qianwen-2-audio 相比一般 LLM，只是 input 增加了 audio， output 只有 text。

### 参数量: 
基于 qwen-7B, 总参数量 8.2B

### audio-encoder
audio-encoder：基于 Whisperlarge-v3，并用它初始化。 

音频处理：音频先整成 16kHz，再转成 128-channel mel-spectrogram（25ms窗，10ms hop），最终每帧 40ms

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

### thinker-talker 两阶段生成

