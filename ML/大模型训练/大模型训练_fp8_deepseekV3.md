
### 《deepseek-v3》paper：3.3节 FP8 Training

> Inspired by recent advances in low-precision training（见下面三个引文）, we propose a fine-grained mixed precision framework utilizing the FP8
data format for training DeepSeek-V3.
>
> 【受到别的 fp8 方案启发】
- 《Gpt3. int8 (): 8-bit matrix multiplication for transformers at scale》- 2022.08 - https://arxiv.org/abs/2208.07339
- 《8-bit numerical formats for deep neural networks》- 2022.06 - https://arxiv.org/abs/2206.02915
- 《FP8-LM: Training FP8 large language models》 - 2023.10 - https://arxiv.org/abs/2310.18313

> While low-precision training holds great promise, it is often limited by the presence of outliers in activations, weights, and gradients（见下面两个引文）.
>
> 【但是当前的 fp8 总是受困于 outlier 问题】
- 《Scaling FP8 training to trillion-token llms》- 2024.09 - https://arxiv.org/abs/2409.12517
- 《Massive activations in large language models》 - 2024.02 - https://arxiv.org/abs/2402.17762

> Although significant progress has been made in inference quantization (见下面两个引文 A 与 B), there are relatively few studies demonstrating successful application of low-precision techniques in large-scale language model pre-training (见下面引文 C).
>
> 【推理量化有进展，但是大规模低精度训练的成功还未见】
- A：《Gptq: Accurate post-training quantization for generative pre-trained transformers》- 2022.10 - https://arxiv.org/abs/2210.17323
- B：《Smoothquant: Accurate and efficient post-training quantization for large language models》 - 2022.11 - https://arxiv.org/abs/2211.10438
- C：《Scaling FP8 training to trillion-token llms》- 2024.09 - （注意上面也出现了） https://arxiv.org/abs/2409.12517

> To address this challenge and effectively extend the dynamic range of the FP8 format,
>
> （1）、we introduce a fine-grained quantization strategy: tile-wise grouping with 1 × 𝑁𝑐 elements or block-wise grouping with 𝑁𝑐 × 𝑁𝑐 elements. The associated dequantization overhead is largely mitigated under our increased-precision accumulation process, a critical aspect for achieving accurate FP8 General Matrix Multiplication (GEMM).
>
> （2）、Moreover, to further reduce memory and communication overhead in MoE training, we cache and dispatch activations in FP8, while storing low-precision optimizer states in BF16.
>
> （3）、We validate the proposed FP8 mixed precision framework on two model scales similar to DeepSeek-V2-Lite and DeepSeekV2, training for approximately 1 trillion tokens (see more details in Appendix B.1). Notably, compared with the BF16 baseline, the relative loss error of our FP8-training model remains consistently below 0.25%, a level well within the acceptable range of training randomness.
