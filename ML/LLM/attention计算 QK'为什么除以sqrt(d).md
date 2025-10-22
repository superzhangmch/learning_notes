### （一）、假设

$Q_i = [q_{i1}, q_{i2}, \dots, q_{id}], \quad K_j = [k_{j1}, k_{j2}, \dots, k_{jd}]$ ，并且每个元素都是独立同分布的随机变量： $q_{ik}, k_{jk} \sim \mathcal{N}(0, 1)$，也就是说：

* 每个分量均值为 0
* 方差为 1
* 各维度相互独立

### （二）、求证 $var(Q_i \cdot K'_j) = d$

点积展开后 $Q_i \cdot K_j = \sum_{k=1}^{d} q_{ik} , k_{jk}$，这个求和包含 d 个乘积项。

每一项的期望与方差：

每个乘积项 $q_{ik}k_{jk}$ 的统计性质如下：

* 由于 $q_{ik}$ 和 $k_{jk}$ 独立，且各自均值为 0： $\mathbb{E}[q_{ik}k_{jk}] = \mathbb{E}[q_{ik}] \mathbb{E}[k_{jk}] = 0$
* 方差为： $\text{Var}(q_{ik}k_{jk}) = \mathbb{E}[q_{ik}^2 k_{jk}^2] - 0 = \mathbb{E}[q_{ik}^2] \mathbb{E}[k_{jk}^2] = 1 \times 1 = 1$

独立项求和: 因为这些 d 个乘积项相互独立且方差为 1，依据 方差可加性 ：

$$
\text{Var}\left(\sum_{k=1}^{d} q_{ik}k_{jk}\right) = \sum_{k=1}^{d} \text{Var}(q_{ik}k_{jk}) = d
$$

所以整体的分布具有：

$$
\mathbb{E}[Q_i \cdot K_j] = 0, \quad \text{Var}(Q_i \cdot K_j) = d
$$
 

因为 $Q_i \cdot K_j$ 是 d 个独立零均值随机变量的和， 根据 中心极限定理 $Q_i \cdot K_j \approx \mathcal{N}(0, d)$。当 (d) 足够大时，这个近似非常准确。

### (三）、为什么要放缩

因此：点积的期望为 0，标准差为 $\sqrt{d}$。 如果不做缩放，softmax 的输入数值大约落在 $[-3\sqrt{d}, 3\sqrt{d}]$ 的范围。比如 (d=64)，标准差就是 8——softmax 就非常**容易饱和**，不利于训练，所以要变得1方差。

