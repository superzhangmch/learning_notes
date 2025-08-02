MOR：《Mixture-of-Recursions: Learning Dynamic Recursive Depths for Adaptive Token-Level Computation》 https://arxiv.org/pdf/2507.10524

<img width="1584" height="954" alt="image" src="https://github.com/user-attachments/assets/718ff2a4-776e-4c6e-8eec-31849b364b56" />

如图，model 结构为：第一层，最后一层不走循环，其他中间层分成多个 block，每个 block 循环 N 次——每个 token 根据 router 的决定，走其中的前几个。

### 循环模式选择

这样的循环安排，有几种选择：
- 每个block一模一样（Cycle）：emb -> **(1,2,3) -> (1,2,3) -> ... -> (1, 2, 3）**-> softmax
- block 内每层一模一样（Sequence）：emb -> **(1,1,1) -> (2,2,2) -> ... -> (N, N, N)** -> softmax
- 有非循环层：
  - 每个block一模一样（Middle-Cycle）：emb -> **L0** -> (1,2,3) -> (1,2,3) -> ... -> (1, 2, 3）-> **L_last** -> softmax
  - block 内每层一模一样（Middle-Sequence）：emb -> **L0** -> (1,1,1) -> (2,2,2) -> ... -> (N, N, N) -> **L_last** -> softmax

| 类型                  | 示例结构                                                              |
| ------------------- | ----------------------------------------------------------------- |
| **Cycle**           | `emb → (1,2,3) → (1,2,3) → ... → (1,2,3) → softmax`               |
| **Sequence**        | `emb → (1,1,1) → (2,2,2) → ... → (N,N,N) → softmax`               |
| **Middle-Cycle**    | `emb → L0 → (1,2,3) → (1,2,3) → ... → (1,2,3) → L_last → softmax` |
| **Middle-Sequence** | `emb → L0 → (1,1,1) → (2,2,2) → ... → (N,N,N) → L_last → softmax` |

paper 中优选 Middle-Cycle。

### router 选择

而 router，有两种方式（如下图）：

**（1）、Expert-choice routing** （paper 推荐这种的）

每一次循环前判断序列中有几个token 可以进入循环 ，若一个token已经被阻断，则不进入下一 loop。
- training 时：所有token并行训练，并靠 attn 三角 mask保证数据不沿时间泄露，而该 routing 方法其实做不到，也就是有数据泄露：按说应该是对 $\{seq[0: i]\}_i$ 中的每个都独立作选重要tokens，但每个选出的没法自然融合。这种泄露需要特殊处理。
- inference 时：假设已经在生成第 n 个 token，每个 loop 仍然要对包括当前token的前 n-1 个重新选 top-k，看当前token是否包括进去（从而决定是否参与 loop 计算）。
  - route 怎么知道一个token重要度，又没标注：靠联合loss建模，model 自动学出来，就像 MOE 的专家路由。

**（2）、Token-choice routing**

每个token独立判断循环走几步。每一个token都独立，则train、inference时很自然进行就行。不过训练时有计算量的负载均衡问题。

<img width="1818" height="1192" alt="image" src="https://github.com/user-attachments/assets/0f884985-e832-4e2f-a589-ac0e4c80ed31" />

### attention kv-cache 选择

既然在每一个 time step，token 未必计算所有 transformer layers，那么当前 token 计算 attn 时，每层怎么和前面的 kv-list（每层都有漏缺）作attention呢？ paper 也给出两种方式：

- Recursion-wise KV caching：每个 token 的 没计算的 loop cache，计算attn时跳过它。
  - 这样计算量要小。
- Recursive KV sharing：只 cache 每个 token 的 loop-1 的 kv 进 kv-cache
  - 这样cache 的 kv 要小，但是 attn 计算量和原生 transformer 比，保持一样。

paper 倾向于 Recursion-wise Caching。

<img width="1318" height="762" alt="image" src="https://github.com/user-attachments/assets/755174f6-cc72-46ba-8600-58407854d6d9" />

----

### 两种路由方式对比：

|    | Expert-choice  | Token-choice |
| ------ | ------------ | --------- |
| 好处    | 没负载均衡问题 | 不泄露     |
| 缺点    | 因果泄露      | 负载不均衡  |
| 怎么解决 | Aux Rout, Aux Loss | Balance Loss, Loss-free |

### 两种 kv-cache 方法对比：

下表的符号含义：
- N = loop_cnt
- N_ctx= seq_len
- k = token 的被选中次数
- k/N_ctx=token 选中率。

下表表示不同方法与"传统 transformer 的 attention"的比较比率：

|                 | **Recursion-wise Caching** | **Recursive Sharing** |
| --------------- | -------------------------- | --------------------- |
| **KV Memory**   | a = (N + 1)/(2N)     | d = 1/N           |
| **KV Cache IO** | b = (N + 1)/(2N)     | e = 1                 |
| **Attn FLOPs**  | c = $k^2/N^2_{ctx}$ < 1    | f = $k/N_{ctx}$ < 1   |

- FLOPs c: 当前token的 q 只计算 k/N_ctx(其余跳过）, 只和 k/N_ctx 的 kv 作 attn，所以为 c= $(k/N_{ctx})^2$。
- FLOPs f: 当前token的 q 只计算 k/N_ctx, 但和全长度的 kv 作 attn，所以为 f= $k/N_{ctx}\cdot 1=k/N_{ctx}$。
- a、b：loop次数为 N, loop-1必定执行，往下走，留存需计算的token越来越少。于是假设是均匀减少的，直到最后一个 loop，剩下 1/N, 也就是逐层留存需计算的token（以及相应的kv-mem占用与 kv-IO）为：1=N/N, (N-1)/N, (N-2)/N, ..., 2/N, 1/N，累加得到 $\sum_i i/N = N(N+1) / 2$, 而原始 transformer 相应数字是 N，从而比率为 $\frac {N(N+1) / 2} N = (N + 1)/(2N)$
- d：多个 loop，只存loop-1，所以为 1/N
- e=1: Recursive Sharing省显存，不省计算保持不变，所以为 1
