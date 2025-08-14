
# 张量并行

出于 《Megatron-LM: Training Multi-Billion Parameter Language Models Using Model Parallelism》 https://arxiv.org/pdf/1909.08053 ， megatron-1（后续还有2,3）中。

多余多层 model，pipeline并行时 对于层聚合划分。而张量并行则是保持层数不变，对于单层内的每个矩阵乘法作分布式计算（切分到多个 gpu 上）。它们俩都是把大模型拆散到多 gpu，所以常都被称为模型并行。

张量并行是关于两个矩阵相乘的时候，通过对矩阵切分到不同 GPU 做分块矩阵乘法的并行方式。

----

## 怎么做

假设要计算 $Y=XW$, W是weight矩阵，X 是 shape=(batch_size, dim) 的矩阵。

### （1）. 只切一个矩阵（单切)：权重按列切分

权重 $W$ 按输出维度切分，每个gpu 存一份：

$$
W = \big[ W^{(0)}, W^{(1)}, \dots, W^{(p-1)} \big]
$$

每卡计算（每卡gpu 都有 X的副本）

$$Y^{(i)} = X W^{(i)}$$

也就是每卡拿到了结果的一部分维度，所以需要通过网络交互 **AllGather** （all-gather：每个阶段存的东西不同，同步使得每个节点拥有所有）拼接：

$$
Y = \text{AllGather}\left( Y^{(0)}, \dots, Y^{(p-1)} \right)
$$

<img width="962" height="222" alt="image" src="https://github.com/user-attachments/assets/7bdd5e89-6241-4aff-9394-506702d257b6" />

### （2）. 两个都切分(双切）：权重按行切分

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

最后通过网络交互 **AllReduce(sum)** （all-reduce：每个节点存了分量，全求和后把结果散播到所有节点。all-reduce=scatter_reduce + all_gather）：

$$
Y = \sum_i X^{(i)} W^{(i)} = \text{AllReduce}_{\text{sum}}\left( Z^{(0)}, \dots, Z^{(p-1)} \right)
$$

<img width="696" height="346" alt="image" src="https://github.com/user-attachments/assets/b318b605-3c4d-4eb2-a368-e1d1dc977067" />

以上两种方式，一般是综合运用。比如对于 XW，两种都可以。如果 XW 有激活【即 f(XW)】，则是单切。如果是 $W2 f(\cdot X \cdot W1)$ 形式，则是单双混合。

----

## megatron-1 怎么用它处理 transformer 训练的

它从 embedding、attention、FFN（MLP） 三个部分都做了张量并行。

### （1）、embedding

词表 tokens embedding 一般是存在同一个gpu上的，它其实是参与矩阵乘法，所以可以张量并行。

- input emb: one-hot 读取 embeddings 其实就是矩阵乘法。可以按 token 维度切分，不同的 token 存于不同的 gpu，用的时候通过 all-reduce 拉过来。
- output emb：也按 token 划分。单个 gpu 上：对于一个 token，可以算出它的交叉熵 loss，于是跨 gpu 直接聚合 loss 即可。 

### （2）、attention

其实就是对 X->QKV, out->X 这几个 projection 所关联的矩阵乘法，作张量并行。方法是按 attn heads 切分作“单切”。attn结束后的proj，则执行双切。

<img width="1044" height="762" alt="image" src="https://github.com/user-attachments/assets/11f953d2-f6e4-4135-97cc-301609eb0d4a" />

### （3）、FFN/MLP

$FFN(X) = W_2 \cdot \text{actFunc}(X \cdot W_1)$, 对于内部的 $Y=X \cdot W_1$，单切 $W_1$ 或者 “X与 $W_1$ 双切”，都可以，但是由于有激活函数，所以要用单切。然后 $W_2 \cdot Y$, Y 已经切开了，这时候对 $W_2$ 作切分即可，整体式双切。

<img width="1032" height="464" alt="image" src="https://github.com/user-attachments/assets/0e927872-9761-4290-932b-b2bed769e0aa" />

### （4）、通讯开销

megatron-1 通讯开销：对于 transformer 一层来说，训练时forward+backward 一共有额外 4 次 all-reduce（all-reduce：先把不同节点的值累加，然后所有节点都有该累加值）。增加通信，所以一般张量并行在单机多卡内进行。

<img width="962" height="572" alt="image" src="https://github.com/user-attachments/assets/b7295661-ef98-44d0-adc9-4a9912ed8944" />

### （5） dropout, layer normalization, or residual connections

> we maintain duplicate copies of layer normalization
parameters on each GPU, and take the output of the model
parallel region and run dropout and residual connection
on these tensors before feeding them as input to the next
model parallel regions. To optimize the model we allow
each model parallel worker to optimize its own set of parameters. Since all values are either local to or duplicated
on a GPU, there is no need for communicating updated
parameter values in this formulation.

### （6）、megatron-1 的实践

megatron-1 的张量并行，可以和数据并行组合使用。一般张量并行示例部署到同一台机器的多卡上，这样通讯开销最小。

<img width="758" height="622" alt="image" src="https://github.com/user-attachments/assets/2ddfad58-07f7-4d14-8751-6a7ae1a62e8a" />
