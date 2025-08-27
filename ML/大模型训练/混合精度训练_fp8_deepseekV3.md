
## 背景

关于 deepseek-v3 （ https://arxiv.org/pdf/2412.19437v1 ） 的 fp8 训练的背景介绍，原文摘录如下（3.3节 《FP8 Training》）：

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


## deepseek-v3 的解法

### 一、整体做法

大体上和 fp16、fp32 混合精度训练的思路是一样的：forward、backward 用低精度。而优化器内部用高精度：

<img width="852" height="650" alt="image" src="https://github.com/user-attachments/assets/fc7df4bd-e13f-4c2f-ac29-916942bc24f8" />

主要是对于矩阵乘法做了 FP8，而对下面部分保持高的精度：
- the embedding module
- the output head
- MoE gating modules,
- normalization operators
attention operators

其细节如下图：

<img width="1658" height="668" alt="image" src="https://github.com/user-attachments/assets/054cf088-55d2-4bab-9e0f-a4a17eb2e660" />

拆解开看：

<img width="678" height="616" alt="image" src="https://github.com/user-attachments/assets/11824955-e551-49ce-b022-03e403755594" />

如上图是只考虑 Linear 全连接层的情形。注意看 FP8 GEMM 计算过程：会在 FP32 中累加 (图中 Σ)，这是为了防止低精度时的累加时精度不够，乃 deepseek-v3 的创新之一。另一创新则是为解决 outlier 问题，对矩阵tensor 分小块作 scale。

令 $y=XW$, $Loss = L(y, ..)$, 其中 X = g(..) 是 y 的输入，W 是权重。对 Loss 求梯度时，不但要对 W 求，还要对 X=g(..) 内的参数求。而为求后者，必须先求 $\partial L / \partial X$。于是一次 backward 既要对 W 也要对 X 求梯度。则 $XW$ 在训练时涉及的三类 GEMM（矩阵乘加运算）：

(a) **Fprop (Forward propagation)**

计算是 $XW$, 把输入激活 $X$ 与权重 $W$ 相乘。

(b) **Wgrad (Weight gradient)**

反向传播计算权重的梯度, 计算是 $\nabla W = X^{\top} \nabla y$, 乃外积，其中 $\nabla y = \frac{\partial \mathcal{L}}{\partial y}$。

(c) **Dgrad (Data gradient / Activation gradient)**

这一步进行反向传播里计算输入的梯度, 即 $\nabla X = \nabla y W^{\top}$，把损失梯度 $\nabla y$ 反向传播到输入，供前一层使用。

### 二、实际操作中的细节

#### **(1) outlier 怎么解决**

<img width="712" height="420" alt="image" src="https://github.com/user-attachments/assets/1bdfbe04-0125-4ec1-9c15-998e7d1cf756" />

如图, 假设是要算 $XW = \[ x_1, x_2, .., x_n\] \cdot \[W_1, W_2, .., W_n\]^T$（且本来也不需要分块算）。

如果 X 或者 W 有一两个 outlier，做 tensor-wise scale 会导致绝大部分值归零。于是采用的方法是，矩阵分块：对于 X，按 1 x 128 分，对于权重 W，按 128x128 分，每一块分别 scale：

<img width="860" height="710" alt="image" src="https://github.com/user-attachments/assets/e7247d0d-4c00-4534-b5e8-07f353058060" />

假设每个分块的 scaling 是 $x_i = \lambda_i a_i$, $W_i = \gamma_i B_i$，则本来 $XW = \sum_i x_i W_i$, 现在就变成了 $XW = \sum_i \[(\lambda_i \gamma_i) (a_i\cdot B_i)\]$。

**关于 block size 的选取：**

见上文可见，一共牵扯到三个 GEMM（XW， $\nabla y W^T$, $X^T\nabla y$)，参与的矩阵有
- X=上一层的activation，同时是本层的input
  - block 大小是 $1 \times N_c = 1 \times 128$，构成了 tile-wise
- $\nabla y$=下一层传来的激活梯度(即 Dgrad)。
  - block 大小是 $1 \times N_c = 1 \times 128$
- W=weight
  - block 大小是 $N_c \times N_c = 128 \times 128$

都是矩阵，为什么不统一按 128x128呢？paper中实验结果是就应该不同处理。paper 推测，对 Dgrad 来说：不同 token 的 Dgrad 差异较大，所以 outlier 与token相关吧，因此要不同 token 不能在同一个 block 内。如上导致 $X^T\nabla y$ 是 [128x1] 分块和 [1x128] 分块的两个矩阵相乘。

#### **(2) 矩阵乘累加精度**

**问题产生的原因：**

对 FP8 矩阵 A 与 B，矩阵乘积 AB 的单个元素 $AB_{ij} = \sum_{k=1}^{K} a_{ik} b_{kj}$，累加项中的单项 $a_{ik} \cdot b_{kj}$ 需要比 FP8 更高的精度；鉴于是多项求和，那么其实需要比单项更高的精度。在 GPU 硬件内部，浮点数其实不用 FP16，FP32 这样的格式，而是内部私有格式。就英伟达 H800 GPU 而言，作 FP8 矩阵乘法的时候， $\sum_{k=1}^{K} a_{ik} b_{kj}$ 累积所用的累加器的精度只有 14 bits，并没达到 FP32 的精度。这样累加过程中就有舍入误差。按其文，K=4096 则可能有 2% 的误差。于是 deepseek-v3 的解法是，需要更高的累加精度。

- FP32 作为累加器：FP32 有效数字（mantissa） = 23 + 1(hidden) = 24 bits → 十进制大约能保证 7–8 位有效数字
- H800 FP8 GEMM 累加器：14 bits → 十进制大约只能保证 4–5 位有效数字

如上，若用 14bits，超出14 bit 部分会有舍入误差，如果累加项较小，则直接被丢弃。从而有结果精度问题。

**结合硬件再阐述下**

用英伟达 GPU 计算大矩阵乘法的时候，你是通过 CUDA 这样的东西进行的。你把两个大矩阵传给了它，但是 GPU 核心其实并不支持那么大的矩阵相乘。所以是 CUDA 内部做了分块矩阵乘法，通过代码层循环方式。

也就是说对于 A*B，它大约是这样做的：假设矩阵分块维 A=[A1,A2, ..An], B=[B1,B2,.., Bn]ᵀ, $A \cdot B=\sum_i A_i \cdot B_i$，执行每个 $A_i \cdot B_i$ 是直接调用的 GPU，而 $\sum_i$ 循环是代码层做的。代码层会是循环执行 $C_{i+1} = A_i \cdot B_i + C_i$ "乘&加" 的形式。这个 "乘&加" 可由 gpu 一次完成。

NVIDIA GPU 硬件层面提供的矩阵乘法指令（只记下助理解）：

- FMA (Fused Multiply-Add)：标量级单点计算，如果作矩阵乘法，需要自己写所有循环。
- MMA (Matrix Multiply-Accumulate)
  - V100引入，指令族: mma.sync.* ，warp 级别的矩阵乘加指令。
  - 可计算 shape=[16, 16] x shape=[16, 16] 大小的矩阵乘
- WGMMA (Warp Group MMA)
  - H100/H800，指令族：wgmma.mma_async.* ，**异步**（从指令名可看出）执行，允许流水线化。
  - 可计算 [64, 16] x [16, 128] 或 [64, 32] x [32, 128] 大小的矩阵乘
  ```
  function GEMM(A[M,K], B[K,N]) -> C[M,N]:
    for bm in 0..M step 64:         # 按 64 行分块
        for bn in 0..N step 128:    # 按 128 列分块
            acc = zeros(64,128)     # 累加器寄存器

            for k0 in 0..K step 16: # 沿 K 维分块
                A_tile = A[bm:bm+64, k0:k0+16]
                B_tile = B[k0:k0+16, bn:bn+128]

                acc = WGMMA(acc, A_tile, B_tile)  # 核心：一次 64×128×16 乘加。对于 MMA，伪代码和这个一样。只需 WGMMA=> MMA, 并缩小 tile 大小

            C[bm:bm+64, bn:bn+128] = acc
  ```

