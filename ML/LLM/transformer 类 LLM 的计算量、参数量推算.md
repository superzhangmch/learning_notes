假设都是标准 transformer：共有 l 层 transformer block，hidden dim = d， FFN 升维因子是 4.

## 参数（不算 emb 等）：
1. FFN：d->4d, 4d->d, 共 $8d^2$ 个
2. ATTN: QKV投影(d 维的 hidden state 变出 d 维的QKV)，以及 attn 后的 d->d 映射，一共是 $4d^2$
3. 这样最终参数量是： $12ld^2$

## 计算量

**小知识**：
- 矩阵乘法的基本计算量：
  - C = A * B， A.shape =[m, k], B.shape = [k, n]
  - 则计算量（FLOPs）是 $2 \times m \times n \times k$（乘法和加法各计1次操作）
  
### 对每个 token (不看attn)
1. FFN：
   - d->4d: 矩阵运算 [1, d]x[d, 4d]->[1,4d], 计算量 $8d^2$
   - 4d->d：矩阵运算 [1, 4d]x[4d, d]->[1,d], 计算量 $8d^2$
   - 共 $16d^2$ 次
2. ATTN 投影:
   - QKV 投影(d 维的 hidden state 变出 d 维的QKV):
     - Q: 矩阵运算 [1, d]x[d,d]->[1,d], 计算量 $2d^2$
     - QKV 总共： $6d^2$
   - attn 后的 d->d 投影: 矩阵运算 [1, d]x[d,d] -> [1,d]，计算量 $2d^2$
   - 
   - 以上 $8d^2$

乘上层数 l 后，以上最终是 $16ld^2+8ld^2=24ld^2$，数值上正好是参数量的 2 倍。

### attn 操作: train / prefill
不考虑 projection 操作：
- 先分成 $n_h$ 个 heads, 每个 head 是 $d/n_h = d_h$ 维的
- 每头分别算出 $[N_q, d_h] \cdot [d_h, N_{kv}] \rightarrow [N_q, N_{kv}]$ 的 attn weight matrix。
  - 每头计算量(注意 $N_q = N_{kv}$)： $2 N d_h N$，总： $2n_h d_h N^2= 2dN^2$
- 然后对 V 根据 attn weight 做加权和(不考虑 softmax）： $[N_q, N_{kv}] \cdot [N_{kv}, d_h]\rightarrow [N_q, d_h]$。
  - 每 head 计算量： $2NNd_h$，总： $2n_h d_h N^2= 2dN^2$
- 以上是 $4dN^2$，算上层数l后是 $4ldN^2$

### attn 操作：one step inference
同上，只是 $N_q = 1$，故把它代入即可。
- 先分成 $n_h$ 个 heads, 每个 head 是 $d/n_h = d_h$ 维的
- 每头分别算出 $[N_q, d_h] \cdot [d_h, N_{kv}] \rightarrow [N_q, N_{kv}]$ 的 attn weight matrix。
  - 每头计算量： $2 d_h N$，总： $2n_h d_h N= 2dN$
- 然后对 V 根据 attn weight 做加权和(不考虑 softmax）： $[N_q, N_{kv}] \cdot [N_{kv}, d_h]\rightarrow [N_q, d_h]$。
  - 每 head 计算量： $2Nd_h$，总： $2n_h d_h N= 2dN$
- 以上是 $4dN$，表示生成第 N 个 token 时的计算量。算层数l后是 $4ldN$

-
- 这样新生成一个 token 的总计算量是 $24ld^2+4ldN=4ld(6d+N)$，当生成长度超过 6d 后，attention 计算就要占据主要部分了。按一般hidden size 在 5000~10000 这个范围算，则 60k 长度后，attn 部分计算在总计算中占比就很高了。

## other

### 关于 inference 的 batch prefilling
对 tokens 数是 N 的 prompt，可以一次性用 batch prefilling 方式，也可以一个一个循环。

单看理论计算量，batch prefill 甚至比一个一个循环，计算量还要多一点点。二者计算差异只在做 attention 这一步: 
- batch prefill 方式，前面token 其实是和后面token做了 attn，只是靠 mask 矩阵使得做了乘零而已
- 而逐步展开，并不会有这多余计算。

在不算 QKV映射的 attn 这一步，时间复杂度上:
- "逐个算"是 $O \left(\sum_{i=1}^N i \right) = O \left( \frac {N(N+1)}{2} \right) \sim  O(N^2)$
- 而 batch prefill 是 $O(N^2)$。
- 两者一个量级，但是前者终究小些。

但是 batch prefill 可以并行化，实际速度要快很多。

