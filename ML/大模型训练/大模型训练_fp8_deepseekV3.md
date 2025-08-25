
### 背景

关于 deepseek-v3 的 fp8 训练的背景介绍，原文摘录如下（3.3节 《FP8 Training》）：

> Inspired by recent advances in low-precision training（见下面引文A,B,C）, we propose a fine-grained mixed precision framework utilizing the FP8
data format for training DeepSeek-V3.
>
> 【受到别的 fp8 方案启发】
- A=《Gpt3. int8 (): 8-bit matrix multiplication for transformers at scale》- 2022.08 - https://arxiv.org/pdf/2208.07339
  - int8 量化来提速推理：Int8 矩阵乘法方案，用在 Transformer FFN 和 Attn proj。
  - 发现特征维度中有一些 outliers 影响量化效果：于是分而治之。
  - <img width="1000" alt="image" src="https://github.com/user-attachments/assets/752d7062-b186-474e-b1b9-5962ecde0542" />
- B=《8-bit numerical formats for deep neural networks》- 2022.06 - https://arxiv.org/pdf/2206.02915
  - 关注训练。用浮点 fp8 比 fixed-point（int8） 好。并推荐：激活/权重用 1.4.3，梯度用 1.5.2
  - 用全局 loss scale 而非细粒度 scale（且正因此比定点的好：定点情况，需要逐层细粒度 scale）
- C=《FP8-LM: Training FP8 large language models》 - 2023.10 - https://arxiv.org/pdf/2310.18313

> While low-precision training holds great promise, it is often limited by the presence of outliers in activations, weights, and gradients（见下面引文D,E）.
>
> 【但是当前的 fp8 总是受困于 outlier 问题】
- D=《Scaling FP8 training to trillion-token llms》- 2024.09 - https://arxiv.org/pdf/2409.12517
  - 用 2T token 训了个 7B model，发现 fp8 的训练不稳来自 SwiGLU 导致的异常值放大，并用 Smooth-SwiGLU 改进之。
- E=《Massive activations in large language models》 - 2024.02 - https://arxiv.org/pdf/2402.17762
  - 极少数超大 outlier 激活值普遍存在于各 LLM（乃至大出 10 万倍），文中叫这 outliers 为 massive activations（且见于 paper 标题）。
    - 此文并不是讲 FP8 训练才如此。而是各种精度的都有可能
  - 某些维、某些 token 才容易发生
    - 不是所有 channel 都 massive：outliers 总是出现在某些 channel 维度（且出现几率很小）。
    - 不是所有 token 都 massive：在一些特殊 token 上（起始 <BOS>、句号 “.”、换行符 \n、分隔符等）才如此。
    - <img width="1162" height="658" alt="image" src="https://github.com/user-attachments/assets/293d84b3-e8b3-471c-a250-1d7633336fb2" />
  - 他们起的作用是 biases，若去掉之会性能下降（Massive activations act as fixed but important biases in LLMs）。attn 中相当于隐式 bias

> Although significant progress has been made in inference quantization (见下面引文F,G), there are relatively few studies demonstrating successful application of low-precision techniques in large-scale language model pre-training (见下面引文 D).
>
> 【推理量化有进展，但是大规模低精度训练的成功还未见】
- 推理时量化：
  - F：《Gptq: Accurate post-training quantization for generative pre-trained transformers》- 2022.10 - https://arxiv.org/pdf/2210.17323
  - G：《Smoothquant: Accurate and efficient post-training quantization for large language models》 - 2022.11 - https://arxiv.org/pdf/2211.10438
- D：《Scaling FP8 training to trillion-token llms》- 2024.09 - （注意上面也出现了） https://arxiv.org/pdf/2409.12517
  - 用 2T token 训了个 7B model，发现 fp8 的训练不稳来自 SwiGLU 导致的异常值放大，并用 Smooth-SwiGLU 改进之。

> To address this challenge and effectively extend the dynamic range of the FP8 format, 【于是推出 deepseek-v3 的解法】
>
> （1）、we introduce a fine-grained quantization strategy: tile-wise grouping with 1 × 𝑁𝑐 elements or block-wise grouping with 𝑁𝑐 × 𝑁𝑐 elements. The associated dequantization overhead is largely mitigated under our increased-precision accumulation process, a critical aspect for achieving accurate FP8 General Matrix Multiplication (GEMM).
>
> （2）、Moreover, to further reduce memory and communication overhead in MoE training, we cache and dispatch activations in FP8, while storing low-precision optimizer states in BF16.
>
> （3）、We validate the proposed FP8 mixed precision framework on two model scales similar to DeepSeek-V2-Lite and DeepSeekV2, training for approximately 1 trillion tokens (see more details in Appendix B.1). Notably, compared with the BF16 baseline, the relative loss error of our FP8-training model remains consistently below 0.25%, a level well within the acceptable range of training randomness.
