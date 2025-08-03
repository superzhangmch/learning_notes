《Qwen3 Embedding: Advancing Text Embedding and Reranking Through Foundation Models》 https://arxiv.org/pdf/2506.05176



<img width="1552" height="574" alt="image" src="https://github.com/user-attachments/assets/05cc09b3-6c1c-406a-b49d-f7c00b749ab7" />

### 方法概述

embedding、reranking 方法如图

(1) embedding

```
{Instruction} {Query}<|endoftext|>
```

然后取 EOS token 的最后一层的 hidden state 当做 embedding。（和 alibaba 的《GME》相似，但是本文没提它）

loss 用的对比学习的 infoNCE 的一个变体：

$$
\begin{align}
L_{\text{embedding}} &= -\frac{1}{N} \sum_{i}^{N} \log \frac{e^{s(q_i, d_i^+)/\tau}}{Z_i} \\
Z_i = &e^{s(q_i, d_i^+)/\tau}  &正 pair\\
&+ \sum_{k}^{K} m_{ik} e^{s(q_i, d_{i,k}^-)/\tau} & 明确的负pair\\
&+ \sum_{j \ne i} m_{ij} e^{s(q_i, q_j)/\tau} & 排除可能的负pair\\
&+ \sum_{j \ne i} m_{ij} e^{s(d_i^+, d_j)/\tau} & 排除可能的负pair\\
&+ \sum_{j \ne i} m_{ij} e^{s(q_i, d_j)/\tau} & 排除可能的负pair\\
\end{align}
$$

其中 $m_{ij}$： 只有在 $s_{ij} > s(q_i, d_i^+) + 0.1 \text{ or } d_j == d_i^+$ 时为 0（此时认为比较相关）。

```
<|im_start|>system
Judge whether the Document meets the requirements based on the Query and the Instruct provided. Note that the answer can only be "yes" or"no".
<|im_end|>

<|im_start|>user
<Instruct>: {Instruction}
<Query>: {Query}
<Document>: {Document}
<|im_end|>

<|im_start|>assistant
<think>\n\n</think>\n\n
```

让 model 输出 yes 或 no token。

训练：按一般 SFT 做即可。

inference：用这两个 token 的 logit 构建出2分类的 softmax score：

$$
\text{score}(q, d) = \frac{e^{P(\text{yes} \mid I, q, d)}}{e^{P(\text{yes} \mid I, q, d)} + e^{P(\text{no} \mid I, q, d)}}
$$

### 训练

<img width="1006" height="268" alt="image" src="https://github.com/user-attachments/assets/cf462d2c-6661-48c7-921a-6fc81ea678b7" />

如图三阶段训练。

下面 ai 总结：

这一节介绍了 Qwen3 Embedding 模型采用的多阶段训练策略，主要包括：

- 第一阶段：大规模弱监督预训练。使用基础模型生成的大量合成文本对进行训练，覆盖任务、语言、长度、难度等多个维度。这一步有助于模型获得较强的泛化能力。
- 第二阶段：高质量监督微调。利用精挑细选的高质量合成数据进行微调，进一步提升模型效果和任务适配能力。
- 模型合并（Model Merging）。引入球面线性插值（slerp）对多个训练中间模型进行合并，提升模型在不同分布下的鲁棒性和泛化能力。
- 此外，reranking 模型只采用第二阶段的监督训练，不包括第一阶段的弱监督训练。

数据：

- 合成数据包括检索、语义相似度（STS）、bitext 挖掘和分类等类型。
- 数据生成策略多样：使用 Qwen3-32B 模型基于预训练语料生成 query-document 对，引入角色视角、query 类型、长度、难度和语言等控制变量。
- 用户视角引导：每个 document 通过 retrieval 模型关联多个用户角色，以模拟真实用户提问，提升生成 query 的真实性与多样性。
- 数据筛选：总共生成约 1.5 亿对训练数据，通过余弦相似度筛选出质量高的数据（相似度 > 0.7），最终得到约 1200 万条高质量对用于第二阶段训练。
