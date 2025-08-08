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

UΣVᵀ分解不容易，UVᵀ 计算也费劲，所以实际中需要用近似算法，即 Newton-Schulz 法，用多次迭代求得（作者证实不需迭代几次故计算量可控）。

----

## 详述

**M_new = UV' 的看起来的合理性**：

M = UEV' 中 E 对角元素乃 M'M 的特征值的平方根，称为 M 的奇异值。对 E 的对角元素排序后，去除尾部较小特征值，对 UEV 作缩减调整后仍作 UEV' 计算，所得矩阵是原矩阵的近似。这可以用来作数据的压缩（比如图片看做矩阵，从而作压缩）。但是 muon 后并不是去掉小特征值，而是一律置为 1，因此难说 UVᵀ 与原始 Mₜ 梯度矩阵近似，所以不能把 muon 理解成用 UVᵀ 逼近原始梯度。

M = UEV' 当做线性空间的对向量的线性变换（x₁= Mx)，则表示变换可以分解成：旋转反射（U)+伸缩（E)+旋转反射（V')。奇异值部分的 E 表示矩阵作用在不同方向上的伸缩“强度”。但是这个伸缩是针对的被 M 作用的 x，而不是 M 内的元素本身。因此也不能把 muon 中的 E => I 理解成把 M 内的维度做了某种放缩归一。

既然 muon 可行，UV' 方向总该和 M 差不多吧——比如用 cosine 衡量的方向。经构造测试，假设M是方针，且 E 对角元素是 abs(正态) 的，二者确实还是很 cosine 相关的。如果 E 取差别更悬殊，cosine 会下降，终究比随机值要大得多（怎么也有零点一二吧）。

M_new = UV' 是正交矩阵，所有元素绝对值不超 1，而 M 最大值无上限限制（M = UEV' = { $\sum_k \sigma_k u_{ik} v_{kj}$ }, 按 muon 作者所言，M 原矩阵的奇异值{ $\sigma_k$ } 差异较大，那么确实 M 最大元素取值有很大可能），这也算是一种对高梯度值的那些参数的约束吧。但不足以解释 UV' 有效性。

从经验直觉，muon 作者这么说的：https://kellerjordan.github.io/posts/muon/:
> And for an empirically-flavored motivation, we observe that based on manual inspection, the updates produced by both SGD-momentum and Adam for the 2D parameters in transformer-based neural networks typically have very **high condition number**(最大最小奇异值的比例）. That is, they are almost **low-rank matrices**, with the updates for all neurons being dominated by just a few directions. We speculate that orthogonalization effectively increases the scale of other “rare directions” which have small magnitude in the update but are nevertheless important for learning.
>
> (人工检查看到，更新矩阵奇异值差异迥异，几乎都是低秩矩阵，所有神经元的更新都主要集中在少数几个方向上。因此 UV' 正交化在某种程度上放大了那些在更新中幅度较小但对学习仍然重要的“稀有方向”的尺度)

另外可以证明，和 M 的 $\sqrt{sum{|a_{ij}|^2}}$ Frobenius 范数距离最小的正交矩阵是 UV'（[Muon优化器赏析：从向量到矩阵的本质跨越 - 科学空间|Scientific Spaces](https://spaces.ac.cn/archives/10592)）。

y = f(Wx), 令 z = Wx, 则 $dy = \frac{\partial f}{\partial z} \cdot dW \cdot x$, 可以从这里感觉下 dW=w_t-w 对loss（y) 下降量的影响。若参数更新量是原始参差不齐的梯度，$dW \cdot x$ 对 x 的各维的影响不一: dW=UEV', 则E会令各维有迥异的伸缩率。若 dW=UV', 则仅仅是对 x 做了旋转反射，从而 x 各维会平等参与到 loss 下降中。

上述总总，让人觉得用 UV' 作优化方向，是有一定道理的，但总觉得有点糊涂——至少一点是，凭啥**一定**导致梯度下降。

### UVᵀ 是参数改变量在谱范数约束下的梯度下降方向

但是 UV' 的合理性，只靠直觉是不够的，需要严格的证明。下面证明方法来自 su jianlin https://spaces.ac.cn/archives/10592 ：

各种优化器，都可以转为在一定距离约束下的优化，也就是下面这样带约束项的形式：

$$
L_{new} = \lambda \lVert w - w_t \rVert^2 + L(w)
$$

其中 λ 为大值数, $\lVert \cdots \rVert$ 为某种范数。为了令 $L_{new}$ 更小，除了对它求导，还可以做转化换一个方式看：

令 

$$
\begin{cases}
γ &:= \lVert w-w_t \rVert = \lVert Δw \rVert \\
ϕ &:=− \frac {Δw} {\lVert Δw \rVert}  &// 为单位长度的方向 \\
g_t &:= \nabla L(w) & //是梯度 \\
L(w_t) &≈ L(w)+ {g'}_ {t} Δw &// 一阶展开 
\end{cases}
$$

则 $L_{new}$ 可以改写成：

$$
\begin{align}
\min L_{new} &= \min\[ λγ^2 + {g'}_t(- \frac {Δw}{\lVert Δw \rVert})(-\lVert Δw \rVert)\]  \\
&= \min \[λγ^2-{g'}_tϕγ \]
\end{align}
$$

其中 g'ₜϕ 为内积。

注意γ与ϕ是完全独立的，从而 min[λγ²-g'ₜϕγ] 可以独立优化，也就是可以 min[λγ²-g'ₜϕγ] = min[λγ²-γ max(g'ₜϕ)]
 
下面考察：g'ₜϕ，它们是两个 1d 向量的内积。但是 muon 设置下，gₜ 本为矩阵形式，ϕ 也是矩阵，所以 g'ₜϕ 内积乃展开成 1d 后的内积。如果仍然保持 gₜ 与 ϕ 是矩阵，则应该是：tr(g'ₜϕ)【这是因为 $tr(A'B) = \sum_{ij} {a_{ij} b_{ij}}$】。于是下面记 g'ₜϕ 为 tr(gₜ'ϕ)。

令 ${g}_t = UEV' = \sum_i^r \sigma_i u_i v'_i$, 这里 $u_i, v_i$ 是来自 UV 的列向量, $u_i v'_i$ 是外积所成的矩阵, r = rank(gₜ)。 则有：

$${g'}_t = VEU' = \sum_i^r \sigma_i v_i u'_i$$

$$
\begin{align}
\text{tr}(g'_t ϕ) &= \text{tr}(\sum_i^r \sigma_i v_i u'_i ϕ) \\
&= \sum_i^r \sigma_i tr(v_i u'_i ϕ)    & // tr 是linear的 \\
&= \sum_i^r \sigma_i tr(v_i (u'_i ϕ)) \\
&= \sum_i^r \sigma_i tr((u'_i ϕ) v_i)  & //tr(u'v) = tr(vu') 对 u, v 是向量\\
&= \sum_i^r \sigma_i (u'_i ϕ) v_i)     & //(u'_i ϕ) \cdot v_i 是数字, 故可以褪去 tr\\
&= \sum_i^r \sigma_i u'_i (ϕ v_i)  &// 结合律\\
& \le \sum_i^r \sigma_i & // v'_i (ϕ u_i) \le 1。原因见下
\end{align}
$$

为啥 $u'_i (ϕ v_i) \le 1$: 

- ϕ 是定义在一定范数距离下的单位方向矩阵，这个范数可以取 F 范数距离，也可以取其他的。这里取矩阵的谱范数。
- $1 = \lVert ϕ \rVert _{谱} := \max_x \frac {\lVert ϕ x \rVert_2} {\lVert x \rVert _2}$, 所以 $\frac {\lVert ϕ v_i \rVert_2} {\lVert v_i \rVert _2} \le 1 \Rightarrow \lVert ϕ v_i \rVert_2 \le \lVert v_i \rVert _2 = 1$ (U是正交的，故 $\lVert v_i \rVert _2 = 1$）
- $\lVert ϕ v_i \rVert_2 \le 1$, $\lVert u'_i \rVert _2 = 1$ ⇒ $u'_i (ϕ v_i) = \lVert u'_i (ϕ v_i) \rVert \le \lVert u'_i \rVert \cdot \lVert (ϕ v_i)\rVert  \le 1$

对于 $\sum_i^r \sigma_i u'_i (ϕ v_i) \le \sum_i^r \sigma_i$ 既然 $u'_i (ϕ v_i) \le 1$， 要使得等号成立，必须对任意 i 都有 $u'_i (ϕ v_i) = 1$。

$u'_i (ϕ v_i) = 1 \Rightarrow ϕ v_i = u_i \Rightarrow ϕ V = U \Rightarrow ϕ = UV'$

note: 
- 在参数更新的约束范数是 L_2, 步长是η 的约束下，单步最优方向等价于 $L_{new} = \lambda \lVert w - w_t \rVert_2^2 + L(w)$ λ=1/(2η) 的优化问题，可解出这时的最优方向正好是 L(w) 的梯度 gₜ（L_new 中对 L(w)用一阶展开，然后求导即可得）。在谱范数下，λ 与 η 的这种对应关系（λ=1/(2η)）不再成立。
- 同一个矩阵的 F 范数比谱范数要大。这能意味着啥嘛？按 sujianl https://www.spaces.ac.cn/archives/10739 （为啥？）：
  >跟SGD一样，Muon给出的同样是下降最快的方向，但它的谱范数约束比SGD的F 范数更为精准，所以有更佳的潜力

### UV' 的计算

可以证明 $UV' = (M M')^{-1/2} M$。其中 $(..)^{-1/2}$ 定义：可对角分解的矩阵 X 的函数 $f(X)$ 的定义是若 $X=P \Lambda P'$ 有正交+对角分解(或 $X=P \Lambda P^{-1}$, 即有可逆+对角的分解)，则 $f(X) := P \cdot f(\Lambda) \cdot P'$。这里 $X=MM'$ 对称矩阵，而 $f(.)=(.)^{-1/2}$。按此定义，可得： 

$$(M M')^{-1/2} M = ((UEV')(UEV')')^{-1/2}\cdot (UEV') = (UE^2U')^{-1/2} (UEV') = UV'$$

这样求 UV' 就归结为求 $(M M')^{-1/2} M$。

**$(M M')^{-1/2} M$ 的计算**：

Newton-Schulz 算法是一种用于矩阵平方根或矩阵逆平方根近似计算的迭代方法。muon名字中就有来自 Newton-Schulz 的字母。这个算法正是为了求出 $(M M')^{-1/2}$。

下面内容据 su jianlin https://spaces.ac.cn/archives/10592：

《《《《

$U(M M')^{-1/2} M = P (\Lambda)^{-1/2} P' M $， 而 $P (\Lambda)^{-1/2}$ 其实就是个分维进行的向量函数，每一维是 $\mathbb{R} \Rightarrow \mathbb{R}$。对单维，可以有 t=1 处的泰勒级数展开：

$$t^{-1/2} = 1 - \frac{1}{2}(t - 1) + \frac{3}{8}(t - 1)^2 - \frac{5}{16}(t - 1)^3 + \cdots$$

所以代回去后，就能有 $(MM')^{-1/2} M$ 的展开的表达式：

$$ 
(MM')^{-1/2} M = M - \frac{1}{2}(MM' - I)M + \frac{3}{8}(MM' - I)^2 M - \frac{5}{16}(MM' - I)^3 M + \cdots \\
$$

上式只取到 $(MM' - I)^2$ 忽略之后项，然后展开与合并后有(ai 算得）：
$$
(MM')^{-1/2} M = \frac{15}{8}M - \frac{5}{4}MM'M + \frac{3}{8}MM'MM'M + \cdots
$$

然后怎么导出的迭代式？？？该文还有，不深究了

他还有后续文章讲这个计算： https://spaces.ac.cn/archives/10922

》》》》

原始作者的讲解：

https://kellerjordan.github.io/posts/muon/ 这里讲得比较容易懂：

首先有这么一个结论（为啥？）：对于 $s \in [0, 1]$，存在某些多项式 $\phi(s) = a s + b s^3 + c s^5$，使得反复迭代后 $\phi^N(s) \to 1$。假设这样的 a b c 我们已经找到了。

对于矩阵 M=UEV', 试图定义它上面的 $\phi(.)$ 函数：

$$\phi(M) := aM + b(MM')M + c(MM')^2M$$

那么就有

$$
\begin{align}
\phi(M) &= (aI + b(MM') + c(MM^T)^2)M \\
&= (aI + bUE^2U' + cUE^4U^\top)UEV' \\
&= U(aE + bE^3 + cE^5)V' \\
&= U \phi(E) V'
\end{align}
$$

多次迭代，也就是有：

$$
\begin{align}
\phi(\phi(M)) &= U \phi(\phi(E)) V'  \\
\phi(\phi(\phi(M))) &= U \phi(\phi(\phi(E))) V'  \\
\end{align}
$$

或者说：

$$
\phi \circ  \phi \circ \cdots \circ \phi (M) = U \cdot \phi \circ  \phi \circ \cdots \circ \phi (E) \cdot V'
$$

E = {σᵢ} 是对角矩阵， 所以  φ∘φ∘⋯∘φ(E) = { φ∘φ∘⋯∘φ(σᵢ)}。

也就是说，如果 σᵢ 都在 [0, 1] 之间，足够多次迭代后，φ∘φ∘⋯∘φ(E) => I, 从而 φ∘φ∘⋯∘φ(M) = Uφ∘φ∘⋯∘φ(E)V' => UV'。这样就靠迭代把 UV' 算出来了（要先对 M 除以范数归一下）。

作者找到的 a b c 为： p(x)=3.4445x-4.7750x³+2.0315x⁵，在 405B Llama model 上，额外计算开销小于 1%。

迭代式迭代了，但是和牛顿好像没啥关系的样子（不得出现个梯度啊）。不深究了。

---

## 推向实用

- A:《MUON IS SCALABLE FOR LLM TRAINING》 https://arxiv.org/pdf/2502.16982v1
- B：《KIMI K2: OPEN AGENTIC INTELLIGENCE》 https://arxiv.org/pdf/2507.20534

### （1）weight decay

原始 Muon 没有 weight decay，大模型训练时权重和层输出 RMS（Root Mean Square 均方根, RMS = $\sqrt{\sum a_{i}^2}/ \sqrt{n}$） 会持续变大，超出 bf16 范围，导致性能下降。

于是采用 AdamW 方式的 weight decay： $W_t ​ =W_{t−1} ​ −η(O_t ​+ λ W_t−1)$, $O_t = UV'$ 抑制权重值过大（注意：按正则项放入 loss，则效果被优化器动量等操作所冲淡，所以才放入优化器）。λ 取 0.1 量级。

<img width="1374" height="628" alt="image" src="https://github.com/user-attachments/assets/826e3906-3ec2-447d-a1c6-b1570503272d" />

### （2）参数平均更新量（RMS衡量）的对齐

用 RMS，即 Root Mean Square 均方根 $\sqrt{\sum \Delta w_{i}^2}/ \sqrt{n}$ 来衡量 {$w_i$} 这多个参数的更新量{$w_i-w_{i-1}$} 的平均每参数的更新量。

上面 A 文指出，Adam/AdamW 的 update RMS 大约是 0.2 ~ 0.4。为啥？？

而 muon 会让同一个参数矩阵内的参数的更新比较平均，但是跨越不同参数矩阵，平均更新量却不同。作者证明了，对一个 shape=$A \times B$ 的参数矩阵，它的 update RMS 是 

$$\sqrt {1/\max(A, B)}$$

（为啥？？？）
这等于说，不同的参数矩阵用了不同的学习率，导致有的更新不够（从而训得不充分），有的过于大（从而训练不稳定）。因此需要每个参数矩阵都调一下，使得各用不同学习率。于是更新公式应该是：

$$
W_t = W_{t−1} − \eta_t(\sqrt {\max(A, B)} \cdot O_t+ λW_{t−1}); \ \ O_t = UV'
$$

**和 adamW 对齐：**

更新的参数除了矩阵，还有向量——这些更适合用 adam、adamW。那么 adamW 管理的参数的 RMS 也应该与 muon 的一致。于是上面式子调整为（取 adam RMS=0.2）：

$$
W_t = W_{t−1} − \eta_t(0.2 \cdot \sqrt {\max(A, B)} \cdot O_t + λW_{t−1}); \ \ O_t = UV'
$$

### （3）并行化

并行训练使得 muon 可能有问题。如果是张量并行，权重矩阵分散开，使得 muon 不可成行，这好理解。除此外，ZERO-1 训练也会导致 muon 不能用。zero 下，即使张量没拆分，参数和动量分片存储，每个 GPU 只拿到矩阵的一部分梯度，不能直接做正交化。

于是需要特别优化，注意每个 DP 组内每个 rank 都会重复做一次 gather + 正交化，这是刻意的换取简单实现和可并行重叠的通信。

<img width="1520" height="724" alt="image" src="https://github.com/user-attachments/assets/67ec1409-1b21-47ff-85b5-206dca5f8c1d" />

好像增加不少计算与通讯。文章指出，通信量为分布式 adamW 的 1~1.25倍，而总 latency 增加大约 1% ~ 3%。

### （4）QK-clip

训练超大规模 LLM 时，才出现的问题。 adamW 也有这问题吗？

在 Transformer 的注意力计算里：

$$
O^h = \text{softmax}\left( \frac{1}{\sqrt{d}} Q^h (K^h)^\top \right) V^h
$$

如果 $Q^h$ 和 $K^h$ 的范数不断变大，$QK^T / \sqrt{d}$ 里的最大 logit 也会变大，softmax 会变得极端尖锐（几乎是 one-hot），梯度传播会很不稳定，甚至梯度消失或爆炸。

QK-Clip 方法是：在每次参数更新后检查当前 batch 中每个 head 的 最大 logit：

$$
S_{\max}^h = \frac{1}{\sqrt{d}} \max_{X\in B} \max_{i,j} Q^h_i (K^h_j)^\top
$$

如果 $S_{\max}^h$ 超过了目标阈值 $\tau$，就把 $W_q, W_k$ 的权重按比例缩小，抑制 logits 增长。这个缩放只影响下一步的计算，不会回改当前步的前向/反向结果（只用作“后处理”）。

---

## **4. 特点**

* **不影响当前步的梯度计算**（forward/backward 完全照常进行），只是更新后做一次 clip。
* **阈值 $\tau$** 控制 logits 允许的最大幅度，比如设成 50 以内可以防止 softmax 饱和。
* 对 MLA（Multi-Head Latent Attention）等共享 Key 的结构，也能精细化裁剪，避免副作用。

---

📌 **一句话总结**
QK-Clip 就是一个**更新后“限速器”**，用来控制 Q 和 K 的权重增长，防止注意力 logits 爆炸，从而保持 softmax 的数值稳定性和梯度可传递性。

---

如果你需要的话，我可以帮你画一个 **QK-Clip 数据流示意图**，把“检测最大 logit → 计算缩放因子 → 裁剪 Q/K 权重”的过程画出来，会很直观。你要我画吗？









---

## 补充知识

**（1）、SVD 分解**

M = UEV' 分解的**存在性**：

M 是 $m \times n$ 矩阵，则 M = UEV' 可以分解为正交+对角+正交三个矩阵的乘积。是因为：

$M'M$ 是正定的，按线性代数可以有分解： $M'M = V \Lambda V'$， 其中 V 是正交矩阵， $\Lambda$ 对角。

令 $E = \sqrt{\Lambda}\sim n \times n$, 令 $U=MVE^{-1} \sim m \times n$，则 $U E V'=(MVE^{-1}) E V' = MVV' = M$, 即分解形式成立(还需吧 U 补成 mxm矩阵，把 E 也相应补零)。

此时还需保证 $U=MVE^{-1}$ 是正交的： $U'U = (MVE^{-1})'(MVE^{-1})={E'}^{-1} V'(M'M)VE^{-1}$ ，而 $M'M = V \Lambda V'= VE^2V'$, 代入可得  $U'U = {E'}^{-1} V'(VE^2V')VE^{-1}=I$。

E 对角元素排序后，分解的**唯一性**： $MM'=UEEU'$ , $M'M=V'EEV$ , 故而 $E^2$ 是 $MM'$ 的取值确定特征值，故E取值确定。

**（2）、矩阵谱范数：**

<img width="1410" height="1174" alt="image" src="https://github.com/user-attachments/assets/ec486978-9934-4e1e-943c-2edc50d48abe" />

**（3）、矩阵的符号函数**：

数学上大约有这么回事：$(M M')^{-1/2} M$ 称之为矩阵的符号函数。 总之，看来这个 UV' 确实可看做 M 的一种符号矩阵的推广，那么 UV' 用来代替 M，起到一种 lion 优化器中的符号方向的作用，是可以理解的。

下面是 ai 提供的一些知识：

<img width="1334" height="1090" alt="image" src="https://github.com/user-attachments/assets/394d2416-f6e4-400a-bdda-b63ce0365f5d" />

ai 又说：

<img width="1368" height="250" alt="image" src="https://github.com/user-attachments/assets/9bfab53a-d39a-4232-82dc-914b387400ff" />

### reference

- https://github.com/KellerJordan/Muon
- https://kellerjordan.github.io/posts/muon/
- [Muon优化器赏析：从向量到矩阵的本质跨越 - 科学空间|Scientific Spaces](https://spaces.ac.cn/archives/10592)
