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

```
(1) => (2): 直接算就可以了

∇_θ L = -∇_θ [ E_{q_θ} log(p/q_θ) ]
      = -∇_θ [ ∑ (q_θ · log(p/q_θ)) ]                 #  E_{q_θ} = ∑ q_θ
      = -∑ [ q_θ′ · log(p/q_θ) + q_θ · (−q_θ′/q_θ) ]  # (ab)' = a'b+ab'
      = -∑ [q_θ′ · (log(p/q_θ) − 1) ]
      = -∑ [q_θ′ · (Rₜ − 1) ]                          # Rₜ := log p/q_θ
      = -E_q [(Rₜ − 1)·∇_θ(log q_θ)]                   # q′ = q · ∇log q.  证明了 (2)
      = -E_q [(rₜ + Rₜ₊₁ − 1)·∇_θ(log q_θ)]      # 注意 Rₜ 是 trajectory 的 reward 和: 每新生成一个 token 就有一份 reward rₜ:=log(p(yₜ)/q_θ(yₜ)), Rₜ = ∑ᵢrᵢ = rₜ+Rₜ₊₁.
      = -E_q (Rₜ₊₁ · ∇_θ(log q_θ)) - E_q[(rₜ−1)·∇_θ(log q_θ)]
      = long_term - E_q[(rₜ−1)·∇_θ(log q_θ)].   # long + short term 分解
```

(2) => (3): ∇_θ L = long_term + short_term. 重点是short_term的变形 $E_{p,q_θ} ∑ₜ [(rₜ−1)·∇_θ(log q_θ)] = E_{p,q_θ} ∑ₜ ∇ E_{q_θ} rₜ$. 详看下面: 
- (26) => (27): 其实就是逆用 (1)=>(2)
- (25) => (26): 注意形式上就是 25 的 ∑ₜ 之后强行插入了 $E_{y_t} ..$, 看起来有问题.
  - 注意 25/26 中: ∑ₜ 后的 yₜ 是不同的:
    - 25 里的 yₜ 来自 trajectory $y~q_θ$, 是 fixed (trajectory_sample --> y -> y[t] == yₜ)
    - 26 中的 yₜ 来自 trajector $y~q_θ$ 的前缀 y[:t-1] 的 next token sample (trajectory_sample --> y -> y[1:t-1] --token_sample--> yₜ).
  - 为什么 25 => 26 等式成立?
    - 25: $E_{x,y} ∑ₜ₌₁ᵀ log(p(y_t|x, y[:t-1]) / q_θ(y_t|x,y[:t-1])) == E_{x,y} log(p(y|x)/q_θ(y|x)$, 也就是等于关于不同trajector 的 log(p(y|x)/q_θ(y|x) 值的均值.

<img width="2290" height="874" alt="image" src="https://github.com/user-attachments/assets/8d2d6b1e-3316-4de8-a04d-6738405faab3" />

