
### whisper
transformer encoder-decoder 结构。不需要 CTC。直接回归做 asr。

另外，whisper 支持识别出的文字的时间戳（在原音频中的时间offset）：方法是通过“char/subword token 与时间戳 token 的交替式自回归”进行联合建模。
