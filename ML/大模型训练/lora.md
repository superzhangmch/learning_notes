### 超参数

lora 有两个重要参数 rank 与 lora_alpha。

rank 自然是 W'=W+AB 中 A 与 B 的秩。lora_alpha（ $\alpha$ ）指的是训练中下面式子中的 $\alpha$ ：

$$
W'=W + \frac {\alpha} {r} A B
$$

inference 推理的时候，并不需要它。所以 lora_alpha 的作用，训练时本质上和新定义一个 $\lambda$ 用于 $W'=W + \lambda A B$ 一样。二者等价。

一般情况选取 lora_alpha=2*r, 或者 lora_alpha=r。

### 初始化

- A：从 高斯分布或均匀分布 初始化，通常与原始网络的初始化方式一致。 例如： $A_{ij} ∼ N(0, 0.02)$
- B：初始化为全零矩阵。
