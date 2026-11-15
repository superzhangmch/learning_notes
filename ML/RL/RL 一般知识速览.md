## Value-Based vs Policy-Based

核心区别
- Value-Based:
  - 学 Q(s,a) 或 V(s)
  - 策略是隐式的: 选 Q 值最大的 action, π(s) = argmax_a Q(s,a)
- Policy-Based:
  - 直接学 π(a|s). 直接输出 action 的概率分布.
  - 不显式学 Q(s,a) / V(s)

```
Value-Based:
  给每个动作打分, 选分最高的
  "这步棋价值 8 分, 那步棋价值 3 分, 选 8 分的"

Policy-Based:
  直接告诉你概率分布
  "这步棋走 70%, 那步棋走 30%"
  不关心具体分值
```

各自的问题, 以及怎么解决:
- Value-Based: 连续动作空间难处理
  - argmax_a Q(s,a) 在连续空间无法穷举
- Policy-Based: 高方差, 样本效率低
  - Monte Carlo 采样估计梯度, 抖动大
- Actor-Critic:两者结合以便互补
  - Actor  = Policy-Based  (输出动作)
  - Critic = Value-Based   (打分, 指导 Actor)

对应算法
- Value-Based:    DQN 系列
- Policy-Based:   REINFORCE
- Actor-Critic:   A2C, PPO, DDPG, SAC ...
  - Actor-Critic 是目前的绝对主流，纯 Value-Based 或纯 Policy-Based 单独用的越来越少。

----

## Q(s, a), V(s)

V(s)
- V(s) = 从状态 s 出发, 按照当前策略 π 一直走下去, 所能获得的累计 reward 的期望
- V(s) = E[ r₀ + γr₁ + γ²r₂ + ... | s₀ = s, 按策略 π 行动 ]

Q(s, a)
- Q(s,a) = 在状态 s, 执行动作 a, 之后按策略 π 走下去的累计折扣 reward 期望
- Q(s,a) = E[ r₀ + γr₁ + γ²r₂ + ... | s₀=s, a₀=a, 之后按π ]

Q(s, a) 和 V(s) 关系
- 如果 s,a 之后的 s' 是确定的:
  - Q(s,a) = r(s,a) + γ·V(s')
- 如果 s,a 之后的 s' 不确定的（随机环境）: s' ~ P(s'|s,a)
  - $Q(s,a) = r(s,a) + γ · E_{s'}[V(s')]$
- Bellman 方程:
  - $Q(s,a) = r(s,a) + γ · E_{s'}[ V(s') ]$
  - $V(s) = E_{a}[ Q(s,a) ]$

怎么学他们: 既可以是查表法, 也可以是神经网络拟合
- 查表: 只适用于 state 空间有限且小的情况
  - V(s)    → 一张大表, 每个 s 对应一个值
  - Q(s,a)  → 一张大表, 每个 (s,a) 对应一个值
- 神经网络拟合: 适用于 state 空间巨大/连续的情况
  - V(s): 输入 s, 输出一个标量
  - Q(s,a)
    * 输入 s, 输出所有 a 的 Q 值 (离散)
    * 输入 (s,a), 输出一个标量 (连续)

鉴于 Bellman 方程, 知道 V 就能知道 Q(and vice versa), 好像不需要特别区分. 实则不然:
- 用 V(s) 求 Q(s,a):
  - 需要知道 env 模型: s,a->s'的分布不可知; 即使s,a->s'是固定映射, r(s,a)也不一定容易获得
    - 下棋例子: s,a->s'固定, 但是 r(s,a) 不一定好衡量
- 用 Q(s,a) 求 V(s):
  - V(s) = Σₐ π(a|s) · Q(s,a), 需要知道 s->a 分布. 而该分布不见得有.
    - 下棋例子: 当前局面下的next action 的分布, 并不知道

即 Bellman 方程让 V 和 Q 能互推，但互推需要额外条件（环境模型或策略）。Model-Free 场景下这些条件不一定有，所以 V 和 Q 各有各的用途，不能随意替换. 所以, 往往根据情况学习 V 或 Q:
- 只学 Q(s,a):
  - 策略是隐式存在的: π(s) = argmax_a Q(s,a)
    - 只需要遍历 a, 不需要环境模型
  - 适合 Model-Free + 离散动作, 典型算法 DQN
- 只学 V(s):
  - 策略 π(s) = argmax_a V(s') = argmax_a E_{s'} V(s'|s,a->s')
    - s,a->s' 无随机性 (规则完全已知的环境, 比如棋类游戏): 可以直接遍历 a, 看 V(s'), 只学 V 就够了
    - s,a->s' 有随机性 (Model-Free 的一般情况, 执行动作 a 之后会到哪个状态, 不知道):
      - 需要在 env 真的去执行各个 a, 且对同一个a需要多次执行, 采样到不同的 s' 需要模拟执行的比较多.

从上面看: 
- Q(s, a) 在决策使用时, 更方便容易: 对于 Q(s,a) 完全不用在 env 中模拟执行, 而 V(s) 则需要(s,a->s' 是确定性的, 除非你能靠规则推断出s', 否则需要执行一步; s,a->s' 是不确定性的, 则需要多次蒙特卡洛采样), 也就是 V(s) 用的时候麻烦
- 同一个问题的 Q(s, a) 的建模更复杂: Q 需要建模 (state, action) 空间, 而 V 只需要看 state 空间
- 对于 s,a->s' 可以提前精确确定的场合, 无意 V(s) 更好用

----

## model-free vs model-based

### (1). 区别

不是说是否只需要查表, 不需要带参数的 model. 而是关于 state+action => next_state (也就是 env 怎么反应)怎么获得: 是用 model 预估, 还是直接看 env 的直接反馈.

note: 环境模型很难学准, 需额外引入一个要训练的模型, 而很多 env 本身就很快, 所以绝大多数实践场景用 model-free. 

model-free/model-based 和"是否用复杂model"是正交的:
```
             |  Tabular(查表)   | Function Approximation(神经网络等)
Model-Free   |  Q-Learning表格  |       DQN, PPO, SAC ...
Model-Based  |       少见       |       Dreamer, MuZero ...
```

```
对比:

Model-Based:
  自己学一个函数:  (s, a) → s'
  可以不问 env, 自己"脑补"下一个状态

Model-Free:
  (s, a) → s'   这一步直接问 env 要结果
  自己完全不建这个映射
```

下棋的例子: 你落子 a (action), 棋盘变成新局面 s' (env 直接给), 你得到 r (赢/输/继续)
```
Model-Free 的算法:
  只关心  (s, a, r, s')  这个元组
  不去建模"为什么落这个子棋盘会变成这样"

Model-Based:
  试图学会围棋规则本身
  → 然后可以在脑子里模拟落子结果
  → 不用真的落子
```

env 可以是:
```
  棋盘程序       → s' 由规则给出
  物理仿真器     → s' 由物理引擎给出  (MuJoCo)
  真实机器人     → s' 由传感器读数给出
  LLM 训练       → s' 就是下一个 token 的上下文

Model-Free 对这些一视同仁:
  不管 env 内部怎么运作
  只管收集 (s, a, r, s') 然后学习
```

所以 Model-Free 本质上就是把 env 当黑盒，只消费它的输出，不试图理解它的内部机制。

### (2). model-based 怎么train

思路是两阶段: (1). 学会 env (2). 在学会的 env(不再需要真 env) paly 并 train 策略

理想的两阶段（概念上）:

```
阶段一: 学环境模型
  真实交互 → 收集数据 → 训练 f(s,a) → s'

阶段二: 在模型里训练策略
  完全不用真实 env
  用 f 脑补轨迹 → 训练策略
```

实际上通常是交替进行的

```
原因: 阶段一学到的模型不完美; 策略探索到新区域时, 模型可能失准. 所以实践中:

loop:
  用当前策略和真实 env 交互一点  ← 还是要碰真实 env
  更新环境模型 f
  在 f 里大量想象, 训练策略
  → 策略更新后又会探索新区域
  → 模型又需要更新
```

----

## on-policy vs off-policy

On/Off-Policy 的本质不是"数据新不新"，而是"**采数据的策略**和**被训练的策略**是不是同一个"。只要不是同一个，就是 Off-Policy，就需要重要性采样来修正。

```
On-Policy:
  只能用"当前这个版本的model"采集的数据
  严格来说: 采完数据立刻训练, 训练完数据作废. 因为训练后 model 变了, 数据就"过期"了

Off-Policy:
  (1) 老几个train step 的采样
  (2) 训练开始时的 base model 采的
  (3) 完全不相干的其他 model 采的
  (4) 真人/其他渠道和 env 交互的
  (5) etc
```

为什么 Off-Policy 能用这些数据: 重要性采样
```
数据是 π_old 采的, 想估计 π_new 下的期望:

E_{π_new}[r] = E_{π_old}[ π_new(a|s)/π_old(a|s) · r ]
                           └────── 重要性权重 ──────┘

只要知道两个策略的概率比, 就能修正偏差
```

但有个问题: π_old 和 π_new 差距越大, 重要性权重方差越大, 修正越不准. 所以 (3)(4) 在实践中用得少. 除非你有大量数据 且 能接受一定偏差.
