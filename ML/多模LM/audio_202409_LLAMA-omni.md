# https://arxiv.org/pdf/2409.06666 《LLAMA-OMNI: SEAMLESS SPEECH INTERACTION WITH LARGE LANGUAGE MODELS》

**支持模态**: 名为 omni，但不支持 vision。

**参数量**： 基于 Llama-3.1-8B-Instruct

### speech encoder
Whisper-large-v3.

### 语音怎么生成的

虽然生成时也用到了 speech tokens（HuBERT 的表示经 k-means 聚类得到离散 token），但并不是自回归出 output speech tokens，而是在基于 output text 的 hidden 表示，直接预测出 speech tokens。这样就有 speech tokens 与 output text tokens 的对齐问题，于是用 CTC 方式做的对齐（为此要先把 text tokens 序列长度通过 upsample 拉长）。

它的语音生成，虽然流程上是和 text 同步生成，但是还是text 先行，边升成 text 边跟读出 audio。这和其他各家 audio-LM 一样。

![image](https://github.com/user-attachments/assets/ab9d1d9c-6e84-484c-a168-b8ca1f1aa0eb)

预测出的 speech tokens 经过 vocoder 编程 audio wave：unit-HiFi-GAN vocoder with a duration predictor（每个离散 token 可能对应不同的时间长度，为了生成自然流畅的语音，需要预测每个 token 的持续时间）。

别家都是 speech tokens => mel谱 => audio wave。它是一步到位。和比它稍早的《speechGPT》所用方法一样，都是用的 unit vocoder。

unit-hifi-gan vocoder: 来自 paper [Speech Resynthesis from Discrete Disentangled Self-Supervised Representations](https://arxiv.org/pdf/2104.00355), 它就是用 hubert 得到的离散语音 tokens 直接跳过 mel-谱得到语音的（用了 hifi-gan 结构。hifi-gan本来input是mel-谱，shape=[bs, seq_len, 80]。现在用 shape=[bs, seq_len] 的 speech tokens 作为input，经过 embedding 后，shape=[bs, seq_len, emb_dim]， 正好满足 hifi-gan 的 input 要求。但这篇paper 中没提到 duration predictor）。
