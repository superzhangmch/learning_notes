## PPO

PPO-llm-rlhf  是标准的 PPO RL 算法框架: actor/critic 模式. 每一token 就是一个 RL step. 

见: https://zhuanlan.zhihu.com/p/715488196

下面是 GRPO 系列的. 另外还有 kimi 的 mirror-descent 法, 见: https://zhuanlan.zhihu.com/p/1894514919472358155 , 二者区别:
- 都是对一个 prompt 采样n次的平均 reward, 来取代 value model 干的事
- kimi-MD 比 GRPO 更省显存, 连 ref model 都不需要了. 它的 KL 是拿参数更新前的和之后的比.
- GRPO 使用了 PPO 那样的 clip 法, 而 kimi-md 则不需要.
- kimi-md 是 one-step RL, 而 GRPO 是token 粒度的多 step RL.

## GRPO

![image](https://github.com/user-attachments/assets/51282531-5e7b-45e4-9dc7-6be61cbbbb3c)

单条数据的 G 个不同采样，决定出一个平均 reward。然后可以用它来得到G个采样各自的 advantage。critic model 计算出的 advantage, 也不过是作为 baseline 能提供平均值的估计; 既然多次采样能算出平均值, 就不用 critic model 好了——于是 grpo 省略了 critic model(或者说 value model).

注意区别: 
- PPO 的 critic model 的 output 是token-wise 的, 不同 token 不同取值(reward 引入 KL, 导致 reward 是 token-wise 的, 然后导致 value-func 是 token-wise 的)
- GRPO 用多次采样的 reward 平均值, 则不再是 token-wise, 而是这一组采样生成的样本, 都用这一个 avg reward.

![image](https://github.com/user-attachments/assets/919ffe18-2d26-4242-9a4e-081c1860891f)

如上 V(..) 就是 value func, 由value model(或者说 critic model)产生.

GRPO 中把 KL 项独立了出来，就不能通过蒙特卡洛采样来算了（否则只用 log(../..) 一项就行了）。但是有它的 unbiased estimator 估计，拿它来算即可。

**GRPO 为啥提取 KL 项出来** 

paper 原文说在于使得 advantage Â_{i,t} 更好计算:
> instead of adding KL penalty in the reward, GRPO regularizes by directly adding the KL divergence between the trained policy and the reference policy to the loss, avoiding complicating the calculation of Â_{i,t}

假如不这样则需要这样: R'_i := r_i − β·KL_i，Â_i := (R'_i − mean({R'_1, .., R'_G})) / std({R'_1, .., R'_G}). 注意这样和paper的把KL提出来之间, 并不是严格数学等价的.

**one-step RL, 还是 per token per step RL?**

PPO 是 per token per step RL 的. GRPO 和 PPO 有区别, 严格来说仍然是 per token per step RL 的. 
- PPO 有 critic 给每个前缀估一个 V(s_t)——这是 KL 项进 reward 导致的，同一条样本的不同位置会拿到不同的优势.
- GRPO 没有 critic，基线是只以 prompt 为条件的组均值，所以每个前缀拿到的都是同一个数。grpo 的 G个采样中的一条样本只有一个奖励 r_i，它的 output 的所有 token 位置共用同一个值，优势也一样：Â_{i,t} = (r_i − mean(r)) / std(r)，对所有 t 都相同(i 是第几条样本、t 是第几个 token)。所以同一条样本 i 的各个位置 t 共用一个 Â_i。
  - 还保留了两处逐 token 的东西(功劳分配按单步，信任域按 token)：
    - ratio 和 clip 是逐 token 算的：每个 token 都有自己的 π_θ/π_old 和裁剪判定。
    - KL 也是逐 token 算的：放在 loss 里，每个位置单独约束。
    - 不看正则项, grpo 可以看作是最后一个 token step 才拿到 reward 的多step RL.

![image](https://github.com/user-attachments/assets/5dfd14e7-faae-438c-99b4-ad97b3122cd7)

## DAPO

<img width="1924" height="448" alt="image" src="https://github.com/user-attachments/assets/dce88d3e-fb0e-4895-b7eb-67689490aaa1" />

如上图, r_{i,t}, A_{i,t} 和 GRPO 一样. 

DAPO 乃对 GRPO 的改进.

1. 去掉 KL 项: 做长 CoT 推理训练时，模型的分布本来就会大幅偏离初始模型，KL 这个约束没有必要.
2. 加补丁:
 
| 补丁                            | 修的问题                                       | 做法                                      |
|---------------------------------|------------------------------------------------|-------------------------------------------|
| ① Clip-Higher（Decoupled Clip） | 熵塌缩：模型很快变得高度确定，不再探索         | 上下限分开设：ε_low = 0.2，ε_high = 0.28  |
| ② Dynamic Sampling              | 零梯度组：全对或全错的组优势全是 0，白占 batch | 丢掉这些组，继续采样直到 batch 填满       |
| ③ Token-level loss              | 长回答的 token 权重偏小                        | 整组所有 token 一起平均，不再先句内平均   |
| ④ Overlong reward shaping       | 截断回答的奖励不准                             | 被截断的样本 mask 掉 loss，加上超长软惩罚 |

- Clip-Higher: ε_low/ε_high = 0.2/0.2  => ε_low/ε_high = 0.2/0.28
- Dynamic Sampling: G 次采样的 reward 都一样, 则这一组都不要了(没有信息增益, 学不到新东西)
- Token-level loss:
  - GRPO：先句内平均，再对样本平均（sample-level）, Loss := (1/G) · Σ_i [ (1/|o_i|) · Σ_t loss_{i,t} ]
    - 每条回答先压成一个数，然后 G 条回答等权平均。不管长短，每条回答的总权重都是 1/G。
  - DAPO：所有 token 放在一起平均（token-level）, Loss := (1 / Σ_i |o_i|) · Σ_i Σ_t loss_{i,t}
    - 每个 token 的权重都相同，回答越长，总权重越大(回答长, 但是有对有错, 所以不能说鼓励长回答)。
- Overlong reward shaping:
  - Overlong Filtering（超长过滤）: 被截断的样本直接 mask 掉 loss，也就是这条样本仿佛看不见. 可以剔除.
  - Soft Overlong Punishment（超长软惩罚）: 在硬上限之前设一个缓冲区，回答进入缓冲区后，按超出的长度线性扣分
  - paper中: 超过 20480：被截断; 16384 个 token 以内：不罚; 16384 到 20480 之间：线性扣分，从 0 扣到 −1，例如 18432 个 token 扣 0.5

## GSPO

**GSPO 相比 GRPO 的改进, 一句话说就是, 不再区分一个 sample 内的token之间如何, 只只看整段句子如何. 所以它的loss里, t 消失了. 为啥要这样:**

1. token 级的重要性比值本身就不成立
重要性采样的原理是：用行为分布（π_old）的很多样本求平均，再用比值去修正分布差异。GRPO 在每个 token 位置算 w_{i,t}，但在那个位置的条件分布上只有一个采样到的 token。只有一个样本，起不到分布修正的作用，比值只是给梯度乘上了一个随机的系数。这就是你记得的"token-wise 不靠谱"。

2. 这个噪声会累积，还会被 clip 放大
每个 token 都带一点噪声，回答越长累积越多。clip 又按 token 零散地把一部分 token 清零、一部分保留，让梯度更加不稳定。论文观察到，长回答、大模型的训练会因此崩溃，而且往往不可逆。

3. 优化的单位应该和奖励的单位一致
奖励是整句一个分，优势也是整句一个，那么 off-policy 修正（比值和裁剪）也应该按整句来做。GRPO 用 token 级的比值去配整句级的优势，单位对不上。

4. MoE 模型上问题最突出：参数一更新，同一个 token 可能被路由到不同的专家，单个 token 的比值会剧烈跳动。GRPO 训练 MoE 需要靠 Routing Replay 才能收敛；GSPO 把比值平均到整句之后，单个 token 的跳动被摊薄，就不再需要 Routing Replay 了。

所以 GSPO 的思路就是：既然逐 token 的区分本来就靠不住，干脆不区分，只按"这句话整体变了多少"来决定更新幅度。

**loss 中 sᵢ = (Πₜ wₜ)^{1/|yᵢ|} 为啥取指数: 其实就是平均到每个 token, 只是是几何平均**

真是要用的重要性采样因子是  $π_θ(y) / π_old(y) = Πₜ wₜ$. 但是只要每个 token 偏一点点，乘起来就会爆炸或者趋近于 0(理想情况 wₜ 应该围绕1, 多个约等于1的数相乘, 结果可能不是接近0就是很大)。

```
假设每个 token 的比值都是 1.01：
┌──────────┬─────────────────────┬─────────────────┐
│ 回答长度  │ 原始整句比值 1.01^L   │   开 1/L 次方之后 │
├──────────┼─────────────────────┼─────────────────┤
│ 10       │ 1.105               │ 1.01            │
├──────────┼─────────────────────┼─────────────────┤
│ 100      │ 2.7                 │ 1.01            │
├──────────┼─────────────────────┼─────────────────┤
│ 1000     │ 约 2×10⁴            │ 1.01            │
└──────────┴─────────────────────┴─────────────────┘
```

如果直接用原始比值：
- 长回答几乎永远被裁掉，因为比值远远超出 [1−ε, 1+ε]。
- 裁剪范围没法统一：短回答和长回答需要完全不同的 ε。
- 方差极大：一个 token 的抖动会被连乘放大。

开 1/|yᵢ| 次方，就是取几何平均： sᵢ = (Πₜ wₜ)^{1/|yᵢ|} = exp( (1/|yᵢ|) Σₜ log wₜ ), 它表示"这句话平均每个 token 变了多少"，长短回答落在同一个量级，一个很小的 ε（论文里是 3e-4 / 4e-4）就能统一适用。

为什么用几何平均，而不用算术平均 (1/|y|)·Σ w_t：序列概率本来就是 token 概率的乘积，在 log 空间里求平均最自然，s_i 仍然对应"整句概率比"这个含义，只是按长度归一了。
- 另外, 算术平均容易被单个异常大的 w_t 主导。几何平均在 log 空间求平均，对单个极端值更不敏感。比如一个 token 的比值是 4、其余是 1：长度为 10 时，算术平均是 1.3，几何平均约 1.15。
- 开了 1/|y| 次方之后，s_i 已经不是严格意义上的重要性权重了，严格的权重应该是原始的整句比值。所以它是一个用一点偏差换来大幅降低方差的近似，和 PPO 的 clip 本身就是有偏近似是同一类取舍。

<img width="2418" height="948" alt="image" src="https://github.com/user-attachments/assets/d491267c-aef5-4985-b6e6-3edc5a8e3a88" />

note: 上面没有 KL 项, 不是像 DAPO 一样不要了, 而是没写出(实际有它).

<img width="1628" height="270" alt="image" src="https://github.com/user-attachments/assets/1275218b-f667-4ad2-89f6-2b2ec27de1ad" />

用梯度角度, 二者形式一样, 只是对 $∇_θ ​log π_θ​(y_{i,t}​∣x,y_{i,<t}​)$ 的权重不同而已.
