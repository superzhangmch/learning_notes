# Multi-teacher On-Policy Distillation (MOPD)

- 《MOPD: Multi-Teacher On-Policy Distillation for Capability Integration in LLM Post-Training》 小米 https://arxiv.org/abs/2606.30406
- 《MiMo-V2-Flash Technical Report》 https://arxiv.org/pdf/2601.02780, 就用到了它

一句话说: 先SFT然后以他为基础, 不同领域分别 RL, 这样得到多个领域专家, 然后再对原来的 sft model, 把这些能力蒸馏过去.

<img width="2020" height="1160" alt="image" src="https://github.com/user-attachments/assets/21c830d0-c002-4dc4-9286-1b175a4df545" />

对于stage3: student 蒸馏 teachers, 是做的KL距离逼近. 这一step, 也是通过 RL 来做的. 方法来自 《MiniLLM: On-Policy Distillation of Large Language
Models - https://arxiv.org/pdf/2306.08543》. 


----

## 《miniLLM》

miniLLM: 一种蒸馏方法, 通过 RL 来拟合 teacher 和 student 的生成分布的 reverse-KL. 

### 为啥用 reverse-KL

rev-kl 还是 fwd-kl, 本质就是用student做sample(rev) 还是用 teacher(fwd).
- D_KL(P || Q) = Σᵢ P(i) log(P(i) / Q(i))
- fwd-kl = D_KL( teacher || student)

|                                         | 在老师 / 固定数据的前缀上 | 在学生生成的前缀上         |
|-----------------------------------------|-----------------------|-------------------------|
| forward KL（每个位置算 Σ_v p · log(p/q)） | 传统蒸馏                | on-policy 的 forward KL |
| reverse KL（每个位置算 Σ_v q · log(q/p)） | 较少见                  | MiniLLM、OPD            |

note: 本文对比的是如上表格的传统蒸馏(上面: "前缀"指的是提问 prompt 加上 response 里已经写出来的前 t−1 个 token)

fwd-kl: 需遍历 teacher 的各种采样(或者说各种 mode), 而学生容量有限，学不会老师分布的全部；于是 forward KL 会逼学生把概率分到老师认为不该出现的地方，reverse KL 则让学生只集中在老师的主要模式上(看下图, fwd/rev 都没能完美学会teacher, 好歹 rev 学到了重点, 而 fwd 啥都没学会):

<img width="872" height="626" alt="image" src="https://github.com/user-attachments/assets/a7904485-a919-4db9-9c0a-a62916e3a4c7" />

### how to

如下图可看到: 和普通的 ML 倒是更像, 和 RL 好像也没多大关系——只是当场 sample data, 这很 RL; 另外, long term 是 "reward × ∇log p" 形式的, 并且 PPO 那样的 clip 一边稳定训练, 这个也很 RL. 

它标榜 RL, 其实并不是最典型的 RL: reward 甚至含有被优化的参数. 它的loss 拆成了 long term+singler term+llm loss 三部分(前两部分看下文).

<img width="2082" height="1132" alt="image" src="https://github.com/user-attachments/assets/650cddca-4aef-42e9-abb6-1b2edf22e3cf" />

### 原理详细解释

<img width="2462" height="1804" alt="image" src="https://github.com/user-attachments/assets/5c99a9f1-7184-4968-aaec-d4d20cd30da6" />

上图公式编号同其 paper中编号(每个公式有所调整). 

是现有loss 然后看怎么用 RL 解. 然后通过形变, 强行构造了一个 reward = Rₜ = log p/q_θ . 而且注意reward 居然含有和策略中的参数θ. 这不算是典型的 RL 了. anyway, 对这个 loss 求导, 可以得到(2). 

然后对(2), 可以拆分成long、short 两项:
- short_term: 对一个已知的prompt 前缀, 所有下一个 token 所带来的reward
- long_term: 对一个已知的prompt 前缀, 所有补全tokens 带来的reward(当然这里指的是下下 token 开始所有 tokens 的 reward 之和)
- 这样对于一个prompt 前缀的补全的reward = short+long

**(1) => (2): 直接算就可以了**

```
∇_θ L = -∇_θ [ E_{q_θ} log(p/q_θ) ]
      = -∇_θ [ ∑ (q_θ · log(p/q_θ)) ]                 #  E_{q_θ} = ∑ q_θ
      = -∑ [ q_θ′ · log(p/q_θ) + q_θ · (−q_θ′/q_θ) ]  # (ab)' = a'b+ab'
      = -∑ [q_θ′ · (log(p/q_θ) − 1) ]
      = -∑ [q_θ′ · (Rₜ − 1) ]                          # Rₜ := log p/q_θ
      = -E_q [(Rₜ − 1)·∇_θ(log q_θ)]                   # q′ = q · ∇log q.  证明了 (2)
      = -E_q [(rₜ + Rₜ₊₁ − 1)·∇_θ(log q_θ)]            # 注意 Rₜ 是 trajectory 的 reward 和: 每新生成一个 token 就有一份 reward rₜ:=log(p(yₜ)/q_θ(yₜ)), Rₜ = ∑ᵢrᵢ = rₜ+Rₜ₊₁.
      = -E_q (Rₜ₊₁ · ∇_θ(log q_θ)) - E_q[(rₜ−1)·∇_θ(log q_θ)]
      = long_term - E_q[(rₜ−1)·∇_θ(log q_θ)].         # long + short term 分解
```

**(2) => (3): 拆分 ∇_θ L = long_term + short_term**

重点是short_term的变形 $E_{p,q_θ} ∑ₜ [(rₜ−1)·∇_θ(log q_θ)] = E_{p,q_θ} ∑ₜ ∇ E_{q_θ} rₜ$. 详看下面: 
- (26) => (27): 其实就是逆用 (1)=>(2)
- (25) => (26): 注意形式上就是 25 的 ∑ₜ 之后强行插入了 $E_{y_t} ..$, 看起来有问题, 为啥能等式成立!
  - 注意 25/26 中: ∑ₜ 后的 yₜ 是不同的:
    - 25 里的 yₜ 来自 trajectory $y~q_θ$, 是 fixed (trajectory_sample --> y -> y[t] == yₜ)
    - 26 中的 yₜ 来自 trajector $y~q_θ$ 的前缀 y[:t] 的 next token sample (trajectory_sample --> y -> y[:t] --token_sample--> yₜ).
  - 为什么 25 => 26 等式成立? 为简化, 假设针对同一个prompt x, 于是下面省略x:
    - 25 式里: $E_y ∑ᵀₜ₌₁ [log(p(yₜ|y[:t])/q_θ(yₜ|y[:t]))⋅∇log(q_θ(yₜ|y[:t]))] = E_y ∑ᵀₜ₌₁ [rₜ⋅∇log(q_θ(yₜ|y[:t]))] == E_y ∑ₜ₌₁ Fₜ(y[:t])$, 令Fₜ:=rₜ⋅∇log(q_θ). 总之是先遍历 trajectory, 然后对单个 trajectory 求和——所得到的是 trajectory 的均值. 这也可以重新组合: 先遍历不同的 y 前缀, 然后不同长度的 y前缀 y[:t] 作全词表的next-token 遍历. 这样, 也是遍历到了所有的 trajectory 的. 这正是 (26) 式子的事.
      - 为啥两个遍历结果一样:
        - 25: E_y ∑ₜ₌₁ Fₜ(y[:t]), 遍历为: `a₁b₁c₁d₁..=>[a₁, a₁-b₁, a₁-b₁-c₁,..], ..., a₂b₂c₂d₂..=>[a₂, a₂-b₂, a₂-b₂-c₂, ...], ...`
          - 乃同一 trajectory 序列, 逐步 head 截取.
          - 遍历时, 不同 trajectory 不交叉.
        - 26: E_y ∑ₜ₌₁ E_{yₜ} Fₜ(y[:t]), 遍历为: `a{b₁, b₂, ..., bₙ}=[a-b₁, a-b₂, ..., a-bₙ],  ab{c₁, c₂, ..., cₙ}=[a-b-c₁, a-b-c₂, ..., a-b-cₙ], abc{d₁, d₂, ..., dₙ}=[a-b-c-d₁, a-b-c-d₂, ..., a-b-c-dₙ], ...`
          - 同一个 trajectory, 截取 head 之后, 遍历下一个token, 所得到的 [head, next_token], 是来自另一个 trajectory 的.
          - 遍历时, 不同 trajectory 出现交叉.
        - 上面都是不多不少一次遍历, 且对每个遍历, 参与求和的都是 Fₜ(y[:t] = rₜ⋅∇log(q_θ(yₜ|y[:t])), 所以 25=>26 成立

<img width="2290" height="874" alt="image" src="https://github.com/user-attachments/assets/8d2d6b1e-3316-4de8-a04d-6738405faab3" />

**(3) => (4): sample mix** (现在多不用它了)
- 为啥引入 sample mix: 防止奖励作弊（reward hacking）
  > "We observe reward hacking when training with Eq. 2 because q_θ sometimes produces degenerated sentences y that receive high scores from the teacher (e.g., repeated phrases) during sampling, especially for small student models". student 比较弱, 于是出现重复输出等问题, teacher 仍然给高分——而teacher 一般不会有这问题. 所以要merge teacher 的一些能力.
- 为啥引入 wₜ: 既然sample 分布被改写, 于是需要重要性采样把这个分布差异给掰回来

后来者, OPD（MOPD、Kimi 等）都没用它. 大概是, student 和 teacher 都是比较强的同大小的 model, 没必要让 teacher 做引导.

**(5) => (6): 引入长度normalization: 去掉长度依赖**

Rₜ₊₁ = ∑ᵀₜ₊₁ rₜ, 正好是 T-t-1 项, 于是除以T-t-1, 得到 normalized Rₜ₊₁ = 1/(T-t-1) ∑ᵀₜ₊₁ rₜ. 这个被除的是当前位置t到尾巴的长度, 而不是 |y|.
- 背景是作者发现 “long sequences tend to have small Rₜ₊₁, which encourages the model to produce short responses”. normalization 在于去除长度依赖, 所以其实不只是解决 long seq 导致 Rₜ₊₁ 更大更小.
  - 关于“long seq 导致 Rₜ₊₁ 小”:
    - 首先注意往往 Rₜ = log p(y|x) /q_θ(y|x) < 0, 因为: (1) 直觉上: teacher 往往不太同意student 采样的y, 所以 p(y) < q(y), log(<1) <0 (2): 数学上: E[ log(p/q) ] = −KL(q ‖ p) ≤ 0, 也就是 log(p/q) 均值 <=0
    -  不做 normalization 则 R(长) < R(短)，所以模型偏向写短; 要纠正，就得让长续写的 R 往上提；R 是负数，乘以一个小于 1 的系数推大 R(long)；于是用系数 1/(T-t-1) < 1, 对一个y, 越关注它的尾部，系数 1/(T−t−1) 越小，往上提得越多

----

## 回到 MOPD

