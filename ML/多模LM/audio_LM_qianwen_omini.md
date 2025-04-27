# qianwen-2-audio https://arxiv.org/pdf/2407.10759 2024.07
更早的 qianwen-1-audio 就不论了。qianwen-2-audio 相比一般 LLM，只是 input 增加了 audio， output 只有 text。

参数量: 基于 qwen-7B, 总参数量 8.2B

audio-encoder：基于 Whisperlarge-v3，并用它初始化。 

音频处理：音频先整成 16kHz，再转成 128-channel mel-spectrogram（25ms窗，10ms hop），最终每帧 40ms

![image](https://github.com/user-attachments/assets/58693b8e-3125-4755-8267-15d8ecaf7b35)

# qianwen-2.5-omni https://arxiv.org/pdf/2503.20215 2025.03
