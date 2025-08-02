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
- Expert-choice routing：每一次循环前判断序列中有几个token 可以进入循环 （paper 推荐这种的）
- Token-choice routing：每个token独立判断循环走几步

<img width="1818" height="1192" alt="image" src="https://github.com/user-attachments/assets/0f884985-e832-4e2f-a589-ac0e4c80ed31" />

### attention 选择

既然在每一个 time step，token 未必计算所有 transformer layers，那么当前 token 计算 attn 时，每层怎么和前面的 kv-list（每层都有漏缺）作attention呢？ paper 也给出两种方式：

