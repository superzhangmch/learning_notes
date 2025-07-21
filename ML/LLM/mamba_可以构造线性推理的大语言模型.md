《Mamba: Linear-Time Sequence Modeling with Selective State Spaces》 https://arxiv.org/pdf/2312.00752

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

这正是数学上卷积形式（不同于 CNN 中的那种卷积）】

### SSM 离散化（Discretization）

**（1）、离散化**

对上面的连续取值的微分方程 $\frac {d x(t)}{dt} = A x_t + B u_t$, 可以离散化的，比如 euler 方法。

而 SSM 常用的方法叫 ZOH 法（Zero-Order Hold），做法大约为：对 input u, 把时间平均切分成一段一段，每一小段的取值等于小段起始点的取值 u_t。

在离散化的 u_t 基础上得到, 用上文的精确解, 即可得到离散化的 y_t 了:

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

既然化为标准的数学上的 1d 卷积了(非 cnn 卷积），而 1d 卷积的计算加速，是有现成的方案的：快速傅里叶变换（FFT）。正可以用它来加速这个卷积的计算。不过，为启用 FFT 加速，需要先提前把卷积核 K[.] 的所有取值都算出来的。

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

以上内容，可以说都是纯数学角度的。

---- 

## S4 model：Structured state space sequence models 

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
A = \begin{bmatrix}
-(0+1) & 0 & 0 & 0 \\
-\sqrt{3}\sqrt{1} & -(1+1) & 0 & 0 \\
-\sqrt{5}\sqrt{1} & -\sqrt{5}\sqrt{3} & -(2+1) & 0 \\
-\sqrt{7}\sqrt{1} & -\sqrt{7}\sqrt{3} & -\sqrt{7}\sqrt{5} & -(3+1)
\end{bmatrix}
$$

卷积与递归两种形式是等价的。其实一般 S4 训练的时候才采用卷积形式：
- 训练时：全序列并行的卷积形式（高效，一次性处理整个序列）
- 推理时：递归的状态更新公式，即像RNN一样一步一步地更新状态，适合流式处理。每一step 的 memory 和计算成本都不随时间增长（而 transformer 非如此）。

<img width="982" height="212" alt="image" src="https://github.com/user-attachments/assets/b96cf7cf-a003-4809-8971-4b4a6312825c" />

用于语言模型建模，可以直接替换 transformer 中的 attention：
>  By simply taking a strong Transformer baseline [2] and replacing the self-attention layers, S4 substantially closes the gap to Transformers (within 0.8 ppl), setting SoTA for attention-free models by over 2 ppl.

----

## H3 model：

《Hungry Hungry Hippos: Towards Language Modeling with State Space Models》 https://arxiv.org/pdf/2212.14052 

