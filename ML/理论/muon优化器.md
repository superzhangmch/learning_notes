### muon

之前的优化器一般都是对每个参数独立处理。而 muon 是对参数整体作控制，考虑他们之间的相互作用。具体说来是把每一个参数矩阵作为整体考虑。model 的所有参数由矩阵与向量组成: params = {W1, W2, ..., Wn}, W_i 是矩阵或向量。muon 优化的是其中的每个矩阵（当然向量作为特殊矩阵也可用它），对每个参数矩阵独立进行。


基本原理是对一个梯度矩阵的动量平均 $m_t$，作 SVD 分解成 UΣVᵀ，然后舍弃中间的对角 Σ，从而用 UVᵀ 代替 $m_t$ 来进行参数更新。数学上 UVᵀ 确实是表示矩阵 $m_t$ 的符号矩阵/符号函数的（但不是逐元素取负那种），这样看和 lion 的取梯度的正负符号的做法很像，因此也算符合直觉吧。如下：

$$
\begin{cases} 
m_t &= \beta_1 \cdot m_{t-1} + (1 - \beta_1) \cdot g_t \\
m_t &= U\Sigma V^T \\
w_t &= w_{t-1} - \eta \cdot (UV^T) 
\end{cases}
$$

【谷歌推出的 lion，使用梯度的方向（正负符号）而不是梯度值，来减少噪声和计算复杂度，极简： $m_t$ 和 muon 一样, 而 $w_t = w_{t-1} - \eta \cdot \text{sign}(m_t)$ 】

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

E 对角元素排序后，分解的唯一性： $MM'=UEEU'$ , $M'M=V'EEV$ , 故而 $E^2$ 是 $MM'$ 的取值确定特征值，故E取值确定。

**M_new = UV' 为啥可行**：

M = UEV' 中 E 对角元素乃 M'M 的特征值的平方根，称为 M 的奇异值。对 E 的对角元素排序后，去除尾部较小特征值，对 UEV 作缩减调整后仍作 UEV' 计算，所得矩阵是原矩阵的近似。这可以用来作数据的压缩（比如图片看做矩阵，从而作压缩）。但是 muon 后并不是去掉小特征值，而是一律置为 1，因此难说 UVᵀ 与原始 Mₜ 梯度矩阵近似，所以不能把 muon 理解成用 UVᵀ 逼近原始梯度。

M = UEV' 当做线性空间的对向量的线性变换（x₁= Mx)，则表示变换可以分解成：旋转（U)+伸缩（E)+旋转（V')。奇异值部分的 E 表示矩阵作用在不同方向上的伸缩“强度”。但是这个伸缩是针对的被 M 作用的 x，而不是 M 内的元素本身。因此也不能把 muon 中的 E => I 理解成把 M 内的维度做了某种放缩归一。

既然 muon 可行，UV' 方向总该和 M 差不多吧——比如用 cosine 衡量的方向。经构造测试，假设M是方针，且 E 对角元素是 abs(正态) 的，二者确实还是很 cosine 相关的。如果 E 取差别更悬殊，cosine 会下降，终究比随机值要大得多（怎么也有零点一二吧）。

M_new = UV' 是正交矩阵，所有元素绝对值不超 1，而 M 最大值无上限限制（M = UEV' = { $\sum_k \sigma_k u_{ik} v_{kj}$ }, 按 muon 作者所言，M 原矩阵的奇异值{ $\sigma_k$ } 差异较大，那么确实 M 最大元素取值有很大可能），这也算是一种对高梯度值的那些参数的约束吧。但不足以解释 UV' 有效性。

从经验直觉，muon 作者这么说的：https://kellerjordan.github.io/posts/muon/:
> And for an empirically-flavored motivation, we observe that based on manual inspection, the updates produced by both SGD-momentum and Adam for the 2D parameters in transformer-based neural networks typically have very **high condition number**(最大最小奇异值的比例）. That is, they are almost **low-rank matrices**, with the updates for all neurons being dominated by just a few directions. We speculate that orthogonalization effectively increases the scale of other “rare directions” which have small magnitude in the update but are nevertheless important for learning.
>
> (人工检查看到，更新矩阵奇异值差异迥异，几乎都是低秩矩阵，所有神经元的更新都主要集中在少数几个方向上。因此 UV' 正交化在某种程度上放大了那些在更新中幅度较小但对学习仍然重要的“稀有方向”的尺度)

上述总总，让人觉得用 UV' 是有一定道理的，但总觉得还是差了一点。

另外可以证明，和 M 的 $\sqrt{sum{|.-.|^2}}$ 范数距离最小的正交矩阵是 UV'（[Muon优化器赏析：从向量到矩阵的本质跨越 - 科学空间|Scientific Spaces](https://spaces.ac.cn/archives/10592)）。

### 关于 UV' 是 M 的符号函数

数学上大约有这么回事：

$(M_t M'_t)^{-1/2} M_t = UV'$ 称之为矩阵的符号函数。 $(..)^{-1/2}$ 定义： 对称矩阵函数 $f(X)$ 的定义是若 $X=PEP'$ 有正交+对角分解，则 $f(X) := Pf(E)P'$，这里 $X=MM'$, $f=(.)^{-1/2}$。按此定义，则易知 $(M_t M'_t)^{-1/2} M_t = UV'$ 成立。

下面是 ai 提供的一些知识：

<img width="1172" height="950" alt="image" src="https://github.com/user-attachments/assets/4fdd1f3e-cfa2-4bc0-b494-7a5d777d644d" />

<img width="1492" height="264" alt="image" src="https://github.com/user-attachments/assets/9fa2d46e-374c-4b3f-bd8d-b16eb57df45f" />

总之，看来这个 UV' 确实可看做 M 的一种符号矩阵的推广，那么 UV' 用来代替 M，起到一种 lion 优化器中的符号方向的作用，是可以理解的。

### 为什么 UVᵀ 是谱范数约束下的梯度下降


https://github.com/KellerJordan/Muon
https://kellerjordan.github.io/posts/muon/
