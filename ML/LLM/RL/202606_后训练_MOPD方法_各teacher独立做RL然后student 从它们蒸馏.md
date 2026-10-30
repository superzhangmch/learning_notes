# Multi-teacher On-Policy Distillation (MOPD)

- 《MOPD: Multi-Teacher On-Policy Distillation for Capability Integration in LLM Post-Training》 小米 https://arxiv.org/abs/2606.30406
- 《MiMo-V2-Flash Technical Report》 https://arxiv.org/pdf/2601.02780, 就用到了它

一句话说: 先SFT然后以他为基础, 不同领域分别 RL, 这样得到多个领域专家, 然后再对原来的 sft model, 把这些能力蒸馏过去.

<img width="2020" height="1160" alt="image" src="https://github.com/user-attachments/assets/21c830d0-c002-4dc4-9286-1b175a4df545" />

对于stage3: student 蒸馏 teachers, 是做的KL距离逼近. 这一step, 也是通过 RL 来做的. 方法来自 《MiniLLM: On-Policy Distillation of Large Language
Models - https://arxiv.org/pdf/2306.08543》.


----

### 《miniLLM》

通过 RL 来拟合 reverse-KL, 以便做蒸馏, 来自 miniLLM 一文. 

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

**(5) => (6): 引入长度normalization: 消除"越短越占便宜"的偏差**

> long sequences tend to have small Rₜ₊₁, which encourages the model to produce short responses

注意:  
