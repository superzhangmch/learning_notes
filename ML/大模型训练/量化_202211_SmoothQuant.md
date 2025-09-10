# 《SmoothQuant: Accurate and Efficient Post-Training Quantization for Large Language Models》 https://arxiv.org/pdf/2211.10438

一个事实：矩阵乘法 XW，X作为上一层的激活，往往有 outlier channel 存在。

smoothQuant 要解决这问题（AWQ-202306 也是要解决这问题）。作者的想法是，把 这些 outlier 取值转移一部分到 W 上。

和 awq 对比：
- awq 只是量化 weight（且是3、4 bit 的量化)；矩阵乘法仍然在 fp16 上做(乃W4A16)。而 smoothQuant 是同时量化 weight 与 activation 到 int8（W8A8）。
- 大方向说，两者的量化策略简直一模一样(s 是对角矩阵）：都是做的outlier 分摊（分摊方式不同）：
  - smoothQuant: $Y = XW = X s^{-1} s W \approx \text{unquant} \circ \text{quant}(X s^{-1}) \cdot \text{unquant} \circ \text{quant}(s W)$
  - AWQ: $Y = XW = X s^{-1} s W \approx (X s^{-1}) \cdot \text{unquant} \circ \text{quant}(s W)$
- smoothQuant 是迁移后，大粒度对 W 与X 量化；awq 是对 W 作 gorup & per-channel 小粒度量化。

---

### smoothQuant 做法： $Y \approx \text{unquant} \circ \text{quant}(X s^{-1}) \cdot \text{unquant} \circ \text{quant}(s W)$

**（1）、原理： 激活 outliers 分摊到权重**

<img width="770" height="328" alt="image" src="https://github.com/user-attachments/assets/3c461c63-97fe-420d-95c2-2a1259086578" />

更详细阐述：

<img width="1294" height="826" alt="image" src="https://github.com/user-attachments/assets/af949051-0818-44c3-aa41-28f81a607893" />

下面实例下看看。对展开 $X s^{-1}$: 

$$
\hat{X} = X \cdot \mathrm{diag}(s^{-1}) =
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

**（3）、具体怎么量化**

对于 $\hat{W}=s W$, 可以提前离线算，而对于 $\hat{X} = X s^{-1}$ 来说，X 一般是上一层的 output——假设 $X = X_1 W_1$, 于是 $X s^{-1} = X_1 (W_1 s^{-1})$，则 s^{-1} 可以离线计算吸收到 $W_1$ 里，也就是并不需要专门乘 $s^{-1}$ 以便得到 $\hat{X}$。按【paper，若 X = norm（..) 也可以类似操作，未深入研究】

总之按这样的 outliers 分摊法，可以得到新的 

$$
Y=XW = \hat{X} \hat{W}
$$

到这一步，只是对 XW 做了等价变换，使得 outliers 也被 weight 分摊。

接下来就是怎么量化 $\hat{X}$ 与 $\hat{W}$。注意：不能把 $\hat{X}$ 的 $s^{-1}$ 当做反量化时的 scaling 因子。

**三种粒度的量化**

一说量化，就涉及粒度：

<img width="1164" height="316" alt="image" src="https://github.com/user-attachments/assets/e46a252d-f2cd-4427-9691-b3edc7bd6e83" />

该 paper 中提到了三种量化（见上图），对 $X \cdot W$ 来说：
- per-tensor: 可针对 X（激活），可针对 W（weight）
- per-token：针对 X 的行的量化
- per-channel：针对 X 的列；或 W 的列。
  - 对 W：per-channel 量化就是 OBQ/GPTQ 的量化方式
  - 对 X：鉴于outlier总出现于某些激活channel，所以如果能对 X 作 per-channel 量化，smoothQuant 等一众算法要解决的问题就迎刃而解了。
    - 但是这有硬件计算效率问题, 对 X、W 都量化则：
      - 对 X-per-token，计算是 $Y = \text{diag}(\Delta_{x}^{\text{FP16}}) \cdot (\bar{\mathbf{X}}^{\text{INT8}} \cdot \bar{W}^{\text{INT8}}) \cdot \text{diag}(\Delta_{w}^{\text{FP16}})$ ，它对硬件优化，这时X（W）的行（列）连续存储，对行（列）施加同一个 scaling 因子，计算高效。
      - 对 X-per-channel，计算是 $Y = \bar{\mathbf{X}}^{\text{INT8}} \cdot \text{diag}(\Delta_{x}^{\text{FP16}}) \cdot \text{diag}(\Delta_{w}^{\text{FP16}}) \cdot \bar{W}^{\text{INT8}} $，缩放因子在内部，计算效率低

这上一段可见，做 X 量化时，X-per-channel 效果好，但计算不友好。所以别的实现只好 X-per-token。那么 smooth-quant 呢？

一般来说量化粒度越小效果越好，而 X-per-channel 效果最好。对 smoothQuant 来说， $\hat{X}$ 与 $\hat{W}$ 的取值已经只有弱化了的 outliers 了，这样它也就不太挑量化粒度了（当然x-per-chanel 肯定更好，但是这不有计算效率问题嘛；smoothQuant 也拿他没办法）。

它倾向于大粒度（且不用 group 量化）量化，并于是它一口气给了三种（-o1, -o2, -o3)：

| Method              | Weight      | Activation             | OPT-175B | BLOOM-176B | GLM-130B* |
|---------------------|-------------|------------------------|----------|------------|-----------|
| FP16                | -           | -                      | 71.6%    | 68.2%      | 73.8%     |
| W8A8                | per-tensor  | per-tensor dynamic     | 32.3%    | 64.2%      | 26.9%     |
| ZeroQuant           | group-wise  | per-token dynamic      | 31.7%    | 67.4%      | 26.7%     |
| LLM.int8()          | per-channel | per-token dyn.+FP16    | 71.4%    | 68.0%      | 73.8%     |
| Outlier Suppression | per-tensor  | per-tensor static      | 31.7%    | 54.1%      | 63.5%     |
| --- | ---  | --- | --- | --- | --- |
| SmoothQuant-O1      | per-tensor  | per-token dynamic      | **71.2%**    | 68.3%      | **73.7%**     |
| SmoothQuant-O2      | per-tensor  | per-tensor dynamic     | 71.1%    | **68.4%**      | 72.5%     |
| SmoothQuant-O3      | per-tensor  | per-tensor static      | 71.1%    | 67.4%      | 72.8%     |

O1 粒度最小，效果最好；同样粒度的O2 与 O3，dynamic 现算量化 scaling 因子，要比 static 提前算的更好。

所以预期：
- 效果 O1 > O2 > O3
  - 上面表格差不多符合这点；在所给的 OPT-175B 表上某一重要指标，甚至 O3 最优。
- 计算速度 O3 > O2 > O1。

---

### 用于 transformer 

如下，除了 norm 层、softmax 之外，都是用 smooth-quant 量化的：

<img width="752" height="500" alt="image" src="https://github.com/user-attachments/assets/7a6c4ea3-e2bf-4648-84d7-26dace055163" />

----

### 知识点

1. Activations are harder to quantize than weights：
   - Activations 取值有 outliers；而weight 分布良好
2. Outliers make activation quantization difficult：
   - activation 中的 outliers 是起作用的，不能压制它。但是它导致 int 量化时，正常值都被挤压成 0 了
3. Outliers persist in fixed activation channels
