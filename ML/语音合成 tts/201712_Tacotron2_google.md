# Tacotron 2：《NATURAL TTS SYNTHESIS BY CONDITIONING WAVENET ON MEL SPECTROGRAM PREDICTIONS》 https://arxiv.org/pdf/1712.05884

### 流程：
character list => mel谱 => audio_wave
- char list => mel spectrogram :通过 带注意力机制的 RNN 序列到序列（Seq2Seq）模型实现的
  - ```Char List → Embedding → CNN（提取局部上下文） → Bi-LSTM → Attention → Decoder（RNN） → Mel Spectrogram```
- mel => audio: 用的 WaveNet 改进版

![image](https://github.com/user-attachments/assets/404d1e84-d92a-4003-8aaf-ecad8f1368bc)

### 中文怎么处理的？

它假设有了 text token list 了。所以各种语音都应该设法转为一种 token list。放 2025 年的现在看，原始语音直接 tokenize 就是了。但是在当时似乎还不是这样。看一些资料，中文需要先转为带声调拼音，然后再作 tacotron2。
