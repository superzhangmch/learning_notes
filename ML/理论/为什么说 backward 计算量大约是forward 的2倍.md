# 为什么说backward 计算量大约是forward 的2倍

神经网络中绝大部分操作只矩阵乘法（注意 CNN 也算矩阵乘法）。这个 2 倍就指的矩阵乘所导致的 2 倍。下面为说明意思，有的地方并没严密对齐各个矩阵是否该 transpose 下。

----

假设 loss 是 

$$Loss = L(W\cdot g(x_1), x_2)$$

其中 $x_1、x_2$ 是原始 input 的各一部分, $W \in \mathbb{R}^{m \times n}$, $g(x_1) \in \mathbb{n \times 1}$ 是列向量。再令 $f = W\cdot g(x_1) \in \mathbb{R}^{m \times 1}$。

----

假设 ∂L/∂f 已经算出来了，那么： 

(1) $\frac {∂L} {∂W} = \frac {∂L} {∂f} \frac {∂f} {∂W} = \frac {∂L} {∂f} g^T(x_1)$

以上 $\frac {∂L} {∂f}$ 是长为 m 的列向量， $g^T(x_1)$ 是长为 n 的行向量，则 $\frac {∂L} {∂f} g^T(x_1)$ 就是外积矩阵（因为 W 是矩阵，所以 $\frac {∂L} {∂W}$ 也需要是同样 shape 的矩阵），所以计算量是 $mn$。

另外注意这里假设了 batch_size = 1。如果当前 gpu 上的 bs > 1, 则 $g^T(x_1) \in \mathbb{R} ^{bs \times n}$, 那么为算 $\frac {∂L} {∂W}$, 还需要把这些样本的外积矩阵加起来。这样看，bs 比较大后，外积矩阵每个元素也需要做一次加法。那么 $\frac {∂L} {∂W}$ 的计算量就是 2mn 了。

详细计算如下图：

<img width="1072" height="942" alt="image" src="https://github.com/user-attachments/assets/cdc483f8-d0d9-4303-92dd-6926e88ac150" />

(2) 为了处理 g(x_1) 里面的参数梯度，还需要把 ∂L/∂g (n维）也算出来。而 $\frac {∂L} {∂g} = \frac {∂L} {∂f} \frac {∂f} {∂g} =  \frac {∂L} {∂f} W$，这里 $\frac {∂L} {∂f} \in \mathbb{R}^{1 \times m}$。 $(1\times m) \times (m \times n)$ 的矩阵相乘，乃矩阵和向量的乘积，则加法与乘法的计算量是 $2mn$。而且注意，它的计算和 batch_size 并没关系。

----

综上看，backward的时候，在 W 这个矩阵处，算了两次矩阵乘法： $\frac {∂L} {∂f} g^T(x_1)$ 与 $\frac {∂L} {∂f} W$，每一个的计算量都大概是 2mn。而 此处forward的时候，$W\cdot g$ 为矩阵乘向量，计算量是 2mn, 正好是 backward 的一半。

另外，$\frac {∂L} {∂f} g(x_1)$ 与 $\frac {∂L} {∂W}$ 无关，但是每有一个 W，确实伴随一个 $\frac {∂L} {∂f} g(x_1)$这样的东西（实际上 ∂L/∂f 往往也是这样伴随别的算出来的），除非 g(x_1) 中不含参数。
