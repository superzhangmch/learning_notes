
## attention-sink 问题

《EFFICIENT STREAMING LANGUAGE MODELS WITH ATTENTION SINKS》 https://arxiv.org/pdf/2309.17453 引入的 attention sink。

quietAttention 是为了解决 attn 时，没法令当前 token 和前面所有 token 都弱关注（近乎零 attend）的问题——也就是没法跳过 attention。于是对 softmax 的分母加一。

而 attention sink 则是说，prompt 中的前几个 token，可能字面上没啥特别含义，却常常被生成的 token 强 attend 到：强 attend 到无意义 token，按说这样的无意义token 可以去掉的。作者实验发现不行，它们在生成效果上是有作用的。也就是说，如果多轮对话 prompt 过长要截掉头部部分，并不能全部截掉，而应该保持前面几个 token 不变。

既然如此，如果训练的时候，就故意 prompt 头部加几个无实际文本意义的 attn sink tokens，inference 时候也用它们，训推一致，就早好不过了。

- sink token 指的是 prompt 中的前几个，而不是生成的前几个。
- 是前几个，而不是第一个。

<img width="1794" height="578" alt="image" src="https://github.com/user-attachments/assets/f2a414f9-5769-4f4d-8ef0-37f5ddc87231" />

## SreamingLLM

这篇 paper 研究 attention sink，是为了实现无限长度推理的 streamingLLM。streamingLLM 虽然可以无限长度生成，但是它 attention 只保持很短的滑动窗口。也就是说，不具有长记忆能力（生成小说，则前面提到的人物名字，后面就彻底不记得了）。如下图：streamingLLM 推理时，每一step 只看有限的历史，二把更早的 token 截走（但是需要把最开始的几个 token 保留；一般头3个token 足矣）。

<img width="1442" height="796" alt="image" src="https://github.com/user-attachments/assets/e1cf2305-7287-4529-83c8-eee7f4c2873f" />

----

##  attention-sink 背后道理

**（1）、按上面 paper：**

> The nature of the SoftMax function prevents all attended tokens from having zero values.（解释：softmax 不能给所有元素都赋0，而是会总和为 1）
>
> This requires aggregating some information from other tokens across
all heads in all layers, even if the current embedding has sufficient self-contained information for its
prediction. （解释：当前token如果有足够多的信息，不需要 attend 其他 token，根据 softmax 机制，是做不到的；总是要从其他位置收集过来信息）
>
> Consequently, the model tends to dump unnecessary attention values to specific tokens.（解释：如果当前token就是不想要其他token的信息，于是它的选择是：那我就从不重要的平凡 token处下手，手段是：给他赋予较大的 softmax 值。而这里被选中的不重要平凡 token，正是 prompt 最开头的 attn sink tokens）
>
> A similar observation has been made in the realm of quantization outliers (Xiao et al., 2023; Bondarenko
et al., 2023), leading to the proposal of SoftMax-Off-by-One (Miller, 2023 即 quietAttention) as a potential remedy. （解释：SoftMax-Off-by-One 也是当前token，不想要 attend 到东西，要摆脱其他token对当前的影响。二者异曲同工）

那么为什么sink 的都是prompt 头部的 token 呢？
> Why do various autoregressive LLMs, such as Llama-2, MPT, Falcon, and Pythia consistently focus on initial tokens as their attention sinks, rather than other tokens? (为啥是 initial tokens？）
>
> Our explanation is straightforward: (因为 inital tokens 被见得多)
>
> Due to the sequential nature of autoregressive language modeling, initial tokens are visible to all subsequent tokens, while later tokens are only visible to a limited set of subsequent tokens. As a result, initial tokens are more easily trained to serve as attention sinks, capturing unnecessary attention.

**（2）、《Why do LLMs attend to the first token?》 https://arxiv.org/pdf/2504.02732 也在讲为什么**



