《Mamba: Linear-Time Sequence Modeling with Selective State Spaces》 https://arxiv.org/pdf/2312.00752

<img width="720" height="630" alt="image" src="https://github.com/user-attachments/assets/d1daff8e-3170-4f68-8ae6-79b60a2e4d51" />

Mamba block 如上。每一步不用像 attn 那样作序列全扫描，但相比 transformer，它内部的 hidden 维度特别大，所以才能保持性能。

这里先记述 mamba 的一些依赖知识与前序 model，然后是 mamba。顺序是 SSM -> S4 -> H3 -> mamba。

----

## SSM： 状态空间模型，State Space Models

SSM 并不是因机器学习的问题而特意创造出来的，而是一类应用很广泛的通用模型，只是后来被借用到了机器学习领域。据 ai（姑信之）：最初来自控制理论，后来被广泛应用于信号处理、时间序列分析、物理建模和机器学习等领域。

它的基本设定是，有一个随着时间 t 而变化的实值 input 信号 $u_t$，期望建模出随时间 t 同步变化的实数值 output 信号 $y_t$。时间 t 可能是连续的，也可能是离散的。也就是它解决的是**一维的序列到序列**的转换问题。

### 连续形式的 SSM

**（1）、最一般形式**

对于最一般的 SSM，可以用这样的一阶线性微分方程来描述它（为啥是这形式？SSM 规定了就是此形式而已。）：

$$
\begin{cases}
\frac {d x(t)}{dt} =A(t) x(t)+B(t) u(t) \\
y(t)=C(t) x(t)+D(t) u(t) \\
\end{cases}
​$$

其中 u(t)、y(t)、D(t)  $\in \mathbb{R}$, 且 A(t)、B(t)、C(t)、D(t) 都是随着t变化的， A(t)是方阵，x(t)、B(t)、C(t) 是向量，x(t) 是 hidden state。

**（2）、实际所用形式**

而更实用与实际的形式是这样的：

$$
\begin{cases}
\frac {d x(t)}{dt} = A x_t + B u_t \\
y_t = C x_t + D u_t \\
\end{cases}
$$

A、B、C、D 都是 constant 的（这叫 Linear Time Invariance (LTI)，时间不变）。即为常系数微分方程。且 D 可以进一步为 0，下面都令 D=0。

note：假设 SSD hidden state 维度是 m，则 $A \in \mathbb{R}^{m x m}$, B、C $\in \mathbb{R}^{m}$， 而 y_t 就是两个 m 维向量的向量积。

**(3)、方程求解**

对于上面的一阶线性常系数微分方程，用解微分方程的常规做法，可以从数学上解出（AI 给出）： 

$$x(t)=e^{A(t-s)}x(s)+\int_s^t e^{A(t−τ)}\cdot B \cdot u(τ) dτ$$

其中时间 0 <= s <= t。

【若令 x(0) = 0, 则 $x(t)=\int_0^t e^{A(t−τ)}\cdot B \cdot u(τ) dτ$。此时若令 $K(t−τ) = \int_0^t e^{A(t−τ)}\cdot B$, 则 

$$y_t = \int_0^t [C e^{A(t−τ)} B] \cdot u(τ) dτ = \int_0^t K(t−τ) u(τ) dτ$$

这正是数学上卷积形式（不同于 CNN 中的那种局部卷积）】

### SSM 离散化（Discretization）

**（1）、离散化**

对上面的连续取值的微分方程 $\frac {d x(t)}{dt} = A x_t + B u_t$, 可以离散化的（离散成差分方程），比如 euler 方法。

而 SSM 常用的方法叫 ZOH 法（Zero-Order Hold），做法大约为：对 input u 把时间 t 平均切分成一段一段，令每一小段内的取值都等于小段起始点的取值 u_t（从而光滑连续信号变成了阶梯连续信号）。在这阶梯信号 u_t 下，原方程仍然有效，其解仍是前述形式（若 u_t 是某种极其不规则的不连续态，并不能这样做。u_t 为阶梯函数，则还可以）。于是对跳变点{u_t}, 代入解公式得到{x_t}, 就可以得到离散化式子了。

具体说来：

假设相邻时间离散点的时间差是 Δ， 把 s=t-Δ 代入精确解析解有：

$$x(t)=e^{AΔ}x(t-Δ)+\int_{t-Δ}^t e^{A(t−τ)}\cdot B \cdot u(τ) dτ$$

令 $x_s:= x(t),\ x_{s-1}:=x(t-Δ)$, 根据 ZOH 离散化定义有 $u_{new}(t-Δ \le . \le t) := u(t)$，于是代入上式有：

$$
\begin{align}
x_s&=e^{AΔ} x_{s-1} + u(t) \int_{t-Δ}^t e^{A(t−τ)}\cdot B  dτ \\
 &=e^{AΔ} x_{t-1} + u(t) \int_0^Δ e^{Aτ }\cdot B  dτ \\
 &=e^{AΔ} x_{t-1} + u(t) [\int_0^Δ e^{Aτ }\cdot dτ] B  & //数学上有：\int_0^Δ e^{Aτ }\cdot dτ = A^{-1} (e^{AΔ}−I)$, 注意 A 是矩阵 \\
 &= e^{AΔ} x_{t-1} + u(t) A^{-1} (e^{AΔ}−I)B
\end{align}
$$

令 $\bar{A} = e^{AΔ}, \bar{B} = A^{-1} (e^{AΔ}−I)B$, 则 $x_s = \bar{A} x_{s-1} + \bar{B} u_s$ 就是离散后的 SSM 了。这正是 《mamba》paper 中的公式4 (那里x表示input）：

<img width="1024" alt="image" src="https://github.com/user-attachments/assets/778543b1-8278-4cb8-b997-3020aa7ba7b5" />

note： $\bar{A} \in \mathbb{R}^{m x m}$, $\bar{B} \in \mathbb{R}^{m}$

**和 RNN 的区别：RNN vs SSM:**

| 维度         | RNN（Recurrent Neural Network）                  | SSM（State Space Model）         |
| ---------- | ---------------------------------------------- | ------------------------------ |
| 状态更新公式 | $h_t = \tanh(W_{xh}x_t + W_{hh}h_{t-1} + b_h)$ | $x_{t+1} = A x_t + B u_t$      |
| 输出公式   | $y_t = W_{hy} h_t + b_y$                       | $y_t = C x_t + D u_t$          |
| 输入维度     | 输入是向量 $x_t \in \mathbb{R}^n$，一次处理多个维度 | 通常 $u_t \in \mathbb{R}$，按维推理或建模 | 
| 激活函数   | 非线性（如 tanh, ReLU）                              | 一般为线性（线性系统建模）                  |

RNN 一次对 input 的多个维度建模，而 SSM 一次建模一个维度（所以使用 RNN 的模型的 hidden dim 远小于使用 SSM 的模型的总 hidden dim）。两者的参数矩阵都是时间无关的。

**（2）、转为卷积**

根据上面的递推公式，逐个展开有：

$$
\begin{cases}
x_0 &= 0 \\
x_1 &= \bar{A} x_0 + \bar{B} u_0 \\
x_2 &= \bar{A} x_1 + \bar{B} u_1 = \bar{A}^2 x_0 + \bar{A} \bar{B} u_0 + \bar{B} u_1 \\
\ldots \\
x_n &= \sum_{i=0}^{n-1} \bar{A}^{n - i - 1} \bar{B} u_i
\end{cases}
$$

于是：

$$
y_n = C \cdot x_n = \sum_{i=0}^{n-1} C \bar{A}^{n - i - 1} \bar{B} u_i
$$

令 $K[n] = C \bar{A}^{n} \bar{B}$, 则有： 

$$
y[n] = \sum_{i=0}^n K[n - i] u[i] =: x * K
$$

这就是离散版本的 SSM 的卷积形式了(且这正是《mamba》中公式3），而 K[n] 则是卷积核。

note： $K[.] \in \mathbb{R}$, 从而 $\sum_{i=0}^n K[n - i] u[i]$ 乃标准的一维卷积。

**（3）、用快速傅里叶加速卷积计算**

既然化为标准的数学上的 1d 卷积了(非 cnn 那种局部卷积），而 1d 卷积的计算加速，是有现成的方案的：快速傅里叶变换（FFT）。正可以用它来加速这个卷积的计算。不过，为启用 FFT 加速，需要先提前把卷积核 K[.] 的所有取值都算出来的。

关于 FFT 法一些简短知识：
- 按 FFT 计算卷积的套路，一般是要求序列长度是2的幂次，这样才能达到最高效率（L * log L)。
- 用 FFT 法，乃频域卷积代替时域递推。计算方式是：y=K∗u⟺FFT(y)=FFT(K)⋅FFT(u) ⟺ y = iFFT(FFT(K)⋅FFT(u))
- 大整数的快速乘法，也是转化成了卷积计算，所以它也可以用 FFT 来加速。也就是二者的加速原理一样。大整数乘法本质是多项式乘法，而乘积正是卷积：

$$\begin{cases}
A(x) = \sum_{i=0}^{n-1} a_i x^i \\
B(x) = \sum_{i=0}^{n-1} b_i x^i \\
C(x) = A(x) \cdot B(x) = \sum_{k=0}^{2n-2} c_k x^k \\
c_k = \sum_{i=0}^k a_i b_{k-i}
\end{cases}$$

以上内容，可以说是从纯数学角度说的。

SSM 参考资料：
- https://huggingface.co/blog/lbourdois/get-on-the-ssm-train

---- 

## S4 model：Structured state space sequence models —— SSM 加速版

《Efficiently Modeling Long Sequences with Structured State Spaces》 https://arxiv.org/pdf/2111.00396

S4 是对最原始的 State Space Model（SSM）进行了一系列结构化设计和加速优化的版本。它正是上面离散 SSM 的卷积形式。它试图解决传统模型在处理超长序列依赖时的计算效率和内存瓶颈问题。

为了加速卷积核的预计算，它对于 A B C 采取了特殊的结构，所以才说是 "structured"。A 矩阵用了一种叫 HiPPO 的结构，方便卷积核中 A^n 的计算：

$$
A_{nk} = -\begin{cases}
\sqrt{2n+1} \sqrt{2k+1}, & \text{if } n > k \\
n + 1, & \text{if } n = k \\
0, & \text{if } n < k
\end{cases}
\\
, \\
比如\ A = \begin{bmatrix}
-(0+1) & 0 & 0 & 0 \\
-\sqrt{3}\sqrt{1} & -(1+1) & 0 & 0 \\
-\sqrt{5}\sqrt{1} & -\sqrt{5}\sqrt{3} & -(2+1) & 0 \\
-\sqrt{7}\sqrt{1} & -\sqrt{7}\sqrt{3} & -\sqrt{7}\sqrt{5} & -(3+1)
\end{bmatrix}
$$

卷积与递归两种形式是等价的。其实一般 S4 训练的时候才采用卷积形式：
- 训练时：全序列并行的卷积形式（高效，一次性处理整个序列）
  - 递归形式，train 时除了不能 tokens 并行，还需要把所有的 hidden state 都存下来，以便梯度回传时用，所以比较耗显存。
    - 递归 hidden 占用 shape：(batch, seq_len, input_dim, ssm_hidden_dim)。卷积模式时不用展开 hidden state 只用存下卷积核，显存占用 shape = (batch, seq_len, input_dim), 显著更小。
- 推理时：递归的状态更新公式，即像RNN一样一步一步地更新状态，适合流式处理。每一step 的 memory 和计算成本都不随时间增长（而 transformer 非如此）。

<img width="982" height="212" alt="image" src="https://github.com/user-attachments/assets/b96cf7cf-a003-4809-8971-4b4a6312825c" />

用于语言模型建模，可以直接替换 transformer 中的 attention：
>  By simply taking a strong Transformer baseline [2] and replacing the self-attention layers, S4 substantially closes the gap to Transformers (within 0.8 ppl), setting SoTA for attention-free models by over 2 ppl.

S4 作为一个 SSM，对于input token embs 的多个维度，只能一个一个维度分开独立建模，有多少维度就有几个 SSM。

**关于 conv SSM 的并行训练：**

训练时，conv 模式的 SSM 可以并行化，但是需要先计算好卷积核（A B C 本身是训练参数，故每次迭代时，都需要准备下）。卷积核 $K = [CA^nB]$ 计算并不能简单并行，而是需要逐步算 A^n（或者采用一定手段并行化）。如果A是对角矩阵，这时候可以完全并行化：

```
a = torch.tensor(3.0)  # 假设 a 是 3
N = 100
powers = torch.arange(1, 1+N)  # tensor([1, 2, 3, 4, 5, .. 100])
results = torch.pow(a, powers) # 并行一次算出 [a^1, a^2, a^3, ..., a^100]
```

----

## H3 model

《Hungry Hungry Hippos: Towards Language Modeling with State Space Models》 https://arxiv.org/pdf/2212.14052 

H3 乃基于 S4 的优化, 不过不再是简单的一个 SSM，而是包含两个 SSM。它的典型用法也是替换 transformer 中的 attention 模块。

**它诞生的 High-level Intuition：**
- SSM 记忆能力不足：不能有效“回忆”序列中早期的 token，为此引入了 Shift SSM 
- S4 不能像 attention 那样“比较不同位置之间 token”(To compare tokens across the sequence)，为此结构总用 pointwise 乘法
- 从 linear attn 获得灵感，因此采用和它类似的流程：linear attn 乃 softmax attn 的一种优化，所以是 QKV 结构的，只是计算时先结合 KV 成 Q(K'V）
  - 于是 H3 也是分出了 QKV 并大约这样形式： $Q \cdot SSM_{diag}(SSM_{shift}(K) \cdot V)$

<img width="968" height="878" alt="image" src="https://github.com/user-attachments/assets/a78a3b08-43cd-4cd5-8e55-3529579e255c" />

**H3 的两个 SSM：**

diag SSM 与 shift SSM，都是 S4 SSM 风格的，也就是乃 1d 卷积形式，可以用 FFT 加速。不过在矩阵选取上比 S4 还简单。

diag SSM：A矩阵是完全的对角形式（故只有 m 个参数），从而 A^n 计算极其简单。

shift-SSM 的 A B C 特殊选择使得它其实就是一个 1d conv，所以在《mamba》paper 的配图中，直接用 conv 来表示：

<img width="894" height="808" alt="image" src="https://github.com/user-attachments/assets/89163445-410c-4e69-93fb-f17df4143c48" />

这是因为，shift-SSM 的 A 矩阵选为

$$
A_{i,j} = \begin{cases}
1 & \text{for } i - 1 = j \\
0 & \text{otherwise}
\end{cases}
, \ \
比如\ A = \begin{bmatrix}
0 & 0 & 0 & 0 \\
1 & 0 & 0 & 0 \\
0 & 1 & 0 & 0 \\
0 & 0 & 1 & 0 \\
\end{bmatrix}
$$

而 B 矩阵，可以选为 $B=e_1 = [1, 0, ... 0]$, 这样按 A x + B u,  对 shift-SSM 的 hidden 有 $xi = [u_i , u_{i−1}, . . . , u_{i−m+1}]$, 正好把最近 m 个时间的 u 给 shift 到了 hidden state 了【note：input u 是多维的，每个维度有独立的 SSM，所以shft-SSM 的 hidden state 存的是某一个维度的最近 m 个历史，多个 shift-SSM 联合起来才存下完整的最近历史】。

令 $C = [w_0, w_1, ..]$, 则 $y_i = C x_i = \sum_{k=0}^{m-1} w_k \cdot u_{i - k}$, 正好是窗长=m 的 1d conv【这个就是 CNN 1d-conv了】。

diag-SSM 需要 IFFT(FFT(.) FFT(.)) 加速，而 shift-SSM 并不需要 FFT。

**怎么使用：**

它的一种典型用法是替换 transformer 中的 attention 模块。从 paper 看，不需要位置编码。看下《H3》paper 中的例子：

Q、K、V、output 都需要 projection，FFN 和 transformer 中一样，这些部分有 $12d^2$ 个参数。shift-SSM 只有 C 有参数（m个）， diag-SSM 的 ABC都是 m 个参数，所以 SSM 不分一共有 4m*d=4md个参数，总参数量是 $12d^2+4md$，假设vocab size=50k，则可以算得 paper 中各 model 参数量如下（基本对得上）：

| 模型   | Layers | Hidden dim(d) | FFN dim | Heads | SSM dim(m) | 算出的参数量|
| ----- | ------ | ------| ------ | --- | --- | ---- |
| 125M  | 12     | 768   | 3072   | 12 | 64 | 125.69M  |
| 355M  | 24     | 1024  | 4096   | 16 | 64 | 359.48M  |
| 1.3B  | 24     | 2048  | 8192   | 16 | 64 | 1322.94M | 
| 2.7B  | 32     | 2560  | 10240  | 20 | 64 | 2665.55M |

注意：
- 例子中，H3 像 MHA attn 一样，也可以分好多个 heads。从 H3 的 $Q \cdot SSM_{diag}(SSM_{shift}(K) \cdot V)$ 式看，SSM 看不到 heads 存在，QKV的交互计算，才牵扯 head。SSM 的input shape 与 output shape 保持不变，所以 H3 结构可以看作是插入了两个 SSM 的 linear attention。
- 关于 " $H3 = Q \cdot SSM_{diag}(SSM_{shift}(K) \cdot V)$ " 一式， 只算是示意。若K、V是多个时间步，则 K V 都是行向量的concat， $SSM_{shift}(K) \cdot V$ 真实表达的是 $\sum_i (SSM_{shift}(K_i) ⊗ V_i)$。 其中 $A⊗B=\\{a_i b_j\\}_{i,j}$ 是外积。

----

## mamba

mamba 包括几方面：一是对 SSM 的改进，二是基于改进的 SSM 而对 H3 的改进。

### 对 S4 SSM 的改进：selective SSM (文内也叫它 S6)

**（1）、selective SSM 什么样子**

<img width="2200" height="838" alt="image" src="https://github.com/user-attachments/assets/0de78f1f-9bbb-4b5e-a10e-af344868fa22" />

结构如上。

- 原始 SSM 的矩阵 A B C 等都是固定的常量， 这里把它改成了 B C $\Delta$ 都是由当前 input x_t 经过线性层推出的(上文 x_t 是当做 hidden state 的，这里当做了input)。这使得它不再是 LTI 了。
  - 不再是 LTI，从而不再能用 FFT 加速，只能递归展开。
- 一个 SSM 只能处理一维数据。这里传给 SSM 的 input 仍然是单维的，但是是经过 x_t 多维度信息交换后的一维。
- 原始 SSM 离散化时是平均切分时间，这里变成了动态切分：时间间隔是动态的，根据当前 input x_t 而定。

<img width="1662" height="510" alt="image" src="https://github.com/user-attachments/assets/21e093d5-d254-46b6-bf50-e6fe70640c7b" />

为什么有上面的改进：为了解决传统 LTI SSM 无法进行“内容选择”的问题，即不能根据输入内容来选择性处理信息，无法“忽略无关信息”或“在特定时刻记住关键内容”。是为了解决传统 SSM 模型缺乏“输入依赖”和“内容选择能力”的根本缺陷而提出的。用原文说，它的好处是：

> the most important property of selectivity is filtering out irrelevant information so that a sequence model’s context can be compressed into an efficient state. 

paper 把它的 SSM 改进结构叫做 S6，是因为：能力上，有序列内的空间感知能力的加强（selective）， 同时有 parallel scan 这样的前缀和的加速算法等一系列计算优化来保证性能（即文中所谓 selective scan）。从而增加两个 S。【原文：被叫 S6 because they are S4 models with a selection mechanism and computed with a scan】

**怎么理解 selective：**

迭代公式：

```
hₜ = A hₜ₋₁ + Bₜ xₜ
yₜ = Cₜ hₜ
```
中：
```
Bₜ = s_B(xₜ)      # 输入决定当前 token 是否写入 state
Cₜ = s_C(xₜ)      # 输入决定是否读取 state
Δₜ = τ(s_Δ(xₜ))   # 输入决定状态更新的快慢/保留
```

除了以上，再看 paper 3.5.2 一节。

**（2）、selective SSM 有啥实现上的困难，怎么解决的**

本来 S4 已经用 FFT 把 SSM 的训练优化得很好了。现在 selective SSM 使得 FFT 不能用了，于是训练不再可以并行，显存会占用更多，计算量会变大——仅仅为了 selective 能力。如何是好？

作者发现：
- **计算量问题**：看起来还好。
  - recurrent 计算量是 $O(BLDN)=a BLDN $, 而 conv FFT 计算量是 $O(BLD\log(L))=b BLD\log(L)$, 往往 log(L) < N【比如log(一千万)=16】，若常数项 a b 一样，确实 conv 计算量小。但是实际中 O(BLDN) 的常数项系数 a 更小。消去相同因子后 a * N 与 b * log(L) 比， 如果 N 比较小，同时 L 比较长，则 recurrent 不见得有劣势。
    - recurrent 模式的 O(BLDN) 怎么来的：SSM 内的计算是 $h \leftarrow Ah+Bx; y \leftarrow Ch$, A 矩阵是对角矩阵，所以 Ah 计算量是 N 而非 N², 而 Bx与 Ch 计算量都是 N，所以一次 SSM 内计算乘法与加法共是 5N。所以是 O(BLDN)
    - conv 模式的计算量是 $O(BLD\log(L))$ 怎么来的：一次 conv 模式的 SSM 计算量是卷积核准备 + IFFT(FFT FFT) 操作。卷积核计算时间是 O(LN^2), 若A矩阵是对角矩阵，则是 O(LN)，batch内只需要计算一次，故卷积核计算量可忽略。一个 FFT 计算量是 5 L log(L), 从而得到 $O(BLD\log(L))$。整个的系数大约为 10，确实比 recurrent 模式的系数大。
  - note: B=batch，L=seq_len, D=input_dim, N=SSM_hidden_dim, 而 FFT 计算量是 Llog(L）
- **显存问题**：可化解。recurrent SSM 需要把所有时间的 hidden 展开存显存(HBM)以便反向传播用。而这用 recomputation 即可（用时当场算出一个）
- **并行问题**：用一个叫 work-efficient parallel scan algorithm 实现并行。
- 其他：IO 优化。用 kernel fuse（把多个操作打包成一个基本操作）。Δ, A, B, C 离散出新的 A B，然后执行 hidden state 更新，并产生输出，一系列操作都放到了一个 kernel 里（selective SSM 图里也有示意）：
  - <img width="1464" height="250" alt="image" src="https://github.com/user-attachments/assets/b0ddf62d-f96e-4251-bf7d-5f71442ecf7b" />
  - reduce IOs by a factor of 𝑂(𝑁) (N=SSM_dim), which in practice speeds up the operation by 20-40 times

**（3）、怎么使用**

如下图，作者没有像之前一般做法那样，仅仅是用新的序列建模结构，替换 transformer 的 attention，而是把该结构嵌入到了 FFN 内部，从而彻底取代了 transformer：

<img width="1802" height="926" alt="image" src="https://github.com/user-attachments/assets/b936a36c-991f-4205-9113-b828fc60c802" />

注意：
- 加了 swiGLU 激活后的 FFN 长这样： $FFN(x)= [Swish(x W_1)\odot (xW_0)]\cdot W_2$ ，它正是上图的 gated MLP。
- H3 的非线性来自点乘，而 mamba 中则有非线性激活函数

为了与 transformer 参数量匹配，mamba block 重复二次当做一个 transformer 的替代物：

<img width="1012" height="868" alt="image" src="https://github.com/user-attachments/assets/d2c945dc-2365-45cc-a529-302b779f8bd1" />

为啥 mamba 重复 2 次等于一个 transformer：令 hidden dim=d。则 transformer 参数量是 12d², FFN 与 ATTN的proj层 各有 8d² 与 4d² 个。而 mamba block 中三个升降维的 proj 参数量都是 2d², 共 6d²，所以 2个 block 是 12d²。注意：transformer FFN 一般升维倍数是 4，swiGLU 化的 FFN 有三个矩阵，升维因子是 8/3（以维持参数量同普通 FFN）, 而 mamba 继承了三个矩阵的 swiGLU FFN，但是升维因子选用了 2(即 paper 3.4节中的 E），见下图。

<img width="1438" height="570" alt="image" src="https://github.com/user-attachments/assets/e4171da2-7f12-4089-bbe9-0ef633f6120b" />

一系列 mamba block stack 起来，下面接 embedding 层，最上接 softmax，就可以作 LLM 那些事了。

其他：
- 位置编码：不需要（paper中没提需要）。即 input emb 不需要这样 x_embed = x_embed + pos_embed
- 多 heads: H3 是有像 MHA 一样的多 heads 的。 mamba 不需要（特别地，paper 表12 提到 "Model dimension and **number of heads applies only to Transformer models**")

**（4)、和 transformer 对比**

mamba 用作 transformer 那样的语言模型后，可以作自回归生成，这时对 prompt 不分，也可以类似 transformer 的 prefill 那样快速并行处理（用 parallel scan）。

据paper:
- 同等参数的model，mamba 不输 transformer，在大上下文（8K）下表现更好
- 在相同模型大小下，Mamba 的 token 生成速度是 Transformer 的 4～5 倍。且内存占用恒定计算量线性 
- Mamba 支持最多 1M token 的上下文长度；性能 随着上下文长度增长而提升，而 Transformer 往往会因为“稀释注意力”而表现下降；原因在于 Mamba 可以选择性地过滤上下文（选择性机制），只保留重要状态。

### 《paper》paper 中一些段落解释

**关于 S4："3.3.1 Motivation of Prior Models"**

<img width="1484" height="520" alt="image" src="https://github.com/user-attachments/assets/b8b76bca-162b-44b5-91da-3d31150da4e1" />

- 第二点：递归式更费显存，指的是train的时候（为了梯度回传，需要把所有 hidden states 都存下来），infer 的时候更省。
- 第三点：为什么 LTI 的 SSM 比传统 RNN 能支持更大的 hidden dim？因为 SSM 是每个 input 维有好多个 SSM 的内部 hidden dim，而 RNN 是全体 input 共享一个 hidden dim。由于 S4 SSM 可以用 FFT 加速，所以 hidden dim 变大了，但是计算效率还很高。 

**关于 3.5.1 节 定理1**

<img width="1008" height="111" alt="image" src="https://github.com/user-attachments/assets/278ff664-3022-4733-9718-05a08522bd88" />

SSM 离散后表达式是：

$$
\begin{cases}
h_t = A_d h_{t-1} + B_d x_t \\
A_d = \exp(\Delta A) \\
B_d = A^{-1}(A_d - I) B = (\Delta A)^{-1} (\exp(\Delta A) - I) \Delta B
\end{cases}
$$

把 $A = -1$, $B = 1$, $\Delta = \delta$ 带入：

$$
\begin{cases}
A_d &= \exp(-\delta) \\
B_d &= (-\delta)^{-1} \left( \exp(-\delta) - 1 \right) \delta = \frac{1 - \exp(-\delta)}{\delta} \cdot \delta = 1 - \exp(-\delta)
\end{cases}
$$

所以更新公式变为：

$$h_t = \exp(-\delta) h_{t-1} + (1 - \exp(-\delta)) x_t$$

现在我们令：

$$g_t := 1 - \exp(-\delta)
\Rightarrow
h_t = (1 - g_t) h_{t-1} + g_t x_t$$

**关于 mamba 的选择机制的一些解释： "3.5.2 Interpretation of Selection Mechanisms"**

根据这节内容:

A). B_t：控制是是否让当前输入 x_t 存入 h_t(或者说存入多少）， 

B). C_t: 控制了让 state h_t 参与多少到 output y_t

C). $\Delta$: 离散时间步进长度，决定了模型对当前输入 $x_t$ 的“注意力”或“记忆效果”：

> **大 $\Delta_t \Rightarrow$ 忽略之前的状态，重置并关注当前输入；
> 小 $\Delta_t \Rightarrow$ 忽略当前输入，延续先前状态。**

而这显然需要在 $h_t = A_d h_{t-1} + B_d x_t$, $A_d = \exp(\Delta A)$ 式中矩阵 A 的取值要配合（比如如 theorem 1， A=-1）。

但是矩阵 A 是可训参数，并没法控制它是负的。若正，则 $\Delta \rightarrow \infty$ 时，反而让之前状态最大化了。对此，model 的处理方式是 3.6 节的特别参数初始化，即初始化为负（但是最终训出的参数并不能保证一定负）：

<img width="1004" height="132" alt="image" src="https://github.com/user-attachments/assets/ac46142b-247e-4aa8-90a7-871619719e91" />

特别的，如果多个本应独立的序列被拼接在一起时，transformer 可以用 attention mask 来分隔，而 LTI 的 SSM 没法区分。而在 mamba 中，则可以令 $\Delta$ 取很大值来隔离不同序列（对应 paper 的 Boundary Resetting 一小节）。

**关于 work-efficient parallel scan algorithm 加速 selective SSM**

这种算法即 Parallel scan。又称为并行前缀和（parallel prefix sum），通俗说，要解决的问题是：已知数量 {$a_n$}, 需要求出前缀和数列 {$b_n$}, 其中 $b_n = \sum_0^n a_i$。(那么就是 torch.cumsum=cumulative sum 问题了）。

当然实际上不只是前缀和，而是某一类问题，前缀和只是其一。它解决的一类问题是：对 f1∘f2∘f3∘..fn(x) 函数嵌套【∘定义为：f∘g(x)=f(g(x)】，如果相邻函数可以结合，即可以 (f1∘f2)∘(f3∘f4)..，则可以并行地把先把结合函数算出，从而递归并行加速。也就是，它其实是逐次的对函数式的归并。

Blelloch scan 乃 Parallel scan 算法之一种。它保持计算量基本不变（相比串行），而运行时间是 O(n) => O(log n)。分两阶段进行：
- Up-sweep（Reduce）阶段：构建一棵二叉树，从底向上归约，最终在根节点得到全局和。这个阶段目的是让每个节点都能获得其子树的和。
- Down-sweep 阶段：从树根向下进行，传播和分配前缀值。这样每个节点最终得到其前缀和。

对于 selective SSM, 为啥可用 Parallel scan?

selective SSM 的 hidden 更新式子可以写成 

$$h_t = M_t(h_{t-1}) = A_t h_{t-1} + u_t \quad \text{其中} \quad u_t = B_t x_t$$

若令 $(A_t, u_t)$ 表示更新映射，即定义 $(A_t, u_t)(x) := A_t x + u_t$ , 则可以验证有：

$$
(A_2, u_2) \circ (A_1, u_1) = (A_2 A_1, A_2 u_1 + u_2)
$$

因此它是满足上面说的 f1∘f2∘f3∘..fn(x) == (f1∘f2)∘(f3∘f4)..fn(x) 的结合性的。从而可以并行递归加速计算。

关于前缀和：https://arxiv.org/pdf/2312.06635 《GLA-gated linear attention》，再参考： https://zhuanlan.zhihu.com/p/1929192016195089740 
