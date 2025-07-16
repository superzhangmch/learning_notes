《GME: Improving Universal Multimodal Retrieval by Multimodal LLMs》 https://arxiv.org/pdf/2412.16855

### 能干啥

能对 text（T)、img（I)、text+img（TI）、pdf截图（VD=visual document）的各种形式嵌入同一个语义空间，从而实现这几种方式的互相检索。

### 实现方法简述

1. 构建包括以上类型数据（T、I、TI、VD）的问答 pair 数据集
2. 对 pair 中问与答都用 qianwen-VL 获得 emb 表示（用最后一层最后一个token 的 latent），对 emb 用 cosine 算相似度，用对比学习的 infoNCE loss 训练。

----

下面展开：

### embedding 怎样构造出来

<img width="512" alt="image" src="https://github.com/user-attachments/assets/e5468d21-04b9-476c-87e1-50aca526a47d" />

qianwen-VL 模型可以以图、文作为 input prompt。这个 prompt 再附加一个 EOS token，作 pre-filling 式 inference，取 EOS token 的输出（the final hidden state
of the last token），即为最终的 embedding 表示。

实际用了：Qwen2-VL 2B 与 7B， lora（rank=8）。

### 怎样把 embedding 学出来

有了 pair 的各自 emb 构造法，下一步就是把 emb 学习出来。这时候用业界惯例——对比学习即可。

对比学习的一般思路是，用 cosine 做相似计算，然后把一个 obj 的少量匹配obj与大量非匹配obj 构建成 infoNCE loss：

$$
\mathcal{L} = -\log \frac{\exp\left(\cos(e_q, e_c^{+}) / \tau\right)}{\exp\left(\cos(e_q, e_c^{+}) / \tau\right) + \sum_{i=1}^{K} \exp\left(\cos(e_q, e_{c_i}^{-}) / \tau\right)}
$$

其中负样本要远多于正样本。对对比学习的原始数据集只有正样本对，所以负样本通过采样得到。

阿里 GME 也是这样。它的正负样本比是 1:8。在随机负采样寻完后，会拿新训 model 对数据集做过滤筛出 hard 负样本，并继续加强训下。

### 所用训练数据集

用了这几类数据：
- single-modal (T→T 用 MSMARCO dataset； I→I 用 imageNet)
- cross-modal (T→VD 用 Docmatix； T→I 用 LAION dataset)
- fused-modal (IT→IT 用 EVQA)

这有5种，再加上5种的mix，共六种数据，分别训练 6个 model。实验证实，mix 模式最好：

<img width="1076" height="576" alt="image" src="https://github.com/user-attachments/assets/3b693214-ac18-41c2-ae94-a3dfe97f0534" />


