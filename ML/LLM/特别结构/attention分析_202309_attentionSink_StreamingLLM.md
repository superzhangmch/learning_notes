
## attention-sink 问题

《EFFICIENT STREAMING LANGUAGE MODELS WITH ATTENTION SINKS》 https://arxiv.org/pdf/2309.17453 引入的 attention sink。

quietAttention 是为了解决 attn 时，没法令当前 token 和前面所有 token 都弱关注（近乎零 attend）的问题——也就是没法跳过 attention。于是对 softmax 的分母加一。

而 attention sink 则是说，prompt 中的前几个 token，可能字面上没啥特别含义，却常常被生成的 token 强 attend 到：强 attend 到无意义 token，按说这样的无意义token 可以去掉的。作者实验发现不行，它们在生成效果上是有作用的。也就是说，如果多轮对话 prompt 过长要截掉头部部分，并不能全部截掉，而应该保持前面几个 token 不变。既然如此，如果训练的时候，就故意 prompt 头部加几个无实际文本意义的 attn sink tokens，inference 时候也用它们，训推一致，效果会更好。

- sink token 指的是 prompt 中的前几个，而不是生成的前几个。
- 是前几个，而不是第一个。

<img width="1794" height="578" alt="image" src="https://github.com/user-attachments/assets/f2a414f9-5769-4f4d-8ef0-37f5ddc87231" />

## SreamingLLM

这篇 paper 研究 attention sink，是为了实现无限长度推理的 streamingLLM。streamingLLM 虽然可以无限长度生成，但是它 attention 只保持很短的滑动窗口。也就是说，不具有长记忆能力（生成小说，则前面提到的人物名字，后面就彻底不记得了）。如下图：streamingLLM 推理时，每一step 只看有限的历史，二把更早的 token 截走（但是需要把最开始的几个 token 保留；一般头3个token 足矣）。

<img width="1442" height="796" alt="image" src="https://github.com/user-attachments/assets/e1cf2305-7287-4529-83c8-eee7f4c2873f" />

----

