# 《SmoothQuant: Accurate and Efficient Post-Training Quantization for Large Language Models》 https://arxiv.org/pdf/2211.10438

一个事实：矩阵乘法 XW，X作为上一层的激活，往往有 outlier channel 存在。

smoothQuant 要解决这问题（AWQ-202306 也是要解决这问题）。作者的想法是，把 这些 outlier 取值转移一部分到 W 上。

和 awq 对比：
- awq 只是量化 weight（且是3、4 bit 的量化)；矩阵乘法仍然在 fp16 上做(乃W4A16)。而 smoothQuant 是同时量化 weight 与 activation 到 int8（W8A8）。
- 大方向说，两者的量化策略简直一模一样(s 是对角矩阵）：
  - smoothQuant: $Y = XW = X s^{-1} s W \approx \text{quant}(X s^{-1}) \cdot \text{quant}(s W)$
  - AWQ: $Y = XW = X s^{-1} s W \approx (X s^{-1}) \cdot \text{quant}(s W)$

---

### smoothQuant 做法： $Y \approx \text{quant}(X s^{-1}) \cdot \text{quant}(s W)$

**（1）、原理： 激活 outliers 分摊到权重**

<img width="770" height="328" alt="image" src="https://github.com/user-attachments/assets/3c461c63-97fe-420d-95c2-2a1259086578" />

更详细阐述：

<img width="1294" height="826" alt="image" src="https://github.com/user-attachments/assets/af949051-0818-44c3-aa41-28f81a607893" />

**（2）、做法**

对 $Y \approx \text{quant}(X s^{-1}) \cdot \text{quant}(s W)$，展开下 $X s^{-1}$: 

$$
X \cdot \mathrm{diag}(s^{-1}) =
\begin{bmatrix}
x_{11} & x_{12} & \cdots & x_{1n} \\
x_{21} & x_{22} & \cdots & x_{2n} \\
\vdots & \vdots & \ddots & \vdots \\
x_{m1} & x_{m2} & \cdots & x_{mn}
\end{bmatrix}
\cdot
\begin{bmatrix}
s^{-1} _ 1 & 0 & \cdots & 0 \\
0 & s^{-1} _ 2 & \cdots & 0 \\
\vdots & \vdots & \ddots & \vdots \\
0 & 0 & \cdots & s^{-1} _ n
\end{bmatrix} = \begin{bmatrix}
x_{11}s^{-1} _ 1 & x_{12}s^{-1} _ 2 & \cdots & x_{1n}s^{-1} _ n \\
x_{21}s^{-1} _ 1 & x_{22}s^{-1} _ 2 & \cdots & x_{2n}s^{-1} _ n \\
\vdots & \vdots & \ddots & \vdots \\
x_{m1}s^{-1} _ 1 & x_{m2}s^{-1} _2 & \cdots & x_{mn}s^{-1} _ n
\end{bmatrix}
$$

s 的选取方法是 

$$
s_j = \frac{\max\left(|\mathbf{X}_j|\right)^{\alpha}}{\max\left(|\mathbf{W}_j|\right)^{1-\alpha}}
$$

它通过 $\alpha$ outliers 在 X 与 W 上的分布。一般 $\alpha=0.5$ 就可以。

**（3）、计算加速**

一般来说，令 s、t 是对角矩阵对角元素， $(\text{diag} _ s X) \cdot (W \text{diag} _ t)$ 这样对 X 与 W 作 缩放，才是硬件友好的。因为这是对 X 与 W 的连续存储施加同样的 scaling （X 是行元素连续，W 会是列连续）。

而 $X s^{-1}$ 与 $s W$ 都是逆此而行，计算效率低下。

**作者发现，可以这样提速：** 对于 $quant(s W)$, 可以提前离线算，而对于 $quant(X s^{-1})$ 来说，X 一般是上一层的 output——假设 $X = X_1 W_1$, 于是 $X s^{-1} = X_1 (W_1 s^{-1})$，则 s^{-1} 可以离线计算吸收到 $W_1$ 里。按 paper，若 X = norm（..) 也可以类似操作，未深入研究。

---

### 用于 transformer 

如下，除了 norm 层、softmax 之外，都是用 smooth-quant 量化的：

<img width="752" height="500" alt="image" src="https://github.com/user-attachments/assets/7a6c4ea3-e2bf-4648-84d7-26dace055163" />

---

### other

该 paper 中提到了三种量化，对 XW 来说：
- per-tensor: 可针对 X（激活），可针对 W（weight）
- per-token：针对 X 的行
- per-channel：针对 X 的列；或 W 的列。
  - 对 W：per-channel 量化就是 OBQ/GPTQ 的量化方式
  - 对 X：per-channel 量化才能解决 outlier 问题，也是 smooth-quant 的优化方向

<img width="1164" height="316" alt="image" src="https://github.com/user-attachments/assets/e46a252d-f2cd-4427-9691-b3edc7bd6e83" />
