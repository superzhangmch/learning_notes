若不说明, 假设都是标准 transformer：共有 l 层 transformer block，hidden dim = d， FFN 升维因子是 4.

## 参数量：
1. FFN：d->4d, 4d->d, 共 $8d^2$ 个 （假设FFN 升维因子是4）
   - note：若 FFN 用到了 sigGLU，则 FFN 处会多用 1 个矩阵，可以选取使得计算量与参数量不变（这时候升维因子其实就由4变成了8/3)。但可能能用更大的因子，比如qianwen2
2. ATTN: QKV投影(d 维的 hidden state 变出 d 维的QKV)，以及 attn 后的 d->d 映射，一共是 $4d^2$
   - note：如果用了 GQA，则KV的参数量会相应变小
3. 词表：vocab_size * d
4. 这样最终参数量，若不算词表 emb，则是： $12ld^2$

计算脚本：
```
def calc(L, d_h, ffn_intermidiate_size=4, use_swiglu=False, gqa_compress=1, vocab_size=0):
    # gqa_compress: GQA 中一个kv head 对应多少个 q head
    # use_swiglu: FFN 中是否用swiglu激活
    # ffn_intermidiate_size: FFN 升维后的维数，或者倍数.

    assert ffn_intermidiate_size < 10 or ffn_intermidiate_size >= d_h

    intermidiate_size = d_h * ffn_intermidiate_size if ffn_intermidiate_size < 10 else ffn_intermidiate_size
    ffn_expansion_factor = intermidiate_size / d_h # FFN 升维后的倍数

    ffn = 2*ffn_expansion_factor*(d_h*d_h)
    if use_swiglu: # 若用 swiglu 激活，则FFN一共两个变换矩阵会变成三个
        ffn = 3*ffn_expansion_factor*(d_h*d_h)

    attn_proj_out = d_h*d_h
    attn_proj_q = d_h*d_h
    attn_proj_k = d_h*d_h / gqa_compress
    attn_proj_v = d_h*d_h / gqa_compress

    emb = vocab_size * d_h

    arr_all =[attn_proj_out, attn_proj_q, attn_proj_k, attn_proj_v, ffn]

    total = sum(arr_all) * L + emb
    ret = total / 10**9
    return ret

# 测试 https://arxiv.org/pdf/2407.10671  qianwen2 的 四种模型
print ("qianwen72b", calc(L=80, d_h=8192, ffn_intermidiate_size=29568, gqa_compress=64/8, use_swiglu=True, vocab_size=151646))
print ("qianwen7b", calc(L=28, d_h=3584, ffn_intermidiate_size=18944,  gqa_compress=28/4, use_swiglu=True, vocab_size=151646))
print ("qianwen1.5b", calc(L=28, d_h=1536, ffn_intermidiate_size=8960, gqa_compress=12/2, use_swiglu=True, vocab_size=151646))
print ("qianwen0.5b", calc(L=24, d_h=896, ffn_intermidiate_size=4864,  gqa_compress=14/2, use_swiglu=True, vocab_size=151646))

```
结果如下，且符合预期：
```
qianwen72b 71.454932992
qianwen7b 7.068787712
qianwen1.5b 1.543123968
qianwen0.5b 0.493701376
```

若按 $12ld^2$ 估算，则分别是 64B，4.3B，0.8B，0.23B。

注意：他们都用了 GQA 与 swiGLU, 且 FFN 升维的 intermidiate 倍数并不是 8/3 倍，而是更大 (FFN+swiglu 的8/3倍, 对应于非 swiglu 的 FFN 的 4 倍) 

![image](https://github.com/user-attachments/assets/45d15530-14dc-46a5-91bd-9efd94411474)

![image](https://github.com/user-attachments/assets/3f0a35ee-a605-4750-a845-45e57421a9e6)

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
     - KV类似，故 QKV 总共： $6d^2$
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
- 这样新生成一个 token 的总计算量是 $24ld^2+4ldN=4ld(6d+N)$，当生成长度超过 6d 后，attention 计算就要占据主要部分了。按上面 qianwen72b d=8k，则 N=48k 长度后，attn 部分计算在总计算中占比就要超一半了； 若要是 N 有百万大小（而百万长度，已经有多家在提供了），那么attn计算就是 90% 以上了。难怪要整出线性注意力之类了。

## other

### 关于 inference 的 batch prefilling：batch 比 循环计算量更高，但是因并行所以更快
对 tokens 数是 N 的 prompt，可以一次性用 batch prefilling 方式，也可以一个一个循环。

单看理论计算量，batch prefill 甚至比一个一个循环，计算量还要多一点点。二者计算差异只在做 attention 这一步: 
- batch prefill 方式，前面token 其实是和后面token做了 attn，只是靠 mask 矩阵使得做了乘零而已
- 而逐步展开，并不会有这多余计算。

在不算 QKV映射的 attn 这一步，时间复杂度上:
- "逐个算"是 $O \left(\sum_{i=1}^N i \right) = O \left( \frac {N(N+1)}{2} \right) \sim  O(N^2)$
- 而 batch prefill 是 $O(N^2)$。
- 两者一个量级，但是前者终究小些。

但是 batch prefill 可以并行化，实际速度要快很多。

