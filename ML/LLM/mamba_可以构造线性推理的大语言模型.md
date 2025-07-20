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

$$x(t)=e^{At}x(s)+\int_s^t e^{A(t−τ)}\cdot B \cdot u(τ) dτ$$

其中时间 0 <= s <= t。

【若令 x(0) = 0, 则 $x(t)=\int_0^t e^{A(t−τ)}\cdot B \cdot u(τ) dτ$。此时若令 $K(t−τ) = \int_0^t e^{A(t−τ)}\cdot B$, 则 

$$y_t = \int_0^t [C e^{A(t−τ)} B] \cdot u(τ) dτ = \int_0^t K(t−τ) u(τ) dτ$$

这正是数学上卷积形式（不同于 CNN 中的那种卷积）】

### SSM 离散化（Discretization）

对上面的连续取值的微分方程 $\frac {d x(t)}{dt} = A x_t + B u_t$, 可以离散化的，比如 euler 方法。

而 SSM 常用的方法叫 ZOH 法（Zero-Order Hold），做法大约为：对 input u, 把时间平均切分成一段一段，每一小段的取值等于小段起始点的取值 u_t。这样具体操作起来，就是对方程的精确解析解离散化——而上面已经有了精确解。

假设相邻时间离散点的时间差是 Δ， 把 s=t-Δ 代入精确解析解有：

$$x(t)=e^{At}x(t-Δ)+\int_{t-Δ}^t e^{A(t−τ)}\cdot B \cdot u(τ) dτ$$

注意： 令 $x_s:= x(t),\ x_{s-1}:=x(t-Δ)$, 根据 ZOH 离散化定义有 $u_{new}(t-Δ \le . \le t) := u(t)$，于是代入上式有：

$$
\begin{align}
x_s&=e^{At} x_{s-1} + u(t) \int_{t-Δ}^t e^{A(t−τ)}\cdot B  dτ \\
 &=e^{At} x_{t-1} + u(t) \int_0^Δ e^{Aτ }\cdot B  dτ \\
 &=e^{At} x_{t-1} + u(t) [\int_0^Δ e^{Aτ }\cdot dτ] B  & //数学上有：\int_0^Δ e^{Aτ }\cdot dτ = A^{-1} (e^{AΔ}−I)$, 其中A是矩阵\\
 &= e^{At} x_{t-1} + u(t) A^{-1} (e^{AΔ}−I)B
\end{align}
$$

