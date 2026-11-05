当前(2026年) LLM post-training 的套路大约是, 先对每个领域分别用 RL 做后训练, 然后把每个独立专家蒸馏到目标model上. 但是不再用典型的那种老师给出答案与 logit 的手把手蒸馏, 而是用 OPT: 学生自己采样, 老师告诉学生在每一token最佳采样分布是怎样的.

- OPT 蒸馏发展过程中的两个重要关节点是: 2023年的 mini-LLM(它详细阐述了 loss 与 梯度怎么搞); 2026.01 的 thinkingmachines 的 blog(指出 mini-LLM 的简化版本就很有效).
- 多专家做 OPD: 小米的MiMo-V2-Flash首先引入(并总结成了 MOPD 一文), 后来 kimi-k3, deepseek-v4 都用到了该法.

----

# Multi-teacher On-Policy Distillation (MOPD)

- 《MOPD: Multi-Teacher On-Policy Distillation for Capability Integration in LLM Post-Training》 小米 https://arxiv.org/abs/2606.30406
- 《MiMo-V2-Flash Technical Report》 https://arxiv.org/pdf/2601.02780, 就用到了它

一句话说: 先SFT然后以他为基础, 不同领域分别 RL, 这样得到多个领域专家, 然后再对原来的 sft model, 把这些能力蒸馏过去.

<img width="750" alt="image" src="https://github.com/user-attachments/assets/21c830d0-c002-4dc4-9286-1b175a4df545" />

对于stage3: student 蒸馏 teachers, 是做的KL距离逼近. 这一step, 也是通过 RL 来做的. 方法来自 《MiniLLM: On-Policy Distillation of Large Language
Models - https://arxiv.org/pdf/2306.08543》. 


----

## 《miniLLM》 2023.06

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

<img width="300" alt="image" src="https://github.com/user-attachments/assets/a7904485-a919-4db9-9c0a-a62916e3a4c7" />

note: 
- MiniLLM 的目标就是把大模型压缩成小模型(名字里的 "Mini"正此意)。它的整个论证，也是建立在"学生容量有限、学不全老师的分布"这个前提上的，这正是它选择 reverse KL 的理由。
- MOPD、DeepSeek-V4、Kimi K3：老师和学生一样大，都从同一个 SFT 检查点出发，目的是合并多个专家的能力。

### how to

如下图可看到: 和普通的 ML 倒是更像, 和 RL 好像也没多大关系——只是当场 sample data, 这很 RL; 另外, long term 是 "reward × ∇log p" 形式的, 并且 PPO 那样的 clip 一边稳定训练, 这个也很 RL. 

它标榜 RL, 其实并不是最典型的 RL: reward 甚至含有被优化的参数. 它的loss 拆成了 long term+singler term+llm loss 三部分(前两部分看下文).

<img width="750" alt="image" src="https://github.com/user-attachments/assets/650cddca-4aef-42e9-abb6-1b2edf22e3cf" />

### 原理详细解释

<img width="700" alt="image" src="https://github.com/user-attachments/assets/5c99a9f1-7184-4968-aaec-d4d20cd30da6" />

上图公式编号同其 paper中编号(每个公式有所调整). 

是先有了loss(loss 是 rev-kl, 且是对整个序列做的 KL), 然后寻思怎么用 RL 解——通过形变, 强行构造了一个 reward = Rₜ = log p/q_θ . 而且注意reward 居然含有和策略中的参数θ. 这不算是典型的 RL 了. anyway, 对这个 loss 求导, 可以得到(2). 

然后对(2), 可以拆分成long、short 两项:
- short_term: 对一个已知的prompt 前缀, 所有下一个 token 所带来的reward
- long_term: 对一个已知的prompt 前缀, 所有补全tokens 带来的reward(当然这里指的是下下 token 开始所有 tokens 的 reward 之和)
- 这样对于一个prompt 前缀的补全的reward = short+long

**(1) => (2): 直接算就可以了**

```
∇_θ L = -∇_θ [ E_{q_θ(y|x)} log(p/q_θ(y|x)) ]         # 注意是针对的整个序列算的KL
      = -∇_θ [ ∑ (q_θ · log(p/q_θ)) ]                 # E_{q_θ} = ∑ q_θ
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
- (26) => (27): 其实就是逆用 (1)=>(2). 只是这里是针对的单个 token, 那里是整个y(token 序列). 概率是一个数, 差别只是input 是一个token, 还是多个, 所以推导一样.
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
    - 首先注意往往 Rₜ = log p(y|x) /q_θ(y|x) < 0, 因为: (1) 直觉上: teacher 往往不太同意student 采样的y(反之student 也不太同意teacher), 所以 p(y) < q(y), log(<1) <0 (2): 数学上: E[ log(p/q) ] = −KL(q ‖ p) ≤ 0, 也就是 log(p/q) 均值 <=0; p、q交换, 不等式仍然成立
    -  不做 normalization 则 R(长) < R(短)，所以模型偏向写短; 要纠正，就得让长续写的 R 往上提；R 是负数，乘以一个小于 1 的系数推大 R(long)；于是用系数 1/(T-t-1) < 1, 对一个y, 越关注它的尾部，系数 1/(T−t−1) 越小，往上提得越多

### 另一个角度看 single 与 long 分解

miniLLM 的 loss, 其实可以转成另一种形式: $KL(q||p) = ∑ₜ E_{y<t} KLₜ(y<t)$, 也就是先固定长度, 然后看下一个 token 的 KL. 证明如下: 

<img width="700" alt="image" src="https://github.com/user-attachments/assets/c3cfad4b-9d7a-4f8d-bbfc-6b87c115c2bc" />

然后: $∑ₜ [E_{y<t} KLₜ(y<t)] = ∑ₜ ∑_{y<t} q_θ(y<t) KLₜ(y<t)$ ⇒ $∇(∑ₜ ∑_y q⋅KLₜ) = ∑ₜ ∑_y(∇q⋅KLₜ) + ∑ₜ ∑_y(q⋅∇KLₜ) = long + single$

上面为啥 ∑ₜ ∑_y(q⋅∇KLₜ) == single, 见下文.

注意: single 项反推出的loss, 其实就是把原 loss 中 E_{y~q_θ} 的采样分布中的参数θ不求导. 所以下文说到只用 single, 就是不关心采样分布中的参数.

#### (1) single term

$∑ₜ ∑_y(q⋅∇KLₜ)$ 正是 single term. 因为 $∑ₜ ∑_y(q⋅∇KLₜ) = ∑ₜ ∑_{y<t}(q(y<t)⋅∇KLₜ) = ∑ₜ E_{y<t} ∇KLₜ = -∑ₜ E_{y<t}(∇E_{yₜ}rₜ) == -E_y ∑ₜ (∇E_{yₜ}rₜ) = single_term$, 注意 KLₜ == -E_{yₜ}rₜ

```
∑ₜ ∑_y(q⋅∇KLₜ) = ∑ₜ ∑_{y<t}(q(y<t)⋅∇KLₜ)
              =  ∑ₜ E_{y<t} ∇KLₜ         // ∑_{y<t} q(y<t) .. = E_{y<t} ..
              = -∑ₜ E_{y<t} (∇E_{yₜ}rₜ)  // KLₜ == -E_{yₜ}rₜ
              = -E_y ∑ₜ (∇E_{yₜ}rₜ)      // E、∑ₜ 交换. E_{y<t} 与 E_y 不同, 按说不能随便交换: 不同的y可能有相同的前缀y[:t]. 其实这里是可以的, 
              = single_term            //            因为每一项只看前缀，所以把共享同一前缀的那些完整序列合并起来，它们的概率加在一起，正好等
                                       //            于这个前缀本身的概率，因此遍历完整序列和遍历前缀得到的数一样.
```

注意: $∇KLₜ = Eᵥ ∇log(q)⋅log(q/p)$ => single_term= $-E_y ∑ₜ Eᵥ[∇log(q(v|y<t))⋅rₜ(v|y<t)] = -E_y ∑ₜ [∇log(q(yₜ|y<t))⋅rₜ(yₜ|y<t)]$, 而后者正是 MOPD 的梯度更新式.
- 因为: $∇KLₜ = ∑ᵥ∇q(v)⋅log[q(v|y<t)/p(v|y<t)]$ == $∑ᵥ∇q(v)⋅log(q/p)=∑ᵥq(v) ∇log(q)⋅log(q/p)$ = $Eᵥ ∇log(q)⋅log(q/p)$, 所以: single_term = $∑ₜ ∑_y(q⋅∇KLₜ) = E_y ∑ₜ ∇KLₜ$ = $E_y ∑ₜ (Eᵥ ∇log(q(v))⋅log(q(v)/p(v))$ = $-E_y ∑ₜ Eᵥ[∇log(q(v|y<t))⋅rₜ(v|y<t)]$. 注意神奇一点: 可以把 Eᵥ 去掉(背后逻辑, 和 miniLLM 一文 (25) => (26) 中的 E_yₜ 的可有可无是一个道理, 本质是不同的遍历的差异!), 而精确得到: single_term= $-E_y ∑ₜ Eᵥ[∇log(q(v|y<t))⋅rₜ(v|y<t)] = -E_y ∑ₜ [∇log(q(yₜ|y<t))⋅rₜ(yₜ|y<t)]$, 而这正是 MOPD 的梯度更新式.

#### (2) long term

∑ₜ ∑_y(∇q⋅KLₜ) 正是 long term.

先来辅助结论

**(i). $E_y [∇log(q(yₛ))⋅rₜ] = = -E_{y<t} [∇log(q(yₛ))⋅KLₜ]$**

概率上有著名的 全期望公式 / 重期望定理：E[X]=E_Y[E[X|Y]], 也就是直接算期望可以转成先算条件期望, 再对条件算期望. 于是对 s < t 有: 

```
E_y [∇log(q(yₛ))⋅rₜ] = E_{y≤t} [∇log(q(yₛ))⋅rₜ]
                     = E_{y<t} E_{yₜ}[∇log(q(yₛ))⋅rₜ]    # E[X]=E_Y[E[X|Y]]
                     = E_{y<t} [∇log(q(yₛ))⋅E_{yₜ}[rₜ]]  # s < t, 所以 ∇log(q(yₛ)) 可以提出来
                     = -E_{y<t} [∇log(q(yₛ))⋅KLₜ]        # KLₜ == -E_{yₜ}rₜ
```

或看图: 

<img width="210" alt="image" src="https://github.com/user-attachments/assets/f774c6f0-a6df-494b-8c5a-7ce04167d838" />

**(ii). $∑ₜ E_{y<t} [(∑_{s<t}∇log(q(yₛ)))⋅KLₜ] = E_y ∑ₛ [∇log(q(yₛ))⋅∑_{t>s} KLₜ]$**

证明: 令 a_{s,t} := ∇log(q(yₛ))⋅KLₜ
- 左 = ∑ₜ ∑_{s<t} [∇log(q(yₛ))⋅KLₜ]     = E_y ∑ₜ ∑_{s<t} [∇log(q(yₛ))⋅KLₜ] = E_y ∑ₜ ∑_{s<t} a_{s,t}
- 右 = E_y ∑ₛ [∇log(q(yₛ))⋅∑_{t>s} KLₜ] = E_y ∑ₛ ∑_{t>s} [∇log(q(yₛ))⋅KLₜ] = E_y ∑ₛ ∑_{t>s} a_{s,t}

因为 s,t 都是 integer, 所以上面所有差异, 其实就是对一个三角矩阵的不同求sum方式: 按行或按列, 所以自然二者相等
```
note: t > s: 
|-------------t------------
|  a₁₂, a₁₃, a₁₄,  ...,  a₁ₙ
|       a₂₃, a₂₄,  ...,  a₂ₙ
s            a₃₄,  ...,  a₃ₙ
|                  ...,
|                     a₍ₙ₋₁₎ₙ
```

**现在证明 ∑ₜ ∑_y(∇q⋅KLₜ) 正是 long term:**

```
∑ₜ ∑_y(∇q⋅KLₜ) = ∑ₜ ∑_y(q(∇q/q)⋅KLₜ)
              = ∑ₜ ∑_y(q ∇log(q)⋅KLₜ)                  # ∇q/q = ∇log(q)
              = ∑ₜ ∑_{y<t}(q(y<t) ∇log(q)⋅KLₜ)         # 稍微补全下符号
              = ∑ₜ E_{y<t} (∇log(q(y<t))⋅KLₜ)          # ∑ q = E
              = ∑ₜ E_{y<t} [(∑_{s<t}∇log(q(yₛ)))⋅KLₜ]  # ∇log(q(y<t) = ∑_{s<t} ∇log(q(yₛ))
              = E_y ∑ₛ [∇log(q(yₛ)) ⋅ ∑_{t>s} KLₜ].    # 关键一步. s< t换成 t>s. 详见下面
              = E_y ∑ₛ ∑_{t>s} [∇log(q(yₛ))⋅KLₜ]
              = ∑ₛ ∑_{t>s} E_y [∇log(q(yₛ))⋅KLₜ]
              = - ∑ₛ ∑_{t>s} E_y [∇log(q(yₛ))⋅rₜ]      # 用辅助结论(i)
              = - E_y[∑ₛ ∇log(q(yₛ))⋅∑_{t>s}rₜ]
              = - E_y[∑ₛ ∇log(q(yₛ))⋅Rₛ₊₁]             # Rₛ₊₁=∑_{t>s}rₜ
              = long term
```
或看图: 

<img width="320" alt="image" src="https://github.com/user-attachments/assets/ed4e5346-139c-497b-90a3-cc8108b4d377" />

### 总结 & 回看

下面总结了 KL loss, 以及梯度/single项 的各种形式(相关推导看上文; thinkingmachines, mopd, kimi, deepseek 都可从下面得到):

<img width="400" alt="image" src="https://github.com/user-attachments/assets/0defeb74-656b-4687-8605-8c9c86a3b881" />

一点注意: 这里列出 loss 与梯度的各种形式; 实际用到的时候, 只需要定义好loss, 怎么求梯度, 用训练框架的自动微分做的. 所以梯度形式其实只是为了说明, 它是什么样子.

----

## thinkingmachines blog: OPD 2026.01

2026.01 https://thinkingmachines.ai/blog/on-policy-distillation/ (它引用了 miniLLM) 正式开启了 OPD 后训练.

出发点：on-policy 和 off-policy 各有一半好处
- RL（on-policy）：学生从自己犯的错里学，但反馈太稀疏。不管回答多长，一条回答只有一个分数，学生不知道是哪个 token 出了问题。
  - 注意: 这里 RL（on-policy）没有老师模型，和蒸馏无关。
- SFT / 传统蒸馏（off-policy）：反馈很密集，但学生学的是老师会走到的状态，而不是自己会走到的状态。早期一步走错，后面就越错越远。作者还引用了已有研究：学生可能学到了老师的风格和语气，却没学到老师的事实准确性。
- OPD 想把两者的优点合起来：在学生自己的轨迹上，由老师逐个 token 打分。

作者用了一个下棋的比喻：
- RL 像是自己下棋，没人指导：只知道最后输赢，不知道哪几步是关键。
- 传统蒸馏: 像是看大师对局, 但那些局面你自己根本走不到。
- OPD 像是下完之后，让引擎给你的每一步打分，就像 chess.com 用颜色标出每一步棋的好坏。

rev-KL 好处:
- 不怕 reward hacking: unhackable：不怕奖励被钻空子
  - reverse KL 的最小值恰好在学生 = 老师的时候取到，KL 低就真的意味着学生的行为接近老师，目标和衡量指标之间没有缝隙可钻。
- mode-seeking：只抓老师的主要模式(miniLLM 就指出过, 比miniLLM 更早就有人指出过)
  - reverse KL 重罚"学生给了概率、老师却认为不可能"的地方，所以学生宁可只学其中一两个峰，也不会把概率摊到峰和峰之间那些老师不认可的地方。
- 减少 exposure bias：训练和推理时看到的前缀一致(前缀=question_prompt + generating_partial_response)
  - 传统训练（SFT、传统蒸馏）的前缀总是标准答案或老师写的，模型在训练时从没见过自己写出来的、可能有错的前缀。而此处训练用的前缀就是学生自己生成的, 训练和推理之间不再有这种错位。

loss
- loss：KL(π_student ‖ π_teacher) := $KL(π_θ ‖ π_T)=𝔼_{x∼π_θ} [log(π_θ(xₜ₊₁|x[:t]))/(π_T(xₜ₊₁|x[:t]))]$, 这个从 blog 直接扣取来的 loss 只算是示意性质的. 补充后应该是 $𝔼_x ∑ₜ [log(π_θ(xₜ₊₁|x<t))/(π_T(xₜ₊₁|x<t))] = 𝔼_x log(π_θ(x))/π_T(x)$, 正好是精确的 KL 定义, 和 miniLLM 是严格一样的.
- 实际loss: 从所提供的 code, 更新的梯度是:
  * 梯度 = -∑ₜ Aₜ ∇logπ_θ(yₜ); Aₜ = -reverse_kl=log π_{teacher}(yₜ)-log π_{student}(yₜ), 这说明实际用的 fwd loss, 并不是精确等于 KL. 
    * 后来的 MOPD 的梯度, 和他的形式一模一样. 那么怎么来的, 看下面 MOPD 讲解
    * 对应到 miniLLM, 其实就是miniLLM 的梯度 single 项, 也就是没看 long 项
      * 作者说: singer term 这样, 只看下一个token, 而不看更多steps, 就够了——看更多没发现收益. 另外只看下一token, 所以可以 partial rollout，不必等回答完整写完。

**具体实现:**

是可以嵌入已有的 RL 框架的, 实现只需改一行：在 RL 代码里设 advantages = -reverse_kl，配合重要性采样的 loss。
- 各家 OPD, 实际操作时, 都是 student 采样出完整的 trajector y. 如果只看一个token, 则是只看y[t]. 这时候天然和原 RL 框架兼容. 如果做 top-k 或者 全词表, 则是会对采样出的 y[:t], 看t位置的所有或topK候选, 这时候原 RL 框架就不能直接用了(deepseek-v4 选择用全 token, 毕竟方差小, 于是需要工程实现能跟上).

**局限**
- 学生必须本来就有一定概率做出老师的行为，所以前面仍然需要 mid-training 或 SFT 打底。
- mode-seeking：学生只会学到老师的一种行为，而不是老师的完整分布。

### 其他

这个 blog 在呼应 minillm 之外, 主要在于点明, 不需要考虑 mini llm 的 long 项. 只看single 项时, 对t位置, 有三种选择:
- 只看 student 的当前采样的 token
- 看该位置全词表
- 看该位置全词表的 teacher logit 的top-k

对应下图:

<img width="400" alt="image" src="https://github.com/user-attachments/assets/74d26bbc-a332-4a04-bca6-071e85bde562" />

该blob 只是尝试了第一种. 后来的 DeepSeek-V4 和 MiMo 分别试了后两点。

再次说明: 这个梯度, 只是说希望怎么更新参数. 而训练用的是自动微分, 所以fwd loss 是需要从这个目标梯度反推的. 
- 全词表来说: $loss = -E_{y~q_θ} ∑ₜ KLₜ$, 注意对于 E 的采样分布的 θ 不求梯度.
- topK 词表: $loss = E_y ∑ₜ ∑_{v ∈ topK} q log(q/p)$, 其中对于 E的采样分布的 θ 也不求梯度.
- 单 token 版: $loss = E_y ∑ₜ (sg[log(q/p)]⋅log(q))$, 其中 sg=stop_gradient, 且对于 E的采样分布的 θ 也不求梯度.

## 小米 MOPD 2026.06

MOPD 的loss 除了长度 normaliza 项外, 其实和 miniLLM 的 loss 一模一样(但是形式有转化, 见上面). 看上文, miniLLM 的loss 另一转化形式所得到的 single term, 可以完美浮现出 MOPD loss 的梯度式.

mopd 的 loss $L^{PG}_{MOPD}(𝜃)$, 是根据梯度式倒推出来的而已.

<img width="700" alt="image" src="https://github.com/user-attachments/assets/5cc8e75c-20d1-44c9-ae3b-89179f73bf02" />

### top-K

MOPD 试验了 top-k:
- 相比只看student单token, top-k 并没有带来额外的稳定性或方差降低
- kimi-k3 也试过, 结论是 "no clear advantage in either convergence speed or final performance"；

**top-K 的 loss 为啥需要调整项:**

对 loss = $E_y ∑ₜ ∑_{v ∈ topK} [q_θ log(q_θ/p)]$, 因 $[q_θ log(q_θ/p)]' = q‘(log(q/p) + 1)= q'log(q/p)+q'$, 所以 $∇loss = E_y ∑ₜ ∑_{v ∈ topK} q‘(log(q/p) + 1)$, 在 $q_θ = p$ 点, loss 不满足极小值必要条件(梯度为0; 虽然梯度为0, 也不见得最小): ∇loss = E_y ∑ₜ ∑_{v ∈ topK} q‘, 难以保证是0梯度. 这不好. 注意 loss 从 minillm 的 single 项出发的, 求导不需要对 E_y 的分布求导. 

引入 adjsut 后, $loss = E_y ∑ₜ ∑_{v ∈ topK} [q_θ log(q_θ/p) - q_θ + p]$, 则 ∇loss = $E_y ∑ₜ ∑_{v ∈ topK} [q‘(log(q/p) + 1) - q']=E_y ∑ₜ ∑_{v ∈ topK} [q‘(log(q/p)]$, 在 q_θ = p 点, ∇loss==0. 保证了优化目标处满足极小值的必要条件. 这就是为啥有 -q_θ 来调整. 至于 还有 p 从而最终调整项是 -q_θ+p, 是为了让 loss value 别大变, 毕竟 q_θ -> p时, -q_θ+p-> 0.

## deepseek-v4 2026.06 https://arxiv.org/pdf/2606.19348

不同专家的 KL 加权和: L_OPD(𝜃) = ∑︁ᴺᵢ₌₁ wᵢ· KL(𝜋_𝜃 || 𝜋_{expertᵢ}

另外, deepseek-v4 用了全词表法. 为此有专门的架构升级.
- 通用优化(无论是否全词表都可以做的):
  - 部署上的优化: 因为是有好多teacher, 一种选择时直接部署多个独立副本; 而deepseek 做法是: gpu 上排队连轴不间断做不同teacher的计算, 同时异步load 下一个teacher(实现了更少资源更大计算). 也就是: ① 老师权重放在分布式存储里按需加载，ZeRO 式分片 ② 异步加载 / 卸载，不阻塞主计算,
  - 每个样本是有自己的 teacher 归属的, 所以可以batch 内, 同一个 teacher 的sample 挨着, 这样: teacher 可以批量计算, 更高效
- 专门给全词表做的优化:
  - teacher 计算的最后一层的 hidden state 要 cache: teacher 的全词表logit 太大, 所以cache hidden state 更好. forward/backward 都需要用到teacher 的logit, 所以有必要cache. 对于单token版: teacher logit 只用于fwd 时算 advantage, 所以不需要cache
  - KL计算优化: 专用 TileLang kernel 算老师和学生 logits 之间的精确 KL：加速，并减少动态内存分配。
    - loss = -E_{y~q_θ} ∑ₜ KLₜ (其中对于 E的采样分布的θ不求梯度), 所以fwd 需要求KL

## kimi-k3

就是 MOPD 原文方法. 
