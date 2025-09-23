# 《attention-is-off-by-one》 https://www.evanmiller.org/attention-is-off-by-one.html

有可能一个 token 和之前的 context tokens 关联都不大（比如表达符号或一些太常见 token?）：那么 softmax(..) weight 就应该比较小。落实到计算 $softmax(q_n, k_j) = \frac {e^{q_n k_j}} {\sum e^{q_n k_i}}$ 上是 $q_n k_j$ 应该是个非常负的数才行。

但是 softmax(.) 乃和为 1 的概率值，即使每个 $q_n k_j$ 都充分小（负），假设是一样的充分小(记为 M），最终导致的却是 $softmax(q_n, k_j) ≈ \frac exp(M) {sum exp(M)} = \frac 1 n$ ——与我们希望他们趋于零不一致(虽然 n 大时， 1/n 也很小）。

----

于是一种解法 quietAttention 是：

$$
softmax_1(q_n, k_j) = \frac {e^{q_n k_j}} {1 + \sum e^{q_n k_i}}
$$

这样如果 $\sum e^{q_n k_i}$ 远大于1，则和普通 softmax 没啥区别。如果 $\sum e^{q_n k_i}$ 取值很小，则 $softmax(.) \rightarrow 0$, 完美实现了诉求（当然也就和小于 1 了）。

如果要用 softmax₁，需要在训练阶段就替换 softmax 为 softmax₁。而非 inference 时临时替换。

----

### 一个 "矛盾"
对一个 context 不敏感 token q，quietAtten 结果是 softmax_1(.) -> 0，意味着 $attn(q) = \sum_i softmax_1(q k_i) v_i \rightarrow 0$, 也就是 attn 最终结果约等于是 0 向量。

这导致一个（看起来的）矛盾：对于一个这样的 context 不敏感 token，在当前 step 做推理是要输出下一个 token的，而下一个 token 不一定仍然是 context 不敏感的。如果当前 token 的 forward 中每层/每 attn_head 的  attn(x) 都被“静默”（attn 输出为或近似为零），那么本 step 推理出的 output token 就是 context 无关的了。违背 Transformer 用 attention 融合上下文的目的，不符合预期与要求。

实际上是这样：所谓 context 不敏感 token q，只是就某些 layers/某些 attn_heads 而言的。不可能所有layer+所有 heads 都这样。quietAttention 只是自动地约束某些 heads 而已。也就是说：softmax_1 只是对当前step 网络中的某些节点去噪声做纯化而已。直观见下：

inference 单个 step：
- single layer: x = norm(multi_heads_attn(x) + x); x = norm(FFN(x) + x);
- input -> layer1 -> layer2 -> .. -> layer_last -> softax(.) -> output token

如上，如果所有 attn(x) == 0，则单个 layer 只剩下 FFN 层了，与前序 context 不再有关。而若部分 heads 的 attn(x) -> 0, 则对整个网络来说，另一些地方通过 resnet 结构透传数据而已，减少了原生softmax 导致的噪声 attn 结果的影响，于是整体上是有好处的。

**总结**

quietAttn 的核心是让那些关联性低的 layer/head 的 attention 输出可以接近零，只让输入透传，而不是强行混合无用 context。
