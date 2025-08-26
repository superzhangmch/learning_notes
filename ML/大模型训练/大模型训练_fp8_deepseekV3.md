
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
  - 关注训练。
  - 用浮点 fp8 比 fixed-point（int8）好。
    - 定点 int8 可表示的数列，相邻间隔固定。而 fp8，则是间隔不一（0 附近精细，而绝对值越大，约粗）。而神经网络的参数激活梯度等都是零均值的。所以用 fp8 更好。
    - <img width="1096" height="846" alt="image" src="https://github.com/user-attachments/assets/afd8684e-62aa-423f-87fd-1d14469d71b7" />
    - fp8 表示的非线性性如图，可参 https://asawicki.info/articles/fp8_tables.php。注意 E4M3 还有一种算法范围是 -448~448.
  - 推荐：激活/权重用 fp8=E4M3，梯度用 fp8=E5M2
  - 它用了全局 loss scale 而非细粒度逐层或逐张量 scale
- C=《FP8-LM: Training FP8 large language models》 - 2023.10 - https://arxiv.org/pdf/2310.18313
  - Nvidia Transformer Engine只对矩阵乘法用 fp8，本文把 FP8 应用到计算、存储和通信全过程，包括梯度、优化器状态和分布式训练。
  - per-tensor scaling
  - 精度分配
    - 主权重 fp16, 优化器adam状态：fp8（一阶）+fp16（二阶）；梯度 fp8。这些本来一个参数需要16字节，变成了 6字节
    - forward、backward 时，关键地方外（GELU、Softmax、LayerNorm, dropout等），都是 fp8

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

从以上的启示是，用 fp8 有好处，但是总是有异常大值（outliers）问题。deepseek-v3 试图解决这点。

### deepseek-v3 的解法

#### （1）整体做法

<img width="1658" height="668" alt="image" src="https://github.com/user-attachments/assets/054cf088-55d2-4bab-9e0f-a4a17eb2e660" />

如上图只考虑 **Linear 层**（全连接层）。令 $y=XW$, $Loss = L(y, ..)$, 其中 X = g(..) 是 y 的输入，W 是权重。

注意对 Loss 求梯度时，不但要对 W 求，还要对 X=g(..) 内的参数求。而为求后者，必须先求 $\partial L / \partial X$。于是一次 backward 既要对 W 也要对 X 求梯度。

下面看 $XW$ 在训练时涉及的三类 GEMM（矩阵乘加运算）：

(1) **Fprop (Forward propagation)**

涉及计算是 $XW$, 把输入激活 $X$ 与权重 $W$ 相乘。

对应上图中，这个 GEMM 在 FP8 计算，但结果会在 FP32 中累加 (图中 Σ)，最后存成 BF16/FP32。

(2) **Wgrad (Weight gradient)**

反向传播里计算权重的梯度, 涉及计算是

$$
\begin{cases}
\nabla y &= \frac{\partial \mathcal{L}}{\partial y} \\
\nabla W &= X^{\top} \nabla y
\end{cases}
$$

即用输入 $X$ 和损失对输出的梯度 $\nabla y$ 反向计算权重更新方向。

对应上图中，这个 GEMM 在FP8 执行，然后进入 FP32 累加(Σ), 并最终用于更新 FP32 主参数。

(3) **Dgrad (Data gradient / Activation gradient)**

这一步进行反向传播里计算输入的梯度, 即

$$
\nabla X = \nabla y W^{\top}
$$

把损失梯度 $\nabla y$ 反向传播到输入，供前一层使用。

对应上图中, 这个 GEMM 同样在 FP8 执行，并在 FP32 累加(图中 Σ), 并 cast 维 FP16 供上一层求梯度用。

换个形式看：

<img width="852" height="650" alt="image" src="https://github.com/user-attachments/assets/fc7df4bd-e13f-4c2f-ac29-916942bc24f8" />
