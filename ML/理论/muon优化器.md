### lion

谷歌推出的 lion，使用梯度的方向（正负符号）而不是梯度值，来减少噪声和计算复杂度。极简。

$$
\begin{cases} 
m_t = \beta_1 \cdot m_{t-1} + (1 - \beta_1) \cdot g_t \\
w_t = w_{t-1} - \eta \cdot \text{sign}(m_t)
\end{cases}
$$ 

### muon

之前的优化器一般都是对每个参数独立处理。而 muon 是对参数整体作控制，考虑他们之间的相互作用。具体说来是把每一个参数矩阵作为整体考虑。model 的所有参数由矩阵与向量组成: params = {W1, W2, ..., Wn}, W_i 是矩阵或向量。muon 优化的是其中的每个矩阵（当然向量作为特殊矩阵也可用它），对每个参数矩阵独立进行。


基本原理是对一个梯度矩阵的动量平均 $m_t$，作 SVD 分解成 UΣVᵀ，然后舍弃中间的对角 Σ，从而用 UVᵀ 代替 $m_t$ 来进行参数更新。数学上 UVᵀ 确实是表示矩阵 $m_t$ 的符号矩阵的（但不是逐元素取负那种，而是在特征根角度），这样看和 lion 很是像，因此也算符合直觉。如下：

$$
\begin{cases} 
m_t &= \beta_1 \cdot m_{t-1} + (1 - \beta_1) \cdot g_t \\
m_t &= U\Sigma V^T \\
w_t &= w_{t-1} - \eta \cdot (UV^T) 
\end{cases}
$$

M = UΣVᵀ 若作为线性变换，则 U/V 是正交矩阵表示旋转，Σ 是一种伸缩。梯度直观上看像是通过 SVD 把梯度的不同维之间的某种起伏抹平了，从而所有参数都得到有效更新。但是其他优化器不管怎么变，还能看出更新量确实是和梯度方向紧密相关，而 muon 不太能看得出：矩阵拉平到 1d 向量，UVᵀ 真的和 UΣVᵀ 方向差不多吗？

苏剑林的 [Muon优化器赏析：从向量到矩阵的本质跨越 - 科学空间|Scientific Spaces](https://spaces.ac.cn/archives/10592) 一文证明了 UVᵀ 乃“谱范数距离” 约束下的梯度下降，它和原始梯度距离很近，确实能令 loss 下降。

UΣVᵀ分解不容易，UVᵀ 计算也费劲，所以实际中需要用近似算法，即 Newton-Schulz 法： 令 M₀ = Mₜ / ||Mₜ||, 迭代下式即可（作者证实不需迭代几次故计算量可控）：

$$
X_k = a X_{k-1} + b(X_{k-1} X_{k-1}^T)X_{k-1} + c(X_{k-1} X_{k-1}^T)^2 X_{k-1}
$$

----

## 详述

### SVD

**M = UEV' 分解的存在性**：

M 是 $m \times n$ 矩阵，则 M = UEV' 可以分解为正交+对角+正交三个矩阵的乘积。是因为：

$M'M$ 是正定的，按线性代数可以有分解： $M'M = V \Lambda V'$， 其中 V 是正交矩阵， $\Lambda$ 对角。

令 $E = \sqrt{\Lambda}\sim n \times n$, 令 $U=MVE^{-1} \sim m \times n$，则 $U E V'=(MVE^{-1}) E V' = MVV' = M$, 即分解形式成立(还需吧 U 补成 mxm矩阵，把 E 也相应补零)。

此时还需保证 $U=MVE^{-1}$ 是正交的： $U'U = (MVE^{-1})'(MVE^{-1})={E'}^{-1} V'(M'M)VE^{-1}$ ，而 $M'M = V \Lambda V'= VE^2V'$, 代入可得  $U'U = {E'}^{-1} V'(VE^2V')VE^{-1}=I$。

**E 排序后唯一性**： $MM'=UEEU'$ , $M'M=V'EEV$ , 故而 $E^2$ 是 $MM'$ 的取值确定特征值，故E取值确定。

M = UEV' 中 E 对角元素乃 M'M 的特征值的平方根，称为 M 的奇异值。对 E 的对角元素排序后，去除尾部较小特征值，对 UEV 作缩减调整后仍作 UEV' 计算，所得矩阵是原矩阵的近似。这可以用来作数据的压缩（比如图片看做矩阵，从而作压缩）。

但是 muon 后并不是去掉小特征值，而是一律置为 1，因此难说 UVᵀ 与原始 Mₜ 梯度矩阵近似，所以不能把 muon 理解成用 UVᵀ 逼近原始梯度。

M = UEV' 当做线性空间的对向量的线性变换（x₁= Mx)，则表示变换可以分解成：旋转（U)+伸缩（E)+旋转（V')。奇异值部分的 E 表示矩阵作用在不同方向上的伸缩“强度”。但是这个伸缩是针对的被 M 作用的 x，而不是 M 内的元素本身。因此也不能把 muon 中的 E => I 理解成把 M 内的维度做了归一。

既然 muon 可行，UV' 方向总该和 M 差不多吧——比如用 cosine 衡量的方向。经构造测试，假设M是方针，且 E 对角元素是 abs(正态) 的，二者确实还是很 cosine 相关的。如果 E 取差别更悬殊，cosine 会下降，终究比随机值要大得多（怎么也有零点一二吧）。

https://kellerjordan.github.io/posts/muon/:
> And for an empirically-flavored motivation, we observe that based on manual inspection, the updates produced by both SGD-momentum and Adam for the 2D parameters in transformer-based neural networks typically have very **high condition number**(最大最小奇异值的比例）. That is, they are almost **low-rank matrices**, with the updates for all neurons being dominated by just a few directions. We speculate that orthogonalization effectively increases the scale of other “rare directions” which have small magnitude in the update but are nevertheless important for learning.

（2）为什么 UVᵀ 是谱范数约束下的梯度下降


https://github.com/KellerJordan/Muon
https://kellerjordan.github.io/posts/muon/
