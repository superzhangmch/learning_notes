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

LLM 主干上的位置编码：乃 qw-2.5-VL 所用的 3D = (time, height, weight) M-RoPE 位置编码的扩展，名之为 TMRoPE（增加了音频支持）。M-RoPE 中 text token 的位置 id 编码方式是 time=height=weight=pos_id，而对于音频仍同样处理。一个音频 token 对应 audio-encode 的一个 40ms frame，故一个位置 id 也是 40ms。

如果是无声video，那么上述位置编码仅仅是把 audio 单作 text 一样，那么和 qw-2.5-VL 的 M-RoPE 就没任何区别了。

video 可能带声音。这时才体现出 TMRoPE 和 M-RoPE 的区别。video 的声音需要和视频同步的，为了保持同步，TMRoPE 的处理方式是，把视频切成 2 秒的片段：每个片段先是这两秒的 video frames，紧跟着是伴随声音的 audio frames。为了对齐 video 与 audio，每个 video 的位置id代表的时长也是 40ms。如下图。注意视频帧率不固定，所以video frame_idx 可能是跳变的，而音频 pos_id 是连续的，但是每个片段的起始 audio pos id 与起始 video pos id 是对齐一致的。

![image](https://github.com/user-attachments/assets/cf4cc581-165c-4585-a203-feb05d1e744a)

### thinker-talker 两阶段生成

