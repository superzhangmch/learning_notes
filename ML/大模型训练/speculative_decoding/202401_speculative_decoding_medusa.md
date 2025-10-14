# 《MEDUSA: Simple LLM Inference Acceleration Framework with Multiple Decoding Heads》 2024.01 https://arxiv.org/pdf/2401.10774

medusa 不同于基于 draft model 的 speculative decoding：它是在原生 LLM 上做一些改造，使得 target LLM 自身就能给出 draft。


### 整体流程

<img width="1274" height="954" alt="image" src="https://github.com/user-attachments/assets/85f584ee-33da-4b4e-a21d-dbf6323d6120" />

如上图。

- 原生 LLM 的最后一层 hidden-states 处接多个并行的轻量级 medusa heads，每个 head 预测不同未来位置的一个 token。这样在生成当前token的同时，顺便生成了未来的几个token的候选，从而实现了轻量级 draft model 干的事。
- 鉴于预测的未来多位置的 token 不是自回归生成的，所以才可以生成（遍历式生成）多个候选的 draft-model 结果。为了从多候选中高效 verify 结果，于是用 tree-attention 的方式高效地做 forward 计算。

### 一、draft model 怎么做：medusa draft model head

第 k 个 head 的网络结构是：

$$
p_t^{(k)} = \mathrm{softmax}\left(
    W_2^{(k)} \cdot \left(
        \mathrm{SiLU}(W_1^{(k)} \cdot h_t) + h_t
    \right)
\right),
\quad
\text{where } W_2^{(k)} \in \mathbb{R}^{d \times V}, \ 
W_1^{(k)} \in \mathbb{R}^{d \times d}
$$

- 乃 MLP + resnet 的极简结构；
- $h_t$ 是最后一个 hidden
- 一般 5 个 heads 就行

怎么训练 medusa-heads：
- W_2 初始化为原 LLM 的 llm-head；W_1 初始化为 0
- 可以把主模型冻结，只训 head，这样的命名为 medusa-1
- 把主模型与 head 都训，叫 medusa-2
- 训练 loss 是不同 heads 的 loss 求和。loss weight $\lambda_k$：距离当前位置越远，weight 越小
    - $\mathcal{Loss} _ {\text{MEDUSA-1}} = \sum _ {k=1}^{K} -\lambda_k \log p_t^{(k)}(y_{t+k+1})$
- 训练数据：应该和打造原 LLM 时一样分布的数据集。如果找不到这样的数据集，那么可以用 self-distillation 用别的数据集的 prompt + 本 LLM 生成 answer 的方法构造出来。

注意：
- 它怎么实现轻量级预测的：一次重计算的 forward 生成当前 token 的同时，能顺便生成未来的几个token的候选。
- 为什么能一次 decoding 出多个候选：因为每个 token 位置是独立解码的。

### 二、target model 怎么高效作 candidates 的 verify 计算：tree attention

<img width="1218" height="942" alt="image" src="https://github.com/user-attachments/assets/ca660ddd-bbad-4faa-9212-bd4cb1327fa9" />

假设有两个 heads，分别取 top2，top3 个采样结果。则**排列组合**后有 6 种候选（后文讲，可以有一定的剪枝）。target model 验证 draft model 结果，而作 forward 的时候，按 naive 思路，就是构建一个 `batch-size=6，seq-len=prefix_len+2` 的 batch 然后做 forward。这样计算冗余太大。

于是作者使用 tree-attention：巧妙构建 attn-mask，从而可以在 `batch-size=1， seq_len=(prefix_len+树节点数)` 的数据上完成计算。上图左侧的 query 的 `root->head1->head2` 就是所说的 tree 结构；数节点数，也就是图左侧 query 长度会是： $\sum_{k=1}^K \prod _{i=1}^k s_i$, 其中 $s_i$ 表示第i个head的采样数。tree attn-mask 构建方式：对 tree 按节点逐层扫描，flatten 成一行，并在 attn-mask 矩阵中把 tree 的节点关系构造（从而获得了稀疏的 mask 矩阵），然后按一般方式做 attn 操作了。另外位置id，也要巧妙设置对。

怎么对树剪枝：

作者给的方法是用 calibration 数据集，统计出不同的head的不同top-i_th 位置的准确率。然后可以根据该统计信息，提前构建好剪枝后的 tree 结构。不同的 prompt 都用同样的剪枝树。怎么构建的：
> building a tree by adding nodes one by one, the contribution of a new node to the expectation is exactly the accuracy associated with the node.
>
> Therefore, we can greedily add nodes to the tree by choosing the node that is connected to the current tree and has the highest accuracy.
>
> (也就是：贪心方法：从根节点开始，逐个增节点，直到达阈值；每次新增的节点是accuracy最高的那个）

即使剪枝，一棵树的节点也会是很多的（paper 中例子：256节点剪到了64节点），这意味着作 verify 的时候，一次forward 好几十上百个token，计算量是很大的——相比之下，原生 speculative decoding verify 一次只有三五个token。

### 三、怎么采样

可以用原生 speculative decoding 的 rejection sampling。作者提到 rejection sampling 在target model 生成温度大时，效率低（温度大，则target model 预测概率低，从而导致accept率降低）。而现实中，大温度生成正是为了多样性，这时候其实应该多采纳 draft model 的结果（这样才体现了多样性）。因此作者断言：speculative decoding 的采样概率分布，不一定要精确拟合target model 的概率。

于是提出可以用 typical acceptance 方法来从候选中筛选，而不是 rejection sampling；公式是：

$$
p_{\text{original}} \left(x_{n+k}\mid x_1, x_2, \cdots, x_{n+k-1}\right) > \min \left(\epsilon,\, \delta \exp \left(-H \left(p_{\text{original}} \left(\cdot\mid x_1, x_2, \cdots, x_{n+k-1}\right)\right)\right)\right)
$$

也就是候选的 target 概率在该范围内的都接受，概率值不能太小；但是也不能太大。额外细节：
- 第一个token 要用 greedy，以便至少能decode出一个 token
- 鉴于一轮操作中有多个候选seq，要选最长匹配的那个作为结果



