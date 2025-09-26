
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

这篇 paper 是从信息mix的角度来看。它的解释是：attention 会导致每个token的表示，都会混入前面token的信息，但是不是混入的越多越好；而是要有个度。而控制这个度的就在于 attention sinks tokens，这些sinks 能把 token 不需要的 softmax score 吸收。

这篇 paper 有一些复杂公式与理论的解释。不看这些，则其实就是说：tokens hidden states，应该在融合其他token基础上，保有独立性，而不是各个token states 看起来都差不多了——这样的话，就发生了paper中说的 rank collapse / representational collapse 了——这时候模式单一，表现力当然就差了。而 sink 的存在，正好能消除这一点。

<img width="1206" height="480" alt="image" src="https://github.com/user-attachments/assets/7123dfea-f0fb-4851-b09a-6a4d5a914d31" />

<img width="1394" height="460" alt="image" src="https://github.com/user-attachments/assets/4608f323-7c77-48be-aba9-c7102f580f02" />

- sink 是普遍存在的，而且规模越大、上下文越长，sink 现象越明显
  - <img width="666" height="138" alt="image" src="https://github.com/user-attachments/assets/8627d2a4-ec3a-4f4c-921b-790b2cb5cde4" />
  - 长上下文训练的模型 sink 更明显，而短上下文（128）的模型几乎没有 sink
- <bos> 作为 sink：
  - 如果训练时总是在开头放 ⟨bos⟩，推理时去掉它 → sink 消失，性能大幅下降。
  - 如果训练时没有 ⟨bos⟩，sink 依然会在第一个 token 出现，但稍微弱一些（既要承担语义表示，又要被部分注意力浪费掉，没 ⟨bos⟩ 那么纯粹）
    - 说明 sink 的形成几乎是“不可避免”的

---- 

### attention sink 的实际例子： openai 的 gpt-oss-120b

《gpt-oss-120b & gpt-oss-20b Model Card》 https://arxiv.org/pdf/2508.10925

在每个 attn head 的 softmax 的分母位置，有一个 learned bias。这样 softmax 总和就不是 1 了。

> Each attention head has a learned bias in the denominator of the softmax, similar to off-by-one attention and attention sinks, which enables the attention
mechanism to pay no attention to any tokens.

代码实现是（ https://github.com/huggingface/transformers/blob/main/src/transformers/models/gpt_oss/modeling_gpt_oss.py#L258 ）：

```
self.sinks = nn.Parameter(torch.empty(config.num_attention_heads)) # 每个 attn_heads 一个 sink bias 参数
...

attn_weights = torch.matmul(query, key_states.transpose(2, 3)) * scaling # QK'
...
    sinks = module.sinks.reshape(1, -1, 1, 1).expand(query.shape[0], -1, query.shape[-2], -1)
    combined_logits = torch.cat([attn_weights, sinks], dim=-1) # attn_w 增加 bias 项

    combined_logits = combined_logits - combined_logits.max(dim=-1, keepdim=True).values # 在新增的 logits 上开算
    probs = F.softmax(combined_logits, dim=-1, dtype=combined_logits.dtype)
    scores = probs[..., :-1]  # we drop the sink here
```

或者用式子表示：

（1）、标准注意力：普通情况下，每个 query $q_i$ 对 key $k_j$ 的注意力是：

$$
\alpha_{i,j} = \frac{e^{s_{i,j}}}{\sum_{t=1}^{T} e^{s_{i,t}}}
\quad \text{其中 } s_{i,j} = \tfrac{q_i \cdot k_j}{\sqrt{d}}
$$

这里 $\sum_j \alpha_{i,j} = 1$，必须把权重分配出去。

（2）、GPT-OSS 加入 sink

GPT-OSS 给每个 head 增加一个可学习参数 $b$，并在 softmax 里拼一个“虚拟槽位”：

$$
\widetilde{\alpha} _ {i,j} = \frac{e^{s_{i,j}}}{e^{b} + \sum_{t=1}^{T} e^{s_{i,t}}}\quad (j=1,\dots,T)
$$

$$
p_{\text{sink}}(i) = \frac{e^{b}}{e^{b} + \sum_{t=1}^{T} e^{s_{i,t}}}
$$

其中 $p_{\text{sink}}$ 是“把注意力分给 sink”的概率。 $e^b$ 相当于是个常数，但是不同 heads 取值不同。

（3）、丢掉 sink 概率

真正用于加权 value 的分布是：

$$
\alpha_{i,j} = \widetilde{\alpha}_{i,j},\quad j=1,\dots,T
$$

于是总和变成：

$$
\sum_{j=1}^{T} \alpha_{i,j}
= 1 - p_{\text{sink}}
= \frac{\sum_{t=1}^{T} e^{s_{i,t}}}{e^{b} + \sum_{t=1}^{T} e^{s_{i,t}}} \le 1
$$
