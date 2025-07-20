《Mamba: Linear-Time Sequence Modeling with Selective State Spaces》 https://arxiv.org/pdf/2312.00752

## SSM： 状态空间模型，State Space Models

SSM 并不是因机器学习的问题而特意创造出来的，而是一类应用很广泛的通用模型，只是后来被借用到了机器学习领域。据 ai（姑信之）：最初来自控制理论，后来被广泛应用于信号处理、时间序列分析、物理建模和机器学习等领域。

它的基本设定是，有一个随着时间 t 而变化的实值 input 信号 $u_t$，期望建模出随时间 t 同步变化的实数值 output 信号 $y_t$。时间 t 可能是连续的，也可能是离散的。

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

A、B、C、D 都是 constant 的。即为常系数微分方程。且 D 可以进一步为 0，下面都令 D=0。

**(3)、方程求解**

对于上面的一阶线性常系数微分方程，用解微分方程的常规做法，可以从数学上解出（AI 给出）： 

$$x(t)=e^{At}x(0)+\int_0^t e^{A(t−τ)}\cdot B \cdot u(τ) dτ$$

若令 x(0) = 0, 则 $x(t)=\int_0^t e^{A(t−τ)}\cdot B \cdot u(τ) dτ$。

**（3）、转为卷积形式**

若令 $K(t−τ) = \int_0^t e^{A(t−τ)}\cdot B$, 则 

$$y_t = \int_0^t [C e^{A(t−τ)} B] \cdot u(τ) dτ = \int_0^t K(t−τ) u(τ) dτ$$

这正是数学上卷积形式（不同于 CNN 中的那种卷积）。也就是说， SSM 就是个卷积，只要知道（或设法建模出）卷积核函数 K(t)，则直接计算卷积，就完成了 SSM 变换。而要获得 K(t), 根本在于知道 A B C 的取值。

### SSM 离散化（Discretization）

对上面的连续取值的微分方程 $\frac {d x(t)}{dt} = A x_t + B u_t$, 可以离散化的，典型如 euler 方法。而 SSM 常用的方法叫 ZOH 法。据 AI，ZOH 是数字控制系统与信号处理中早就有的一个关键概念。在 mamba/S4/H3等模型中，不过是借用而已。





