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
- vision-encoder：和 qianwen-2.5-VL 一样， 0.675B。

### 位置编码

LLM 主干的位置编码：乃 qw-2.5-VL 所用的 3D = (time, height, weight) 位置编码 M-RoPE 的扩展，名之为 TMRoPE（增加了音频支持）。M-RoPE 中，text token 的位置 id 编码方式是 time=height=weight=pos_id。 对于音频仍同样处理，且一个音频 token 对应 于 audio-encode 的一个 frame = 40ms。这使得一个位置 id 对应于 40ms 长时间（视频的位置 id 也是 40ms）。

如果是无声video，那么上述位置编码仅仅是把 audio 单作 text 一样，那么和 qw-2.5-VL 的 M-RoPE 就没任何区别了。

video 可能带声音。这时才体现出 TMRoPE 和 M-RoPE 的区别。

![image](https://github.com/user-attachments/assets/cf4cc581-165c-4585-a203-feb05d1e744a)
