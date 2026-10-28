### 《Conditional Memory via Scalable Lookup: A New Axis of Sparsity for Large Language Models》 https://arxiv.org/abs/2601.07372

<img width="1340" height="864" alt="image" src="https://github.com/user-attachments/assets/63b1363f-97e0-4108-9fb4-23a7f2549d8d" />

engram机制: 相当于把最近 n 个 token 合成一个"大 token"，给它一个专属的嵌入，直接加到当前位置. 效果上像是在不改 tokenizer、不扩输出词表的前提下，给模型加了一张"短语级词表"。
- 本来每个token 位置的hidden, 来自该 token emb, 以及 attn 而关联到的前面token 的 emb. 这里 engram机制, 则相当于是直接把前面的n个tokens, 组合成一个新的“大token”, 直接注入到了当前位置. 而不再需要费老劲儿通过attn. 

另外注意: 
1. 注意力还在，只是省了一部分活。
  - 局部搭配不用再靠前几层的注意力和 FFN 去拼凑，但长距离的依赖、推理仍然要靠注意力。论文的分析也印证了这一点：Engram 模型第 5 层的表示，相当于普通 MoE 模型第 12 层，前几层的负担确实被卸掉了一部分；长上下文检索（NIAH）提升最大，说明注意力腾出了能力去做更远距离的事。
3. 注入点不是输入层，而是第 2 层和第 15 层，而且要经过门控。
  - 这个"大 token"的嵌入要先和当前的 hidden 比对，由门控决定加入多少。原因是同一个短语在不同语境下意思可能不同，纯输入层的嵌入看不到语境。
4. "大 token"的词表是用哈希开出来的。用特征hash 那样的方法.
  - 所有可能的 2-gram、3-gram 数量是天文数字，不可能每个都分配一行。所以用哈希把它们映射到有限大小的表里，冲突不可避免，再用多个哈希头把冲突的影响降下来。高频的搭配因为训练得多，嵌入会学得比较好；罕见搭配即使撞了行，影响也有限。

