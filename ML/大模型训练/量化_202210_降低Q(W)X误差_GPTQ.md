《GPTQ: ACCURATE POST-TRAINING QUANTIZATION FOR GENERATIVE PRE-TRAINED TRANSFORMERS》 https://arxiv.org/pdf/2210.17323

GPTQ 继承自 OBQ(Optimal Brain Quantization，2022), 而 OBQ 又是来自 OBS（Optimal Brain Surgeon，1993）。

名字由来: QPTQ = QPT(GENERATIVE PRE-TRAINED TRANSFORMERS) + Q(量化）。

这一类方法做的是训练后的量化。它针对的是 inference 中矩阵乘法的权重 w，而不管激活。它的基本思路是，选一批随机 sample 做 inference，从而可以得到每一个矩阵乘的激活 input X。对网络中的一个具体权重矩阵 W，寻找最佳量化 $\hat{W}$ 满足 $\text{argmin}_{\hat{W}} ∥W X − \hat{W} X∥_2^2$。

也就是说，用它做量化时，不关心网络结构是什么，原始 loss 是什么，而只需要知道一个权重 W 的典型 input X 啥样，就可以对 W 做量化。

GPTQ 文中试了 4 bit, 乃至于 2 bit 量化。但是只针对参数，对激活仍然保持高精度(FP16)，没有量化。

比它晚，但是基本精神一样【都是降低 $\hat{W}X$ 误差】的是 AWQ。AWQ 指出，GPTQ 的问题是容易过拟合，导致泛化性能差（见：《AWQ》 https://arxiv.org/pdf/2306.00978 ）

----

## 理论: OBQ - Optimal Brain Quantization，2022

发展脉络是 OBS => OBQ => GPTQ。但是背后的基本原理是一样的。看一些资料，OBS 是想把不重要的权重给置零，OBQ 是用同样的参数筛选方式，但是不是置零而是量化之。这里只看 GPTQ paper 中介绍的 OBQ。

### （1）、思路

如前所述，它只处理矩阵乘法，且只处理里面的权重。对一个具体权重矩阵 W，它的量化策略是，寻找 $\hat{W}=quant(W)$ 使得 $\hat{W}$ 满足 $∥W X − \hat{W} X∥_2^2$ 最小，其中 X 是一批样本做 inference 得来。

那么每个权重 $w \in W$ 都取最接近量化，这样可行吗？这样做都没反映出最小化 $∥..∥$，当然不好！。实际上，鉴于量化后的 $\hat{W}$ 是 “量化“的，也就是有限取值离散的，OBQ 真实想做的是：如果把所有可行解全遍历搜索一下，就能得到最佳 $\hat{W}$ 了。当然这样做会比较低效。所以 OBS/OBQ 在于有一套方法，能更高效低做，当然它的解法也不是全局最优解，只是比每个权重 w 取最接近量化要好。

注意，鉴于 OBQ 真实想做（但做不到的）的是全遍历搜出最佳解，所以对最终量化后的每个 $w \in \hat{W}$ 只是处于某一量化位而已，并不必然保证与原始 w 的数值差很小。

**可以对 W 每行独立量化：**

权重 W 一般是矩阵，WX 计算时，W 的每一行独立和 X 计算，且 $∥W X − \hat{W} X∥_2^2 = \sum_{row} ∥W_{row} X − \hat{W}_{row} X∥_2^2$, 所以可以对 W 每行独立量化：仿佛权重矩阵本来只是 1 x n 的。也就是如下形式的 W，可以独立处理每行：

$$
W \cdot X =
\begin{bmatrix}
w_{11} & w_{12} & \cdots & w_{1n} \\
w_{21} & w_{22} & \cdots & w_{2n} \\
\vdots & \vdots & \ddots & \vdots \\
w_{m1} & w_{m2} & \cdots & w_{mn}
\end{bmatrix} \cdot \begin{bmatrix}
x_1 \\
x_2 \\
\vdots \\
x_n
\end{bmatrix}
$$

OBQ 正是一次只考虑 W 的一行，这样 Wx 是 scalar 数字。除非说明，下面都假设 W 是列向量。

**迭代式：**

先列出每优化一个参数时的迭代公式，下文讲为啥。

参数迭代公式：

$$
\begin{cases}
w_q = \arg\min _ {w_q} \frac{(\text{quant}(w_q) - w_q)^2}{[H^{-1}] _ {qq}} & // 用来决定量化哪个参数\\
\delta_F = - \frac{w_q - \text{quant}(w_q)}{[H^{-1}] _ {qq}} \cdot (H^{-1}) _ {:,q} & // 其余参数怎么做补偿更新；\delta_F 是列向量
\end{cases}
$$
- $[H^{-1}] _ {qq}$ 是 $H^{-1}$ 的 row, col=q, q 的元素
- $(H^{-1}) _ {:,q}$ 是 $H^{-1}$ 的第 q 列元素构成的列向量
- $\delta_F$ 是列向量

涉及到的 Hessian 逆矩阵的迭代式：

$$
H _ {-q}^{-1} = \left( H^{-1} - \frac{1}{\left[H^{-1}\right] _ {qq}} H^{-1} _ {:,q} \, H^{-1} _ {q,:} \right) _ {-p}
$$

- 下标 -q 表示去掉第q维度。
- $H^{-1}$ 迭代前一步的 hessian 逆，用它可以得到当前 step 的 hessian 逆 $H _ {-q}^{-1}$。
- $H _ {-q}^{-1}$ 表示 $H^{-1}$ 去掉 q 行 q 列后所得的小一号的矩阵
- $\left[H^{-1}\right] _ {qq}$ 表示取 $H^{-1}$ 取 row, col = q, q 位置的标量元素
- $H^{-1} _ {:,q}$ 为 $H^{-1}$ 取第 q 列所得的列向量
- $H^{-1} _ {q,:}$ 为 $H^{-1}$ 取第 q 行所得的行向量

### （2）、为啥牵扯到 Hessian

鉴于 OBQ 是在最小化 $∥W X − \hat{W} X∥_2^2$，也就是以它为目标，可以列出 loss 如下；为方便理解，符号上令原权重是 $W_0$，量化后结果权重是 $W$，并都是列向量：

$$
Loss(W) = ∥X W_0 − X W∥_2^2
$$

一眼可看出该 loss 的最优解是 $W=W_0$，此时 loss = 0。岂不都不用优化了？注意这是个带约束的优化问题，约束是每个 w 都应该处于某一量化整点位。

对它做 $W_0$ 点的 Taylor 展开，注意 L 是二次的，所以正好可以精确展开到 2 阶：

$$
L(w) = L(w_0) + \nabla_w L(w_0)^\top (w-w_0) + \tfrac{1}{2}(w-w_0)^\top \nabla_w^2 L(w_0) (w-w_0)
$$

注意：
- L(w) 中 w 是列向量
- 在 $w_0$ 点 L(w) 取得最小值，也就是 $\nabla_w L(w_0) = 0$
- $\nabla_w^2 L(w_0)$ 就是 Hessian 矩阵，记作 H。它乃对称矩阵，可算得等于 $2XX^T$。
  - 若 X 是一条样本的，则 X 是列向量， $XX^\top$ 是外积。如果 X 是多条数据，则 X 是列向量的拼接，X = { $x_1, x_2, .., x_n$ }, $XX^\top = \sum_i x_i x_i^\top$。

于是 $L(w) = L(w_0) + \tfrac{1}{2}(w-w_0)^\top H (w-w_0)$, 而任一种量化方案 loss 差是 $\Delta L = L(w) - L(w_0) = \tfrac{1}{2}(w-w_0)^\top H (w-w_0)$。于是，OBQ 的量化思想归结为选择 $W$ 使得下式最小：

$$
\tfrac{1}{2}(w-w_0)^\top H (w-w_0) = (w-w_0)^\top X X^\top (w-w_0)
$$

### （3）、启发式逐权重量化：思路

- 一次量化一个参数：启发式逐个推进
  - 对待量化参数 { $w_i$ }, 找到最适当的一个并量化它，同时补偿调整其他未量化参数的取值，使得 $\Delta L(w)$ 可控。

下面说下它这个启发式逐参数量化咋做的。

它是逐参数量化的，对于已经量化的就不再管了（而未量化参数集合则是每次迭代少一个）。于是每量化一个参数的时候，仿佛面对的就是原始参数向量 W 一样（只是长度短了）。

一次量化一个参数，但其他的参数也会补偿更新——也就是一个迭代其实更新了所有参数。对权重 $W$ = { $w_1, w_2, .., w_n$ }，假设选定要量化的是 $w_q$，更新后的这n个参数是 $w_q^{'}$ 与 $w'_{F}$ (下标 F 表示不包含 q 的所有index)。那么这些更新应该满足：
- $w_q$ 按量化规则量化得到的 $w_q^{'}$, 而其他参数的更新方法应该是： $w_q \rightarrow w_q^{'}$ 的基础上最小化 $\Delta L$, 也就是
  
$$
w_{F}^{'} = argmin_{w_{F}} L(\{ w_q^{'}, w_{F} \})
$$

- 反过来，对 $w_q$ 来说，它如果知道 $w_{F}$ 会怎样根据 $w_q^{'}$ 而更新，它应该把这点考虑进去——这就是被优化参数的选择原则：作量化的参数 index 是

$$
  index = argmin_{q}\ \text{L}(\\{quant(w_q), argmin_{w_{F}}\ \text{L}(\\{ quant(w_q), w_{F} \\}) \\})  \ \ 或者说
$$

$$
\begin{cases}
w' _ {F} := argmin_{w_{F}}\ \text{L}(\\{ quant(w_q), w_{F} \\}) \\
index = argmin_{q}\ \text{L}(\\{quant(w_q), w' _ {F} \\})
\end{cases}
$$

- 上面颇有点博弈论的那意思。

根据以上，那么 $w_1, w_{2:n}$ 的更新公式就容易推导了：令 $e_q = quant(w_q) - w_q$，推导出其他 n-1 个参数的最佳补偿更新 $\delta_F$, 然后把 $\delta_F$ 代入 $\Delta L$, 并选出最适合(即使得 $\Delta L$ 最小)量化的那个权重。

### （4）、启发式逐权重量化：具体怎么做

假设选定对第 $q$ 维量化，记量化差 $e_q := {quant}(w_q)-w_q$, 并记其余 n-1 各参数的补偿更新改变量是 $\delta_F$，则有如下分块表达式：

$$
\Delta L = \tfrac{1}{2} {\Delta w}^\top H {\Delta w} = \tfrac12
\begin{bmatrix}
e_q^\top,
\delta_F^{\top}
\end{bmatrix}
\begin{bmatrix}
H_{qq},  H_{qF} \\
H_{Fq},  H_{FF}
\end{bmatrix}
\begin{bmatrix}
e_q \\
\delta_F
\end{bmatrix},
$$

注意 Hessian H 是对称的， $H_{qF}^\top = H_{Fq}$, $e_q$ 与 $H_{qq}$ 都是标量数字， $\delta_F$ 是列向量。

现在要固定 $e_q$ 把最优 $\delta_F$ 求出来。可以得出其最优解是 $\delta_F^\star = -H_{FF}^{-1} H_{Fq} e_q$。

**怎么求：**

这可以用直接展开 $\Delta L$ 并求导得到：展开 $\Delta L$ 的分块矩阵乘法表达式， 并关于 $\delta_F$ 求导有：

$$
\begin{cases}
f(\delta_F) := \Delta L = \tfrac{1}{2} e_q^\top H_{qq} e_q + \tfrac{1}{2} e_q (H_{qF}\delta_F + \delta_F^\top H_{Fq}) + \tfrac{1}{2}\delta_F^\top H_{FF}\delta_F \\
\nabla_{\delta_F} f(\delta_F) = H_{FF}\delta_F + H_{Fq} e_q
\end{cases}
$$

而最佳 $\delta_F$ 是满足 $\nabla_{\delta_F} f(\delta_F) = 0$ 的，于是解 $H_{FF}\delta_F + H_{Fq} e_q = 0$ 得 $\delta_F^\star = -H_{FF}^{-1} H_{Fq} e_q$。

再把 $\delta_F^\star$ 表达式代入 $\Delta L$, 又可得：

$$
\Delta L_{\min}(e_q) = \frac{1}{2} e_q^\top (H_{qq} - H_{qF} H_{FF}^{-1} H_{Fq} ) e_q
$$

于是需量化的那个参数下标 q，乃能令 $\Delta L_{\min}$ 取值最小的（其中 $H_{qq} - H_{qF} H_{FF}^{-1} H_{Fq}$ 称为矩阵的 Schur complement， 见下面）。

**迭代更新式:**

这样就得到了迭代更新式：

$$
\begin{cases}
e_q := {quant}(w_q)-w_q &\\
q = argmin_q \ \frac{1}{2} e_q^\top (H_{qq} - H_{qF} H_{FF}^{-1} H_{Fq} ) e_q & // e_q 是 scalar\\
\delta_F = -H_{FF}^{-1} H_{Fq} e_q &//\delta_F 是列向量
\end{cases}
$$

看起来和 paper 所给的不一样, paper 中的是：

$$
\begin{cases}
w_q = \arg\min _ {w_q} \frac{(\text{quant}(w_q) - w_q)^2}{[H^{-1}] _ {qq}} & \\
\delta_F = - \frac{w_q - \text{quant}(w_q)}{[H^{-1}] _ {qq}} \cdot (H^{-1}) _ {:,q} &// \delta_F 是列向量
\end{cases}
$$
- $[H^{-1}] _ {qq}$ 是 $H^{-1}$ 的 row, col=q, q 的元素
- $(H^{-1}) _ {:,q}$ 是 $H^{-1}$ 的第 q 列元素构成的列向量

下面用 Schur complement 推导出 paper 中的公式，并证明二者等价。先补充下相关知识

> （a)、Schur complement 的定义
> 
> 设一个分块矩阵

$$
M = \begin{bmatrix}
A & B \\
C & D
\end{bmatrix}, \quad D \text{ 可逆}.
$$

> 那么 $M$ 对 $D$ 的 **Schur complement** 定义为： $S = A - B D^{-1} C.$
> 
> 它的由来，见下图：
>
> <img width="708" height="396" alt="image" src="https://github.com/user-attachments/assets/d7ace931-8d81-4a01-86e2-c995399ab3fc" />
>
> Schur complement 有关内容，重点都在于消去一元后，关于另外一元的系数。
>
> （b)、用于矩阵求逆
>
>  <img width="1222" height="336" alt="image" src="https://github.com/user-attachments/assets/33c6d768-4f5f-4e93-ae2b-438f0f2adcf8" />
> 
> （c）、二次型消去一元，并求极值：对于任意二次型

$$
   Q(x,y) = \tfrac{1}{2}
   \begin{bmatrix} x^\top, y^\top \end{bmatrix}
   \begin{bmatrix}
   A & B \\
   B^\top & D \end{bmatrix}
   \begin{bmatrix} 
   x\\
   y \end{bmatrix},
$$

> 其中 x、y 是列向量，如果要“固定 $x$，消去 $y$”，最优值总是

$$
Q_{\min}(x) = \tfrac{1}{2} x^\top (A - BD^{-1}B^\top)x,
$$

> 这个是一个非常标准的结论。从而代入可以直接得到上面 $\Delta L_{\min} = \frac{1}{2} e_q^\top (H_{qq} - H_{qF} H_{FF}^{-1} H_{Fq} ) e_q$ 的表达式。

用以上矩阵求逆式子，就可以得到 paper 中的迭代公式（注意每迭代一次，F 小 1）：下面假设量化的参数是第一个：

<img width="1286" height="1124" alt="image" src="https://github.com/user-attachments/assets/f71cf29b-fa42-446c-bbe0-5c86e28eb6e8" />

上面推导，除了最后一步根据 $H^{-1} _ qq$, $e_q$ 是 scalar 而调整形式外，其余过程是假设 $e_q$ 是列向量推导的。

### （5）、Hessian 求逆的迭代求法

OBQ 在每步迭代中都是面对的一个新的 H（size 小 1），如果每量化一个参数，就算一个矩阵逆，计算量太大。作者给出了巧妙的迭代求逆式，每次借助上一个更大一圈的 H 的逆（注意 H 来自 X，每次的新 H 都是上一个更大一圈 H 的子矩阵）：

$$
H _ {-q}^{-1} = \left( H^{-1} - \frac{1}{\left[H^{-1}\right] _ {qq}} H^{-1} _ {:,q} \, H^{-1} _ {q,:} \right) _ {-p}
$$

- 下标 -q 表示去掉第q维度。
- $H _ {-q}^{-1}$ 表示 $H^{-1}$ 去掉 q 行 q 列后所得的小一号的矩阵
- $\left[H^{-1}\right] _ {qq}$ 表示取 $H^{-1}$ 取 row, col = q, q 位置的标量元素
- $H^{-1} _ {:,q}$ 为 $H^{-1}$ 取第 q 列所得的列向量
- $H^{-1} _ {q,:}$ 为 $H^{-1}$ 取第 q 行所得的行向量

仍然可以用 schur 补来证明此式。

<img width="1510" height="1086" alt="image" src="https://github.com/user-attachments/assets/3de4cb7f-28bc-448a-b0a7-1325af2c023c" />

这样，对一个权重行的量化，只需要在最开始算一次 $H^{-1}$，接下来每次量化一个参数并需要算一个更小的 H 逆的时候，就用该迭代式逐次算就行了，计算量很小。

----

## GPTQ

GPTQ 只是对 OBQ 的弱化版本与加速版本。

### （1）、不再优选最佳量化的那个参数，而是随便选一个都行；额外好处：可以并行量化权重矩阵 W 的不同行

**为啥可以不关心顺序**

> this is because the slightly lower number(更少数量的) of quantized weights with large individual error(大的量化误差）is balanced out by those weights being quantized towards the end of the process, when only few other unquantized weights that can be adjusted for compensation remain.

the slightly lower number(更少数量的) of quantized weights with large individual error(大的量化误差）：OBQ 希望每个参数量化的时候，量化误差都小些。或者说它的贪心量化方式，意在降低有 "大的量化误差" 的参数数量。这是通过量化参数的优先级完成的——先量化的那些参数，误差会小。

由于参数调整，OBQ 过程的最后阶段的量化误差必然比较大。但这是所剩未量化参数已经不多，补偿更新作用比较弱，力度不够了。

总之，没必要斟酌，直接随便一个顺序来逐参数量化即可。

**为啥可以并行**

- 不同权重行的并行：OBQ 把 W 拆成行并独立进行。GPTQ 发现，如果可以不关心量化的参数顺序，那么这些行可以并行量化。这是因为对一行权重量化的时候，依赖于 Hessian $H=XX^\top$ , 而不同的 $W_i$ 都作用于同一个 X。

### （2）、一次量化一行权重的多个参数（Lazy Batch-Updates）

- 必要性：每次更新都要改动一个很大的矩阵（Hessian 逆矩阵里的行列），运算量很小但内存访问很大 → GPU 算力吃不满，速度受限于内存带宽。
- 好处：计算量没变，但把“很多零碎的小更新”合并成“大批量更新”，显著提高 GPU 利用率。
  - paper 实验里，能带来一个数量级的加速，对大模型特别关键。

结合前面 GPTQ 一次处理 W 的所有行 { $W_i$ }，所以一次量化的参数量是 $B \times row\_cnt$, B=128 列。

前面 OBQ 是一次量化一个参数，如果一次量化多个，那么还用上面的推理逻辑，可以求得补偿更新式, 与Hessian逆的迭代式是：

$$
\begin{cases}
\delta_F^\star = (H^{-1}) _ {FQ} \big( [H^{-1}] _ {QQ} \big)^{-1} \big(w_Q-{quant}(w_Q)\big) & // 补偿更新, W_Q 是列向量, \delta_F^\star 仍是列向量 \\
H_{-Q}^{-1} = \Big( H^{-1} - H _ {:,Q}^{-1} \big([H^{-1}] _ {QQ}\big)^{-1} H _ {Q,:}^{-1} \Big) _ {-Q}  & // Hessian 逆的迭代式
\end{cases}
$$
- 下标 "-Q" 表示排除掉某些列或行
- $H^{-1}) _ {FQ}$ 中 FQ 含义：同上面 Fq, Q表示正在被量化的多个参数， F表示其余（没量化的）
- 限于多次迭代后的精度问题，GPTQ 并不用上面 $H_{-Q}^{-1} = ..$ 来算 hessian 逆。

**note：paper 中的补偿更新式有问题（shape 对不上）：**

<img width="512"  alt="image" src="https://github.com/user-attachments/assets/662b2dad-5839-43e0-8b5d-d7c3820a7354" />

为避免符号混淆， $H_F$ 这里改写为 H，并更正为：

$$
\begin{align}
\delta_{F} &= -(w_{Q} - quant(w_{Q})) \big([H^{-1}] _ {QQ}\big)^{-1} {H^{-1}) _ {F,Q}}^\top \\
&= -(w_{Q} - quant(w_{Q})) \big([H^{-1}] _ {QQ}\big)^{-1} (H^{-1}) _ {QF}
\end{align}
$$

- $(H^{-1}) _ {QF}$ 表示 $H^{-1}$ 分块为下面方式时，右上角那一块：

$$
H^{-1} = 
\begin{bmatrix}
h_{QQ}, h_{QF} \\
h_{FQ}, h_{FF}
\end{bmatrix}
$$

- 就形式来说，它是吧 $W_Q$ 当行向量看待，于是三个矩阵的shape 分别应该是 $[1, Q]\times [Q, Q] \times [Q, F] \rightarrow [1, F]$。


### （3）、 hessian $H^{-1}$ 的更精确求解：Cholesky 分解

- 迭代更新逆矩阵容易累积误差：连用 $H_{-Q}^{-1} = \Big( H^{-1} - H _ {:,Q}^{-1} \big([H^{-1}] _ {QQ}\big)^{-1} H _ {Q,:}^{-1} \Big) _ {-Q}$ 迭代导致
  - hessian 矩阵可能变得 indefinite，无逆。特别是批量量化时更容易发生。
    - 实践中作者看到，超过几 B 的模型，总会有某几层权重会导致这样。

解法：Hessian 对家元素加 $\lambda$, 再用 cholesky 分解法求逆。相关代码见下面：

```
    # from https://github.com/IST-DASLab/gptq/blob/main/zeroShot/models/gptq.py ，并稍微改变变量名
    
    damp = percdamp * torch.mean(torch.diag(H)) # λ=1% of the average diagonal value 
    H[diag, diag] += damp             # H += λE，使得变正定矩阵
    L = torch.linalg.cholesky(H)      # L = torch.linalg.cholesky(H), LL' = H，返回下三角矩阵（右上角为0）
    H_inv = torch.cholesky_inverse(L) # 根据L，求出 LL' 的逆（这样求逆的数值稳定性比较好）

    U = torch.linalg.cholesky(H_inv, upper=True) # 获得逆矩阵的分解的上三角矩阵。 UU' = H_inv
    Hinv = U  # 按算法一，以及代码后续把上三角当做 H⁻¹ 一样用
```

**附：关于上面借由 cholesky 获得原矩阵的逆的好处，ai 回答如下：**
> 在数值计算里，直接对矩阵做逆运算（例如 `torch.inverse`）通常不推荐，因为：
> * **数值不稳定**：直接求逆容易引入较大误差。
> * **计算开销大**：时间复杂度同样是 $O(n^3)$，但系数更大。
> * **实际需求中往往不需要完整逆矩阵**：大多数情况只需要解线性方程 $Ax=b$。
> 
> 如果矩阵 $A$ 是 **对称正定矩阵 (SPD)**，可以写成： $A = L L^T$, 其中 $L$ 是下三角矩阵。此时： $A^{-1} = (L L^T)^{-1} = (L^T)^{-1} L^{-1}$, 
> 这样就可以通过对三角矩阵求逆，再乘起来得到结果。
>
> 相比直接求逆，好处是：
> 1. **更快**：三角矩阵求解比一般矩阵简单。
> 2. **更稳定**：Cholesky 分解只在 SPD 情况下使用，数值性质更好，避免了常规逆运算可能带来的病态问题。
> 3. **专用场景优化**：很多机器学习/深度学习里的协方差矩阵、核矩阵（Kernel matrix）、Fisher 信息矩阵都是 SPD，适合用这个方法。


### (4)、用 Cholesky 分解的三角矩阵代替 $H^{-1}$ 

GPTQ 中两用 Cholesky 分解。
- 第一次只是为了算 $H^{-1}$，为了得到更数值稳定的 $H^{-1}$
- 第二次则是对算出的 $H^{-1}$ 再次用 Cholesky 分解成 $H^{-1}=R^\top R$, R 是上三角矩阵。然后他用这个 R 来巧妙取代 $H^{-1}$ 行事。也就是上面代码中的(重新复述下):
  ```
    U = torch.linalg.cholesky(H_inv, upper=True) # 获得逆矩阵的分解的上三角矩阵。 UU' = H_inv
    Hinv = U  # 按算法一，以及代码后续把上三角当做 H⁻¹ 一样用
  ```

**第二次 Cholesky 分解，用 R 代替 $H^{-1}$ 的合理性：**

行向量版的参数补偿更新式是 $\delta_F = -(w_{Q} - quant(w_{Q}))([H^{-1}] _ {QQ})^{-1} (H^{-1}) _ {QF}$，要对里面的 $([H^{-1}] _ {QQ})^{-1} (H^{-1}) _ {QF}$ 做取代。

令 

$$
R^\top \cdot R = 
\begin{bmatrix}
R^\top _ {QQ},\  0 \\
R^\top _ {QF},\  R^\top _ {FF} 
\end{bmatrix} \cdot \begin{bmatrix}
R_{QQ}, R_{QF} \\
0, \ \ R_{FF}
\end{bmatrix}  = \begin{bmatrix}
R^\top _ {QQ} R_{QQ}, \ R^\top _ {QQ} R_{QF} \\
R^\top _ {QF} R_{QQ}, \ R^\top _ {FF} R_{FF}
\end{bmatrix} = \begin{bmatrix}
{[H^{-1}]} _ {QQ}, \ {[H^{-1}]} _ {QF} \\
{[H^{-1}]} _ {FQ}, \ {[H^{-1}]} _ {FF}
\end{bmatrix}
$$

于是有：

$$
\begin{cases}
[H^{-1}] _ {QQ} = R^\top _ {QQ} \cdot R _ {QQ} \Rightarrow  ([H^{-1}] _ {QQ}) ^ {-1} = (R^\top _ {QQ} \cdot R _ {QQ}) ^ {-1} = R _ {QQ} ^ {-1} \cdot (R^\top _ {QQ})^ {-1} \\
(H^{-1}) _ {QF} = R^\top _ {QQ} R_{QF}
\end{cases}
$$

于是

$$
([H^{-1}] _ {QQ}) ^ {-1} (H^{-1}) _ {QF} = R _ {QQ} ^ {-1} (R^\top _ {QQ})^ {-1} R^\top _ {QQ} R_{QF} = R _ {QQ} ^ {-1} R_{QF}
$$

也就是参数补偿更新式可以是：

$$
\begin{align}
\delta_F &= -(w_{Q} - quant(w_{Q}))([H^{-1}] _ {QQ})^{-1} (H^{-1}) _ {QF} \\
         &= -(w_{Q} - quant(w_{Q})) R _ {QQ} ^ {-1} R_{QF}
\end{align}
$$

<img width="1438" height="836" alt="image" src="https://github.com/user-attachments/assets/9163ad9c-b50b-4114-a185-50300236cb41" />

### （5）、最终量化算法

最终得到的 GPTQ 量化算法如下：所用的参数补偿更新式是 $w_Q$ 为行向量：

<img width="1230" height="1204" alt="image" src="https://github.com/user-attachments/assets/18b9ec07-dc9a-4dbd-ac43-74f1628274fc" />

- $H^{-1} = (2XX^T + \lambda I)^{-1}$, 是通过 Cholesky 分解的方法求得逆，即： $H^{-1} = (L^T)^{-1}\cdot L^{-1}$
- 对该 hessian 逆，再做一次 Cholesky 分解，把所得的三角矩阵，当做 $H^{-1}$ 一样用于后续流程
  - 只用求一次：整个量化过程中都用它，每次迭代，按需拉取三角矩阵的子内容
- 一次处理一个 block B=128；但是对于 block 内的每个参数，是一个一个处理的

---

## GPTQ 具体怎么量化的

几个问题：
- 对于一个参数，怎么量化它的？用 scaling factor 那样方式吗
  - 先统计出 scale/zero 等用于量化具体参数。统计这些量的时候，在本权重矩阵上以一定方式进行
- gptq 量化一个参数后，对其余的参数有补偿更新，这导致统计出的 min,max等都失效了，用来量化被"更新"过的参数，不会有问题吗？
  - 确实有这问题。所以 gptq 采取的一个方式是，每量化若干个参数（即下面代码中的 groupsize），就要重置并重新统计下min/max等
- 那么需要把这些 scale/zero 存下来吗？
  - 需要存下，这样才能用于正常推理
- 怎么支持的 2bit，3bit，4bit 不同量化？
  - 不同 bits 代表允许切分成多少份。所以 bits 数只用于计算切分成多少份（maxq), 所以它才能同一方式处理不同bits的量化
- 量化公式是什么
  - $torch.clamp(torch.round(x / scale) + zero, 0, maxq)$, 也就是 $round(x/scale)+zero$, 然后使得必须在范围 [0, maxq]内
  - 逆回原值用 $scale \times (q - zero)$ 即可

看代码 https://github.com/IST-DASLab/gptq/blob/main/zeroShot/models/gptq.py ：

```

class GPTQ:

    def __init__(self, layer): # layer：所以 class GPTQ 一次处理一个 layer（但不是逻辑上一个 layer，而是一个基本操作 layer）
        self.layer = layer
        self.dev = self.layer.weight.device
        W = layer.weight.data.clone() # 获得该layer 的权重
        if isinstance(self.layer, nn.Conv2d): W = W.flatten(1)   # CNN-2d 也能处理
        if isinstance(self.layer, transformers.Conv1D): W = W.t()
        ...

    def fasterquant(self, blocksize=128, percdamp=.01, groupsize=-1): # 外层调用它
        W = self.layer.weight.data.clone()
        ...

        if not self.quantizer.ready():
            self.quantizer.find_params(W, weight=True) # 准备好量化用到的 scale, zero, min, max。可见对这些的统计不超本 layer
        ...

        damp = percdamp * torch.mean(torch.diag(H))
        diag = torch.arange(self.columns, device=self.dev)
        H[diag, diag] += damp
        H = torch.linalg.cholesky(H)
        H = torch.cholesky_inverse(H) # 求出了原 hessian 矩阵的逆
        H = torch.linalg.cholesky(H, upper=True)
        Hinv = H # H^-1 的分解后得到的三角矩阵
        # 这段就是上面引用过的，为了得到 cholesky 分解后的三角矩阵

        for i1 in range(0, self.columns, blocksize): # 遍历 blocks
            ...
            for i in range(count): # 遍历block内部
                ...
                if groupsize != -1:
                    if (i1 + i) % groupsize == 0:
                        # 这里" % groupsize" 的作用：GPTQ 量化过程中会调整未量化参数的取值，有可能在处理一个参数时，会超过提前算好的量化超参数。于是每量化 groupsize 个，就应该对 scale，zero，min/max 等重新统计下
                        # paper 中的 group-size，就指的这个
                        self.quantizer.find_params(W[:, (i1 + i):(i1 + i + groupsize)], weight=True)

                q = quantize(w.unsqueeze(1), self.quantizer.scale, self.quantizer.zero, self.quantizer.maxq).flatten() # 执行量化
                ...
                Losses1[:, i] = (w - q) ** 2 / d ** 2  # 量化误差
                ...
            ...
        ...
```

代码 https://github.com/IST-DASLab/gptq/blob/main/zeroShot/models/quant.py
```
def quantize(x, scale, zero, maxq):
    q = torch.clamp(torch.round(x / scale) + zero, 0, maxq) # 这表示怎么量化的。也就是 $round(x/scale)+zero$, 然后使得必须在范围 [0, maxq]内
    return scale * (q - zero) # 这表示把量化后的逆回原值。
    # 上面两行：
    #   第一行用于对一个 model 量化过程。
    #   第二行用于使用量化的 model inference 的时候

class Quantizer(nn.Module):

    def __init__(self, shape=1):
        super(Quantizer, self).__init__()

        # 下面三项就是量化而引入的额外存储，需要保存到最终的量化产物里
        self.register_buffer('maxq', torch.tensor(0))
        self.register_buffer('scale', torch.zeros(shape))
        self.register_buffer('zero', torch.zeros(shape))

    def configure(self, bits, perchannel=False, sym=True, mse=False, norm=2.4, grid=100, maxshrink=.8):
        self.maxq = torch.tensor(2 ** bits - 1) # bits 是要量化到几个bit。 maxq表示要量化位多少份。 bits=8，则 maxq=255； bits=2,则 maxq=3
        ...

    def find_params(self, x, weight=False): # 内部做了 zero/scale等的计算
        ...
        xmin = torch.minimum(x.min(1)[0], tmp)
        xmax = torch.maximum(x.max(1)[0], tmp)
        ...
        self.scale = (xmax - xmin) / self.maxq
        if self.sym:
            self.zero = torch.full_like(self.scale, (self.maxq + 1) / 2)
        else:
            self.zero = torch.round(-xmin / self.scale)
        ...

    def quantize(self, x):
        if self.ready():
            return quantize(x, self.scale, self.zero, self.maxq) # 调用 scale/zero/maxq作量化
        return x

```
