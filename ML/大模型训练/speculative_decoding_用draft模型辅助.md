### 基于 draft model 的 speculative decoding 

有两篇 paper 是关于基于 small draft model 的 speculative decoding 的。都是 google 家的（其中一篇是 deepmind的）。 

- 2022.11 《Fast Inference from Transformers via Speculative Decoding》  https://arxiv.org/pdf/2211.17192
- 2023.02 《Accelerating Large Language Model Decoding with Speculative Sampling》 https://arxiv.org/pdf/2302.01318
  > Coincidentally, the work in this manuscript was undertaken **concurrently and independently** of the work on speculative decoding from Leviathan et al. (2022).
  >
  > We focus more heavily the distributed serving setting for large models and offer some incremental optimisations, but otherwise the core underlying idea is the same. (背后做法一样。但本篇更侧重分布式 serving 与一些优化）

----

### 该方法怎么做的

首先要说明，基于 draft model 的 speculative decoding 方法的独特巧妙之处，draft model 固然越强越好，但是可以有任意能力，不影响最终结果和直接从大LLM 采样的一致性。

该方法流程如下（来自《Accelerating ..》一文）：

<img width="1228" height="868" alt="image" src="https://github.com/user-attachments/assets/478c0d79-f438-4650-8a5d-076778e8c45e" />

解释：
- 标 A 部分：用 draft model 自回归采样 K 个 token
- 标 B 部分：target model 用上一步生成的 k 个 tokens，做一次 forward。所得结果是 target model 对 draft model 建议的概率得分
  - 上面算法中写着 "in parallel", 其实只是说不必串行自回归。而不是说要对 k 个递增序列构建一个 size 为 k 的 batch= `{prefix, prefix+[x1], prefix+[x1,x2], .., prefix+[x1, .., x_k]}`，然后padding后推理（固然可以这么做，效果等价）
- 标 C 部分：依次看 k 个 draft model token 是否可以接受。要一直接受，直到 reject 然后退出。
  - 每次循环：按 P = min(1, q/p) 的概率，决定是否采纳 draft-model 的 token。这样，如果 q > p，即 target_prob > draft_prob，一定采纳。如果 q < p, 则按 q/p 的概率而采纳。r ~ U[0, 1] 和 min(1, q/p) 的比较，是为了完成这个 "是否采纳" 的概率采样。
  - 一旦不采纳，就要退出，并不理会后面的 token。但是退出时，可以额外采样一个token：根据 target-model 给出的概率分布，但是需要做一个调整。
- 标 D 部分：如果 k 个全接受了，那么根据target-model所得的概率分布，还可以额外采样一个 token。此时不需要作概率调整
- 上面算法，每跑一遍，target-model 推理一次；可以看到，至少可以产生一个 token。鉴于 draft model计算量远小于 target-model，所以即使全部拒绝了它的结果，总推理时间的退化也很有限。

**naive 的想法**

上面的方法，naive 的想法会是这样：A、B仍一样做法，而在C部分，按 target-model 的采样方法对概率分布作采样，如果采样出的 token 和 draft 的结果一样，则采纳；否则拒绝（同时用这次 target-model 采样结果作为本次的结果）。这样做，也能实现生成结果和直接用 target-model 生成的一致，拒绝时还不需要概率调整。起步很好！

注意这样做的接受率要低，所以不取：假设 draft 采样出了 token x，speculative decoding 的接受概率是 min(1, q(x)/p(x)), 而 naive 想法的接收概率是 q(x)。比较 min(1, q/p) vs q:
- q > p: min(1, q/p) vs q => 1 vs q => 1 > q, 前者胜出
- q < p: min(1, q/p) vs q => q/p vs q => q/p > q, 前者胜出

---

### 为啥该采样结果和直接 target model 采样相一致

下面看为啥上面算法流程的奇怪操作，采样结果的分布和直接 target model 采样相一致。注意，鉴于二者一致，所以 draft model 使用哪一种都是无所谓的，甚至用随机采样都行。

令 P 表示该算法的采样概率分布，则需要证明 P(x) == q(x), 对任意 x 属于词表成立（其中 q,p分别是target 与 draft 分布）。

该算法能采样出 x，可以通过两种途径：
- draft 直接命中 x 并被接受
- 被拒绝后的采样得到了 x 

于是：`P(X=x) = P(x 被采样且被接受) + P(被拒绝后采样得到了x)`。希望证明 `P(X=x) == q(x)`。

(1)、draft 被接受的概率

P(x 被采样且被接受})=prob(x被采样)⋅prob(x被接受)=p(x)⋅min[1, q(x)/p(x)]=min(p(x), q(x))

- prob(x被采样) = p(x)
- prob(x被接受) = min(1, q(x)/p(x))
- 注意 p(x)⋅min[1, q(x)/p(x)] = min(p(x), q(x))

(2)、拒绝后采样得到 x 的概率

P(被拒绝后采样得到了x)=prob(被拒绝)⋅prob(拒绝后的采样得到了x)

- prob(被拒绝)：这个指的是，无论 draft 采样出什么token 都被拒绝，而不只是说特定的 x 被拒绝。所以 `prob(被拒绝)=1-prob(有任意的一个token被接受)`。
  - 而 `prob(有任意的一个token被接受)=∑_y prob(y被draft采样出并被接收)`, 即为词表每个token都成功的概率和。根据前面一步可知，`prob(y被draft采样出并被接收)=min(p(y), q(y))`, 所以 `prob(有任意的一个token被接受)=∑_y min(p(y), q(y))`
  - 于是：`prob(被拒绝)=1-∑_y min(p(y), q(y))=1-∑ₓ min(p(x), q(x)) = ∑ₓ [p(x) - min(p(x), q(x))] = ∑ₓ max(0, p(x)-q(x)) = ∑ₓ max(0, q(x)-p(x))`
- prob(拒绝后的采样得到了x)：根据算法中定义是 `normalize(max(0, q(x)-p(x))) := max(0, q(x)-p(x)) / ∑ₓ max(0, q(x)-p(x)) == (q - p)₊`
- 上面两者相乘后，后者把前者的分母消掉，得到： P(被拒绝后采样得到了x)=max(0, q(x)-p(x))

（3）、上面两者相加，得到：`P(X=x) = P(x 被采样且被接受) + P(被拒绝后采样得到了x)=min(p(x), q(x))+max(0, q(x)-p(x))=q(x)`, 得证。

- p > q: min(p(x), q(x))+max(0, q(x)-p(x))=q(x)=q(x) + 0 = q(x)
- p < q: min(p(x), q(x))+max(0, q(x)-p(x))=p(x) + q(x) - p(x) = q(x)

上面证明，总结如下，来自 《Accelerating ..》中截图并改编：

<img width="1118" height="922" alt="image" src="https://github.com/user-attachments/assets/604e2a5e-b374-45f6-9b94-3645114ef46a" />

---

### 一些理论分析

下面主要来自 《Fast Inference ..》一文。

假设单个 draft model token 的的接受率是 β, 那么平均接受率 α := E(β), 即对于各种推理前缀时接受率的平均值。

（1）、每次迭代的平均接纳 token 数量怎么算

draft model 一次采样 K 个，那么平均接纳几个呢？这构成了一个 capped geometric 分布（截断几何分布）：它常用于表示「尝试直到成功」但尝试次数不能无限多的情形。假设 α 已经知道了，数学上可以得到，平均接纳 token 数为：

$$
E(\text{accept 数}) = \frac {1 − α^{k+1}} {1 − α}
$$

| a | k | 长度|
| -- | -- | -- |
|0.1|3|1.111|
|0.1|4|1.111|
|0.1|5|1.111|
|0.1|6|1.111|
|0.1|7|1.111|
|0.1|8|1.111|
|0.1|9|1.111|
|0.3|3|1.417|
|0.3|4|1.425|
|0.3|5|1.427|
|0.3|6|1.428|
|0.3|7|1.428|
|0.3|8|1.428|
|0.3|9|1.428|
|0.5|3|1.875|
|0.5|4|1.937|
|0.5|5|1.968|
|0.5|6|1.984|
|0.5|7|1.992|
|0.5|8|1.996|
|0.5|9|1.998|
|0.7|3|2.532|
|0.7|4|2.773|
|0.7|5|2.941|
|0.7|6|3.058|
|0.7|7|3.141|
|0.7|8|3.198|
|0.7|9|3.239|
|0.8|3|2.952|
|0.8|4|3.361|
|0.8|5|3.689|
|0.8|6|3.951|
|0.8|7|4.161|
|0.8|8|4.328|
|0.8|9|4.463|

（2）、平均接受率 α := E(β) 怎么算

上面证明中，已经有了对一次具体的前缀的接受率=prob(有任意的一个token被接受)=∑_y prob(y被draft采样出并被接收)=∑_y min(p(y), q(y)), 所以 $α = E_{prefix}\ \sum_x\ min(p(x|prefix), q(x|prefix))$

(3)、所需计算时间的提升怎么算

令 c = drafe_model跑一次时间/ target_model跑一次时间 （它取决于硬件等方方面面），一般 c < 0.05。k 是 draft model 的一次生成 token 数。

则所需时间的加速比是（base时间/speculative_decoding_time):  $\frac {1−α^{k+1}} {(1−α)(k c+1)}$

| α | k | c | 加速比| 
| -- | -- | -- | -- |
|0.5|3|0.01|1.820|
|0.5|3|0.05|1.630|
|0.5|4|0.01|1.862|
|0.5|4|0.05|1.614|
|0.5|5|0.01|1.875|
|0.5|5|0.05|1.575|
|0.5|6|0.01|1.872|
|0.5|6|0.05|1.526|
|0.6|3|0.01|2.112|
|0.6|3|0.05|1.892|
|0.6|4|0.01|2.216|
|0.6|4|0.05|1.921|
|0.6|5|0.01|2.269|
|0.6|5|0.05|1.906|
|0.6|6|0.01|2.292|
|0.6|6|0.05|1.869|
|0.7|3|0.01|2.459|
|0.7|3|0.05|2.202|
|0.7|4|0.01|2.666|
|0.7|4|0.05|2.310|
|0.7|5|0.01|2.801|
|0.7|5|0.05|2.352|
|0.7|6|0.01|2.885|
|0.7|6|0.05|2.352|
|0.8|3|0.01|2.866|
|0.8|3|0.05|2.566|
|0.8|4|0.01|3.232|
|0.8|4|0.05|2.801|
|0.8|5|0.01|3.513|
|0.8|5|0.05|2.951|
|0.8|6|0.01|3.727|
|0.8|6|0.05|3.039|

特别地，只要 α > c，则可以选择 k 使得加速比大于 1（加速比最少为 $\frac {1+α} {1+c}$ ）。

(4)、计算量的增加怎么算

令 c 表示每 token 的 draft model 与 target model 的计算量的比。则：

