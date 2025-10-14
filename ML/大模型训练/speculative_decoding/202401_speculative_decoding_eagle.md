# 《EAGLE: Speculative Sampling Requires Rethinking Feature Uncertainty》 https://arxiv.org/pdf/2401.15077

eagle 有 v1，v2，v3 三篇 paper。

这里看 v1。paper 看是比 medusa 还要好。

## 整体流程

<img width="1208" height="1138" alt="image" src="https://github.com/user-attachments/assets/84e18bc2-c70b-44d1-a8f7-5d728ba1e128" />

### 一、draft model：轻量自回归 head
在原始 LLM 上增加轻量的 draft 自回归 head。这点和 medusa 一样，但是 medusa 是多个并行 heads，分别预测不同位置的 tokens，从而实现多候选 seq 的生成。 eagle 的 draft head 是自回归的，只需要一个 head。

多候选怎么生成：draft model 每次生成一个 token的时候，要选取top K 个token，然后下一个 forward 自回归生成的时候，对这 K 个 token 都要作下一token生成。如是循环。这样就构建了一颗 tree 结构（如上图之下）。

### 二、verify 怎么做

target model 怎么计算 draft model 的结果的 logits 概率：和 medusa 一样用 tree attention

### 三、怎么对 draft 结果作 accept

用原生 speculative decoding 那样的拒绝采样法，保证结果的分布和原 LLM 一致。

----

## 自回归 head 细节

<img width="1036" height="802" alt="image" src="https://github.com/user-attachments/assets/565bd52c-e5ab-4d93-89c8-9630ad60a6c4" />

- 特征：每个 token 位置的 input：token emb + 该token的上衣位置的最后一层的hidden-stat
- 网络：
  - embedding 层、LM-head 层，共享
  - 自回归 head：FC + decoder-layer
- loss：
  - 训练的时候，原始 LLM 完全冻结。一次 target-model forward 把整个序列推理一遍，然后就可以得到 {$f_i$} 与 {$p_i$} 了。
  - 然后在此基础上，可以算得 draft-head 的 $\hat{f}_i$ 与 $\hat{p}_i$，从而构建出预测 hidden-state 的回归 loss，与token预测的分类 loss。最终loss 乃二者之和。详细 loss 式子见下面：

$$
\begin{align}
L_{\text{reg}} &= \text{SmoothL1}\big(f_{i+1}, \text{DraftModel}(T_{2:i+1}, F_{1:i})\big) &// f_{i+1} 乃target-model给出的\\
\\
p_{i+2} &= \text{Softmax}(\text{lmHead}(f_{i+1})) &// target-model 的预测概率\\
\hat{p} _ {i+2} &= \text{Softmax}(\text{lmHead}(\hat{f} _ {i+1})) &// \hat{f} _ {i+1} 乃 draft-model 预测出的\\
L_{\text{cls}} &= \text{CrossEntropy}(p_{i+2}, \hat{p}_{i+2}) \\
\end{align}
$$
