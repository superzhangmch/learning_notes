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

paper 作者发现，对于一定的多模态检索任务，用混合数据集训练效果更好（相比用和任务适配的数据集）。

具体说来：
- 有三种检索类型：
  <img width="512" alt="image" src="https://github.com/user-attachments/assets/ff79afbd-576a-40b4-bf7c-5aef58ad9d52" />
- 有 4 类数据可用
  - single-modal 数据 (T→T 用 MSMARCO dataset； I→I 用 imageNet)
  - cross-modal 数据 (T→VD 用 Docmatix； T→I 用 LAION dataset)
  - fused-modal 数据 (IT→IT 用 EVQA)
  - mixed 数据：把以上三种混合

如上 T→T，I→I，T→VD，T→I，IT→IT，mix，共六种数据，用同一套模型超参，可以训练 6个 model。每个模型模型训好后，可以在这四类数据上分别作效果评测。既有下表（横轴 6 个是model，纵轴4个是测试的数据，每个 model 测试 4 次）：

<img width="512" alt="image" src="https://github.com/user-attachments/assets/c227cefb-466c-4ea3-b160-a0ddbe764c36" />

可以看到：
- 对具体 model：假设用 x 数据训练的，则它在 x 类数据上表现最好
- 对具体类型 data：每一种都是用 mix 训出的model，对该类 data 最优。 

---



