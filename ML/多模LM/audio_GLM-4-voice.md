### 参数量
LLM 部分是 9B。

### 支持模态
audio input + audio output，不支持 vision。

### audio tokenizer 与 decoder

**（1）、audio tokenizer**

不像 qianwen-2.5-omini 用了 audio-encoder，glm-voice 是用的 tokenizer——也就是把 audio 离散 token 化，然后 embedding。

如下图，在 whisper-large-v3 的 encoder 的中间插入 vector 量化层，然后作一定 fine tune。最后取 encoder 的一半（截止到量化层），作为 tokenizer。

![image](https://github.com/user-attachments/assets/25c239e5-fd5c-449f-a631-6a12bc6bf1e2)

最终的 tokenizer 对一秒 audio 编码出 12.5 个 token (12.5HZ)。根据 glm-4-voice 所依赖的前作 https://arxiv.org/pdf/2411.17607 (也是他们团队的），codebook 大小是 2^14=16384, 即一个 token 占用 14个bit。14*12.5=175，所以文中说，他们的 tokenizer 是 175 bits/sec 的超高压缩率的。

为支持流式 encoding，也有相应改造（卷积以及双向 attention，都变成了 causal 风格的）。

**（2）、audio decoder**

上述 audio tokenizer 生成的 speech tokens，既用于audio input 编码，也用于 audio output 生成。

为了从 speech tokens 中生成 audio，要经过两个model：类似扩散模型的 flow matching（tokens => mel谱)，以及 GAN 模型(mel谱 => audio wave)。

![image](https://github.com/user-attachments/assets/43a3af74-3016-4b1e-835d-473f7fd292da)

上面的 tokenizer 方法，据作者讲，受到了 cosyvoice 的 tokenizer 所启发。而 flow_matching + GAN 的 decoder，模型架构直接借自 cosyvoice。

