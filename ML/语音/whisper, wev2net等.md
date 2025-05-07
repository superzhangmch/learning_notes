### wav2vec

Wav2Vec 系列主要用于语音的 自监督表示学习，尤其是 Wav2Vec 2.0 在 ASR 中广泛使用；支持通过少量有标注数据微调，获得接近甚至超越传统监督方法的效果；

- Wav2Vec 2.0 的核心创新是将 BERT 风格的 masked prediction 思想引入语音领域，替代原始对比学习方式。
  - Wav2Vec 2.0 是语音 BERT 的雏形：使用对比学习 + mask 机制；
- HuBERT 可以说是 Wav2Vec 系列的升级/演化版之一，但更准确地说，它是继承并改进了 Wav2Vec 2.0 思想的 另一条分支。它们都来自 Facebook AI（Meta AI），也都属于 自监督语音表征学习（self-supervised speech representation learning） 方向。
  - 类似 BERT，预测隐藏的 speech token（聚类获得）
  - HuBERT 更接近 NLP 中的 BERT-style masked LM：用离线聚类先生成 token，再进行 mask prediction；
  - HuBERT 的效果在多个下游任务中比 Wav2Vec 2.0 更好，尤其是在 低资源和语音识别任务 中表现更强。

用它做 asr 流程：
```
原始音频（raw waveform）
        ↓
Wav2Vec 2.0 Encoder（自监督预训练好的特征提取器）
        ↓
上下文表示（contextual embeddings）
        ↓
加一个线性层（CTC head） or Decoder
        ↓
用 CTC loss 训练微调
        ↓
Greedy / Beam Search 解码为文本
```

### whisper
transformer encoder-decoder 结构。不需要 CTC。直接回归做 asr。

另外，whisper 支持识别出的文字的时间戳（在原音频中的时间offset）：方法是通过“char/subword token 与时间戳 token 的交替式自回归”进行联合建模。
