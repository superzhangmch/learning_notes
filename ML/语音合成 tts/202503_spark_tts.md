# 《Spark-TTS: An Efficient LLM-Based Text-to-Speech Model with Single-Stream Decoupled Speech Tokens》 https://arxiv.org/pdf/2503.01710

它的基本方法，和 cozyvoice 一样，用通用预训练的 LLM 作为主干，对于语音都 token 化。所以很天然支持语音 clone。

- cosyvoice： token => mel谱 => wave， token => mel谱，需要 flow matching。
- spark-tts 不需要这样。token 一步到达 wave。

----

### biCodeC tokenizer

不但抽token，还能根据 token 还原语音。

<img width="886" height="532" alt="image" src="https://github.com/user-attachments/assets/e4b016c8-85ba-40f6-8126-78c7fc844ed9" />

网络结构如下（乃一自编码器）：

<img width="1090" height="710" alt="image" src="https://github.com/user-attachments/assets/9c6e6485-223a-4441-8641-42cd16b34387" />

**ConvNeXt，可以理解为：**
- 结构像 ResNet（分 Stage，下采样，残差连接）。
- 风格像 ViT（LN、GELU、大感受野、深宽设计）。
- 性能接近或超过 ViT，同时保持 CNN 的高效性。

### 语音怎么生成的：BiCodec decoder

用 BiCodec 的 decoder。

一般做生成，是用 gan 或者 diffusion 类（比如 flow matching）。而 BiCodec 乃基于 VQ-VAE 的 autoencoder，但用了 GAN 训练方法：
> BiCodec is trained end-to-end employing a **Generative Adversarial Network (GAN)** methodology to minimize reconstruction loss, together with L1 feature matching loss (via discriminators) while simultaneously optimizing the VQ codebook.

### 主流程

<img width="1158" height="696" alt="image" src="https://github.com/user-attachments/assets/b6c0a787-edd8-494f-8390-2d5d1c47da01" />

- Attribute，可提供： pitch level, speed level

训练 loss 如下：

<img width="914" height="570" alt="image" src="https://github.com/user-attachments/assets/b1f9d0a1-9074-4967-9ad7-bbe6cb447580" />

两种 loss 分别在预测下面部分：

<img width="800" height="522" alt="image" src="https://github.com/user-attachments/assets/9951e552-1adb-4009-81ea-fc5a905deead" />

### 怎么做的语音迁移

用 biCodec 的 global token 来做。
