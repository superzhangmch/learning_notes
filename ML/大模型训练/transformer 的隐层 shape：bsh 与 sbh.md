# transformer 的隐层 shape 用 [B,S,H] 还是 [S,B,H] layout, 啥区别

令 B=batch_size， S=sequence_len, H=hidden_dim, transformer 的 hidden shape，可以有两种选法：[B,S,H] (batch first) 或 [S,B,H] (sequence first)。

对于 transformer 来说：
- 只有 softmax(QK')V' 这一步真正涉及序列操作，从而 [B,S,H]、[S,B,H] 有区别。
- 其他地方，包括 attn 的 projection、FNN、layerNorm 等，[B,S,H]、[S,B,H] 没区别：它们都是 token 粒度计算的，本质上 batch_size=B*S。 

先记下结论：无论用哪种，当前（2025.08.17) transformer 计算 attn 时，**都是用的 [B,S,H]**, 形式，如果不是，则先转成。

RNN 时代都是 [S, B, H] 形式的（RNN/LSTM/GRU 模块）。transformer 时代，两者都有用，主流是 [B,S,H]，而 megatron 是用的 [S,B,H] （但内部 attn 会转成 [B, S, H]）。

----

下面一探下。 注意因为是 multi heads, 所以 H 会拆成多头，从而实际是 [B, S, n, h] 或 [S, B, n, h]。

### （1）、torch.nn.MultiheadAttention: 最终用 [B, S, H]

它默认把 input 当 batch_first=False （[S, B, H] 处理。看代码，如果不是，也会先转成 [S,B,H]。但是到了真正做 MHA 的时候，还是会转 [B,S,H]）:

<img width="1368" height="600" alt="image" src="https://github.com/user-attachments/assets/233f5a9a-b626-453d-8032-f3b58c4ea689" />

它所以这样，是历史传统继承。transformer 也是序列模型，它是在接口层面，继承了 RNN 时候的惯例而已。

### （2）、flashAttention：用 [B, S, H]

flashAttention 是 batch first 的。


### （3）、megatron： attn 用 [B, S, H]

megatron 在其他地方都用的 [S, B, H], 但是 attn 最核心处，仍然用的 [B, S, H] 形式。至于原因，见下文分析。

<img width="1250" height="1134" alt="image" src="https://github.com/user-attachments/assets/ea0e0cd2-cd2b-497b-871d-411b0177c175" />

注意用了： torch.bmm/torch.baddbmm

----

### 关于 megatron

megatron 第二篇 [《Efficient Large-Scale Language Model Training on GPU Clusters Using Megatron-LM》](https://arxiv.org/pdf/2104.04473) 4.2 节（计算优化一节）说：
> we changed the data layout in the transformer layer to avoid memory-intensive transpose operations, and to enable the use of strided batched GEMM kernels. Specifically, we changed the data layout from [𝑏, 𝑠, 𝑎, ℎ] to [𝑠, 𝑏, 𝑎, ℎ], where 𝑏, 𝑠, 𝑎, and ℎ are batch, sequence, attention-head, and hidden-size dimensions, respectively

也就是说为了使用 strided batched GEMM 乘法（它要求 [𝑠, 𝑏, 𝑎, ℎ] 的输入），特意从 [B, S, H] 转到了 [S, B, H]。若不转，则使用 strided batched GEMM 会有高昂的 transpose 成本（注意，非不得已，底层的实现不用做物理上的 transpose，那么这里指的是物理transpose）。从此 megatron 变成了 sequence first 的。

但是正如上面所示，megatron 后来版本的 attention 计算，并没用 sequence first 方式【代码库中也没搜到 strided batched GEMM有关东西。 strided-batched-gemm 没有 torch 直接函数，有个 cublas 的实现 cublasGemmStridedBatchedEx】。而是用了 batch first 的  torch.bmm/torch.baddbmm。

那么：
- 是 megatron 研发人员后来发现还是 batch_first 更好，但是限于惯性不好改了，于是整体用 [B, S, H], 而在 attn 时临时 seq-first 一下吗?
- 还是说上面呈现的 batch_first 的 torch.bmm/torch.baddbmm 内部，它又要给再转成物理连续的 seq-first（而原生[S, B, H] 在此处转的时候无成本吗）？

----

### 矩阵乘法的补充知识

**（1）torch.bmm：**

atch Matrix Multiply，直接做批量矩阵乘法
```
A.shape = [Batch, M, K]
B.shape = [Batch, K, N]
output.shape = bmm(a,b).shape = [batch, M, N]
output = [A[i] × B[i] for i in range(batch)]
```

note：

- torch.dot → 只能 1D 向量点积。也就是只能两个向量（batchsize=1）， 若要 batchsize > 1, torch 中需要组合多算子来实现。
- torch.mm → 只能 2D 矩阵乘。也就是两个矩阵乘法，或者说 batchsize=1
- torch.bmm → 只能 3D 批量矩阵乘。batchsize > 1 时的矩阵乘法

**（2）torch.baddbmm：**

Batch Add + Matrix Multiply，在矩阵乘的基础上，还能把已有的矩阵结果加进去（带 alpha/beta 系数）。只是 torch.bmm 的一个拓展。
```
A.shape = [Batch, M, K]
B.shape = [Batch, K, N]
C.shape = [Batch, M, N] 为已有结果
output = [βC[i] + α(A[i] × B[i]) for i in range(batch)]
output.shape = torch.baddbmm(C, A, B).shape = [Batch, M, N]
```

**（3）strided batched GEMM：**

前面两个都好理解。strided batched GEMM 是这样的矩阵乘法：
```
A.shape = [M, Batch, K] 连续存储
B.shape = [N, Batch, K] 连续存储
output.shape = bmm(A,B').shape = [M, batch, N]
output = [A[:,i,:] × B'[:,i,:] for i in range(batch)].trans_shape_to([M, batch, N])
```

**（4）什么时候 tensor 的 reshape/transpose/permutate等操作会导致物理内存 copy**

举几个 MHA 中的例子：

```
# 假设输入
batch, seq, hid, num_heads = 2, 5, 16, 4
head_dim = hid // num_heads
q = torch.randn(batch, seq, hid)             # [batch, seq, hid], contiguous

q = q.transpose(0, 1)                        # [seq, batch, hid], zero-copy (stride 改变)
# 变成了 [seq, batch, hid]

q = q.reshape(seq, batch, num_heads, head_dim)  # [seq, batch, num_heads, head_dim], zero-copy
q = q.reshape(seq, batch * num_heads, head_dim) # [seq, batch*num_heads, head_dim], ⚠️ copy
q = q.reshape(batch * num_heads, seq, head_dim) # [batch*num_heads, seq, head_dim], zero-copy
```

```
batch, seq, hid, num_heads = 2, 5, 16, 4
head_dim = hid // num_heads
q = torch.randn(batch, seq, hid)             # [batch, seq, hid], contiguous

q = q.view(batch, seq, num_heads, head_dim)  # [batch, seq, num_heads, head_dim], zero-copy
q = q.permute(0, 2, 1, 3)                    # [batch, num_heads, seq, head_dim], zero-copy (stride 改变)
q = q.reshape(batch * num_heads, seq, head_dim) # [batch*num_heads, seq, head_dim], ⚠️ copy
```
