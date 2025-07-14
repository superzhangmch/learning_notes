LLM 训练的时候，一般是右 padding。而 inference 的时候一般是左 padding。

首先，只有 batch 操作才需要 padding。所以如果一次 inference 一个，没必要 padding。

如果一次 infer 一批，那么为了充分用到 batch 的并行能力，需要一次生成 n 个 token。如果右 padding，生成的token 并不能对齐，所以才要左 padding。

训练时右 padding，infer 时左 padding，不一致不会有问题吗？答案是不会，以为 attention mask 会把 padding mask 掉。
