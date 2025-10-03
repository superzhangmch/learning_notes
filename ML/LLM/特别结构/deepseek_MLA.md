- 我对原始deepseek-v3 代码加了注释的代码：https://github.com/superzhangmch/learn_DeepSeek-V3/blob/main/inference/model.py
- 所做笔记：https://zhuanlan.zhihu.com/p/1889957077524407359

上面笔记记载很多，但是是把学习过程记录进去了（而非彻底学通后的总结），比较乱。不想重新整理了，这里简单补充几句，作为总结。

1. MLA 节约显存在于先压缩再解压。
   - 假设压缩后的 q 与 k 分别是 latent_q 与 latent_k，还原映射分别是 proj_q_up 与 proj_k_up，则：`q = latent_q x proj_q_up`, `v = latent_k x proj_k_up`
   - 这样 qkᵀ 可以有两种表达方式：
     - (1). qkᵀ = `QKᵀ = (latent_q x proj_q_up) x (latent_k x proj_k_up)ᵀ`
       - 用它来作 attn，乃 MHA 的
       - 这样做，其实根本上没省下显存，因为需要还原。对超长序列，需要分块做 attn，想来也有效。但是无论如何：用 MLA 无疑使得多轮对话中把前面轮的 kv 给 cache 或存下来成为可能
     - (2). qkᵀ = `Q_new K_newᵀ = (latent_q x proj_q_up x proj_k_upᵀ) x latent_kᵀ`
       - `Q_new=latent_q x proj_q_up x proj_k_upᵀ`， `K_new := latent_k`
       - 用它来做 attn，本质上是 MQA 的：K_new 只有一个 head
         - 它在 inference 的时候，是有好处的（但 train/prefill 并不占优）
2. 上面两种 qk' 表达式, 结果上等价，但是计算量与显存占用不同。
   - train 与 prefill 的时候，适用第一种
   - decoding 的时候，适用第二种
3. 上面没考虑 rope 位置编码。施加 rope，则对 `(latent_q x proj_q_up) x (latent_k x proj_k_up)ᵀ` 无影响，而 ` (latent_q x proj_q_up x proj_k_upᵀ) x latent_kᵀ` 无法兼容 Rope：
   - 为啥不兼容：施加 rope 后需要在 ` (latent_q x proj_q_up x RRR x proj_k_upᵀ) x latent_kᵀ` 这里的  RRR 位置插入 rope 的变换矩阵。q 和 k 都是位置有关的，RRR 将会是与q 和 k 的位置都有关。这样导致没法把 (latent_q x proj_q_up x RRR x proj_k_upᵀ) 当做一个新定义的 q 看待。
   - 怎么解决：拉出一个 rope 分支。为了与非 rope 兼容（能改写成 MQA 模式）， rope 分支需要是 k 只有一个 head。

<img width="1790" height="904" alt="image" src="https://github.com/user-attachments/assets/0cc7725f-97f9-4367-85ac-842ab4d9193e" />
