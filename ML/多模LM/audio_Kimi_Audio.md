# 《Kimi-Audio Technical Report》 https://arxiv.org/pdf/2504.18425

### 参数量
7B

### 支持哪些模态
audio input + audio output，不支持 vision。

### audio tokenizer 与 decoder

**（1）、audio 的编码**

它用了两种方式来编码 audio input：glm-4-voice 用到的 audio-tokenizer，以及 whisper 的 encoder。

whisper 本身是 encoder-decoder 结构的，encoder 的输出是高度语义化(semantic)的特征，glm-4-voice 觉得 audio token 应该在 acoustic & Semantic 上取得平衡，所以它的 audio-tokenizer 其实就是从 whisper encoder 中间层量化得到的。而 kimi-audio 觉得只用这个还不够，于是追加使用 whisper-encoder。这两者都是 whisper 的，可以说一个是一半的 whisper-encoder，一个是完整的whisper-encoder。

当然，glm-4-voice-audio-tokenizer 所得到的是离散的 token id，使用时还需要 embeddding 化，而 Whisper-encoder 结果本身就是连续表示了。后者是 50HZ 的，因此需要adaptor下采样成 tokenizer 的 12.5HZ。

**（2）、audio 的解码生成**

生成 audio output 时，是通过对 audio token 自回归完成的，且 input 和 output 所用 audio token 空间是一致的。

和 glm-4-voice 等一样，audio decoder 是 flow-matching（token => mel谱） + GAN（BigGAN，mel谱=>audio wave) 的组合。为低延迟，flow-matching 要 chunk 化处理。 

### 整体怎样工作

经看代码，对原 paper 中图改编下如下：

![image](https://github.com/user-attachments/assets/58ab09e6-19f4-468e-bc3e-96e103a2d7fa)
