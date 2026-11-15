## model-free vs model-based

### (1). 区别

不是说是否只需要查表, 不需要带参数的 model. 而是关于 state+action => next_state怎么获得: 是用 model 预估, 还是直接看 env 的直接反馈.

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
