## 《Conditional Memory via Scalable Lookup: A New Axis of Sparsity for Large Language Models》 https://arxiv.org/abs/2601.07372

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
  - hash 词表大小, 大约几百万行.
  - 多头hash 以减少冲突: "To mitigate collisions, we employ K distinct hash heads for each N-gram order n. Each head k maps the compressed context to an index within an embedding table E_{n,k} (of prime size M_{n,k})"

----

### 作者出发点: 

文章想把一部分"计算型参数"换成"存储型参数"。后者只查表不计算，可以放在显存之外，因此能用很低的代价把总参数量做得非常大. 

1. 稀疏化目前只有一种手段
MoE 靠"条件计算"扩大容量：参数量很大，每次只激活一部分，这已经是前沿模型的标准做法。作者的问题是：除了 MoE，还有没有别的稀疏化维度？

2. 语言建模其实包含两种性质不同的任务
原文说，语言建模包含 组合推理（compositional reasoning） 和 知识检索（knowledge retrieval） 两类子任务：
- 推理需要深层、动态的计算；
- 但相当一部分文本，比如命名实体、固定套话，是 "local, static, and highly stereotyped"（局部的、静态的、高度程式化的）。

经典的 n-gram 模型就能很好地捕捉这类规律，说明它们本来就适合用便宜的查表来处理。

3. Transformer 没有"查表"这个原语，只能用计算去模拟
这是全文的核心动机。原文的例子是：认出一个常见的多 token 实体，要消耗前面好几层的注意力和 FFN（论文表 3 有分析）。作者的说法是：

▎ "This process essentially amounts to an expensive runtime reconstruction of a static lookup table, wasting valuable sequential depth on trivial operations"

意思是，模型每次都在运行时花大力气重建一张本该是静态的查找表，把宝贵的网络深度浪费在简单的事情上。

4. 所以给模型补一个"条件记忆"维度
MoE 的条件计算负责动态逻辑，条件记忆用稀疏查表取出固定知识，两者互补。具体实现上，作者回头去用 n-gram 嵌入（fastText 那一类的老方法），再加上几项现代改造：tokenizer 压缩、多头哈希、上下文门控、多分支融合。

5. 接着提出一个新问题：参数预算怎么在两者之间分配
总参数固定时，该给 MoE 多少、给记忆多少？由此得出 U 形的配比规律。

6. 还有一个工程上的考虑
MoE 的路由是动态的，算到那一层才知道要用哪些专家。Engram 的地址只取决于 token ID，是确定的，所以能提前预取、把表放到 CPU 内存里，绕开显存的限制。原文给的数字是：100B 参数的表放在主机内存，开销不到 3%。

还有一个连作者自己都觉得意外的结果：本来以为记忆只会帮知识类任务（MMLU +3.4），结果推理（BBH +5.0）、代码和数学的提升更大。作者的解释是，前几层从"重建静态知识"里解放出来，相当于给推理增加了有效深度；注意力也不用再忙局部搭配，可以专心处理全局上下文，所以长上下文检索提升最明显。

一句话概括：Transformer 把"记住固定搭配"和"推理"混在同一套计算里做，浪费深度；Engram 把前者拆出来，交给一张查找表。

