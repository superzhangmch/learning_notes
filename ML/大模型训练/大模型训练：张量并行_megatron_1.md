
# 张量并行

出于 《Megatron-LM: Training Multi-Billion Parameter Language Models Using Model Parallelism》 https://arxiv.org/pdf/1909.08053 ， megatron-1（后续还有2,3）中。

它是关于两个矩阵相乘的时候，通过对矩阵切分到不同 GPU 做分块矩阵乘法的并行方式。

----

## 怎么做

假设要计算 $Y=XW$, W是weight矩阵，X 是 shape=(batch_size, dim) 的矩阵。

### （1）. 只切一个矩阵：权重按列切分

权重 $W$ 按输出维度切分，每个gpu 存一份：

$$
W = \big[ W^{(0)}, W^{(1)}, \dots, W^{(p-1)} \big]
$$

每卡计算（每卡gpu 都有 X的副本）

$$Y^{(i)} = X W^{(i)}$$

也就是每卡拿到了结果的一部分维度，所以需要通过 **AllGather** （all-gather：每个阶段存的东西不同，同步使得每个节点拥有所有）拼接：

$$
Y = \text{AllGather}\left( Y^{(0)}, \dots, Y^{(p-1)} \right)
$$

<img width="962" height="222" alt="image" src="https://github.com/user-attachments/assets/7bdd5e89-6241-4aff-9394-506702d257b6" />

### （2）. 两个都切分：权重按行切分

权重 $W$ 按输入维度切分（每 gpu 存一份）：

$$
W = \begin{bmatrix} 
W^{(0)} \\ 
W^{(1)} \\
\dots \\ 
W^{(p-1)} 
\end{bmatrix}
$$

输入 $X$ 同样切分（每 gpu 存一份，X^i 要存在 W^i gpu 上）：

$$
X = \big[ X^{(0)}, X^{(1)}, \dots, X^{(p-1)} \big]
$$

结果是：

$$
Z=XW=\big[ X^{(0)}, X^{(1)}, \dots, X^{(p-1)} \big] \begin{bmatrix} 
W^{(0)} \\ 
W^{(1)} \\
\dots \\ 
W^{(p-1)} 
\end{bmatrix}
$$

每卡计算：

$$
Z^{(i)} = X^{(i)} W^{(i)}
$$

最后 **AllReduce(sum)** （all-reduce：每个节点存了分量，需要求和，把结果存于某一个节点， 然后把散播到所有节点）：

$$
Y = \sum_i X^{(i)} W^{(i)} = \text{AllReduce}_{\text{sum}}\left( Z^{(0)}, \dots, Z^{(p-1)} \right)
$$

<img width="696" height="346" alt="image" src="https://github.com/user-attachments/assets/b318b605-3c4d-4eb2-a368-e1d1dc977067" />

----

## megatron-1 怎么用它处理 transformer 训练的

它从 embedding、attention、FFN（MLP） 三个部分都做了张量并行。

### （1）、embedding

词表 tokens embedding 一般是存在同一个gpu上的，根据 one-hot 读取embeddings 其实就是矩阵乘法。

对于 input emb: 可以按token 维度切分，不同的 token 存于不同的 gpu，用的时候通过 all-reduce 拉过来。

对于 output emb：

### （2）、attention

### （3）、FFN/MLP
