# 《MEDUSA: Simple LLM Inference Acceleration Framework with Multiple Decoding Heads》 2024.01 https://arxiv.org/pdf/2401.10774

medusa 不同于基于 draft model 的 speculative decoding：它是在原生 LLM 上做一些改造，使得 target LLM 自身就能给出 draft。


### 整体流程

<img width="1274" height="954" alt="image" src="https://github.com/user-attachments/assets/85f584ee-33da-4b4e-a21d-dbf6323d6120" />

如上图。

- 原生 LLM 的最后一层 hidden-states 处接多个并行的轻量级 medusa heads，每个 head 预测不同未来位置的一个 token。这样在生成当前token的同时，顺便生成了未来的几个token的候选，从而实现了轻量级 draft model 干的事。
- 鉴于预测的未来多位置的 token 不是自回归生成的，所以才可以生成（遍历式生成）多个候选的 draft-model 结果。为了从多候选中高效 verify 结果，于是用 tree-attention 的方式高效地做 forward 计算。

### medusa draft model head

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
- 怎么训练 medusa-head：
  - W_2 初始化为原 LLM 的 llm-head；W_1 初始化为 0
  - 可以把主模型冻结，只训 head，这样的命名为 medusa-1
  - 把主模型与 head 都训，叫 medusa-2
  - 训练 loss 是不同 heads 的 loss 求和。loss weight $\lambda_k$：距离当前位置越远，weight 越小
    - $\mathcal{Loss} _ {\text{MEDUSA-1}} = \sum _ {k=1}^{K} -\lambda_k \log p_t^{(k)}(y_{t+k+1})$

注意：
- 它怎么实现轻量级预测的：一次重计算的 forward 生成当前 token 的同时，能顺便生成未来的几个token的候选。
- 为什么能一次 decoding 出多个候选：因为每个 token 位置是独立解码的。

### tree attention 高效计算怎么做的

<img width="1218" height="942" alt="image" src="https://github.com/user-attachments/assets/ca660ddd-bbad-4faa-9212-bd4cb1327fa9" />

假设有两个 heads，分别取 top2，top3 个采样结果。则**排列组合**后有 6 种候选（后文讲，可以有一定的剪枝）。target model 验证 draft model 结果，而作 forward 的时候，按 naive 思路，就是构建一个 batch-size=6，seq-len=prefix_len+2 的 batch 然后做 forward。这样计算冗余太大。

于是作者使用 tree-attention：巧妙构建 attn-mask，从而可以在 batch-size=1， seq_len=(prefix_len+树节点数) 的数据上完成计算。上图左侧的 `root->head1->head2` 就是所说的 tree 结构。对 tree 逐层扫描，flatten 成一行，并在 attn-mask 矩阵中把 tree 的节点关系构造（获得了稀疏的 mask 矩阵），然后按一般 attn 方式做就行了。



