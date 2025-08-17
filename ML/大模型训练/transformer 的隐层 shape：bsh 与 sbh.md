# transformer 的隐层 shape 用 [B,S,H] 还是 [S,B,H] layout, 啥区别

megatron 第二篇 [《Efficient Large-Scale Language Model Training on GPU Clusters Using Megatron-LM》](https://arxiv.org/pdf/2104.04473) 4.2 节（计算优化一节）说：
> we changed the data layout in the transformer layer to avoid memory-intensive transpose operations, and to enable the use of strided batched GEMM kernels. Specifically, we changed the data layout from [𝑏, 𝑠, 𝑎, ℎ] to [𝑠, 𝑏, 𝑎, ℎ], where 𝑏, 𝑠, 𝑎, and ℎ are batch, sequence, attention-head, and hidden-size dimensions, respectively

也就是说为了使用 strided batched GEMM 乘法（它要求 [𝑠, 𝑏, 𝑎, ℎ] 的输入），特意从 [B, S, H] 转到了 [S, B, H]。若不转，则使用 strided batched GEMM 会有高昂的 transpose 成本（注意，非不得已，底层的实现不用做物理上的 transpose，那么这里指的是物理transpose）。从此 megatron 变成了 sequence first 的。

这一段深表困惑。特研究下。

----

令 B=batch_size， S=sequence_len, H=hidden_dim, transformer 的 hidden shape，可以有两种选法：[B,S,H] (batch first) 或 [S,B,H] (sequence first)。

对于 transformer 来说：
- 只有 softmax(QK')V' 这一步真正涉及序列操作，从而 [B,S,H]、[S,B,H] 有区别。
- 其他地方，包括 attn 的 projection、FNN、layerNorm 等，[B,S,H]、[S,B,H] 没区别：它们都是 token 粒度计算的，本质上 batch_size=B*S。 

RNN 时代 hidden 都是 [S, B, H] 形式的（RNN/LSTM/GRU 模块）。transformer 时代，两者都有用，主流是 [B,S,H]，而 megatron 是用的 [S,B,H] （但内部 attn 会转成 [B, S, H]）。但无论用哪种，当前（2025.08.17) transformer 计算 attn 时，**都是用的 [B,S,H]**, 形式，如果不是，则先转成。如实则 megatron 做法看起来和它说的相反（下文讲这种矛盾).

----

下面一探具体代码层都是怎么处理的。

将会看到计算 attn 时，都会变成 [batch*num_head, seq, head_dim], 即 batch first【注意因为是 multi heads, 所以 H 会拆成 num_head 与 head_dim, 且把 head_dim*batch 作为新的大batch】：

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

按开头所述，megatron 说因为..., 所以要用 seq first。这和现在所见的实际 megatron 代码不一致。

那么：
- 是 megatron 研发人员后来发现还是 batch_first 更好，但是限于惯性不好改了，于是整体用 [S, B, H], 而在 attn 时临时 batch_first 一下吗? 
- 还是说上面代码中呈现的 batch_first, 背后其实就是（或者说"也"是）它 paper 说的情形？

综合看，指的是后者。

----

### 矩阵乘法的一些知识

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

前面两个都好理解。strided batched GEMM 是还可以一次处理这样的矩阵乘法：
```
A.shape = [M, Batch, K] 连续存储
B.shape = [N, Batch, K] 连续存储
output.shape = bmm(A,B').shape = [M, batch, N]
output = [A[:,i,:] × B'[:,i,:] for i in range(batch)].trans_shape_to([M, batch, N])
```

它没有 torch 的直接接口，但是 torch.bmm 内部会按需调用它。

对它，没深入研究。

### 矩阵转置等变换

**一、什么是矩阵的访问的 strides：**

一个矩阵 $A.shape = \[a, b, c, d\]$, 假如是连续的:

则访问它的 $A\[i,j,k,l\]$ 元素的时候，是通过 strides 完成的。它的

$$strides = \[bcd, cd, d, 1\]$$

为了计算 $A\[i,j,k,l\] = data\[offset\]$, 只需决定 offset

$$\text{offset} = i \times (bcd) + j\times(cd) + k \times d + l$$

**二、各种矩阵转置交换操作怎么做的：**

**a) permute：**

改变维度的顺序，本质上是重新安排 strides 的对应关系，不做拷贝。`transpose` 交换两个维度, 乃 `permute` 的特例。

比如 `permute(0,2,1,3)` → `[a,c,b,d]`。新 strides 就是把原来的 `strides = [bcd, cd, d, 1]` 按 permute(0,2,1,3) 作重排，从而得到新 `strides = [bcd, d, cd, 1]`。

offset 更新公式对应换维： $\text{offset}(i,j,k,l) = i \times bcd + j \times d + k \times cd + l$

**b) reshape:**

尝试用原 strides 重新解释数据的形状。如果新形状与原内存布局兼容, 则零拷贝；否则 PyTorch 会做一次拷贝生成连续的新张量。

比如 `[a,b,c,d] → [a, b, cd]`。原 strides = `[bcd, cd, d, 1]`，合并 c,d → 新 strides = `[bcd, cd, 1]`。

offset 计算公式为： $\text{offset}(i,j,k) = i \times bcd + j \times cd + k$

不兼容的情况：比如 `transpose` 后再 `reshape`，会导致重新分配内存。比如下面：

起点是 `shape=[a,b,c,d]`, `shape = [bcd, cd, d, 1]`。第一步：`transpose(0,1)`，得到 `shape =[b,a,c,d]`, `strides=[cd, bcd, d, 1]`，此时张量非连续（但用起来仿佛连续）。第二步：尝试 `reshape` 合并中间两维成 `shape = [b, ac, d]`。

但是合并两维要满足 stride 相容条件：

$$
\text{stride}(\text{要合并的前一维}) = \text{size}(\text{要合并的后一维}) \times \text{stride}(\text{要合并的后一维})
$$

代入发现是：

$$
bcd \stackrel{?}{=} c \times d
$$

条件不成立。所以 `(a,c)` 这两维在物理内存中并不紧邻，无法零拷贝合并。所以这时候会触发 **拷贝**，生成新的连续张量。

**c) 总结：**
- permute/transpose：不会拷贝数据，只是重排 strides；offset 公式 = **新下标 × 对应的新 stride**。
- reshape：能兼容时零拷贝（修改 shape、计算新 strides），否则触发拷贝变成新的连续内存。
- 连续张量：offset = Σ (index[dim] × stride[dim])。

**三、例子：什么时候 tensor 的 reshape/transpose/permute 等操作会导致物理内存 copy:**

不是每一次调用都会导致 内存 copy，而是必要时进行。举几个比较真实的 MHA 中的例子：

例子（torch.nn.MultiheadAttention， 先转 batch first）：

```
# 假设输入
batch, seq, hid, num_heads = 2, 5, 16, 4
head_dim = hid // num_heads
q = torch.randn(batch, seq, hid)             # [batch, seq, hid], contiguous

q = q.transpose(0, 1)                        # [seq, batch, hid], zero-copy (stride 改变)
# 无论怎样都先变成 [seq, batch, hid]。torch.nn.MultiheadAttention 就是这样。然后作多 head 切分

q = q.reshape(seq, batch, num_heads, head_dim)  # [seq, batch, num_heads, head_dim], zero-copy
q = q.reshape(seq, batch * num_heads, head_dim) # [seq, batch*num_heads, head_dim], ⚠️ copy
q = q.reshape(batch * num_heads, seq, head_dim) # [batch*num_heads, seq, head_dim], zero-copy
```

另一个例子(总是第一维是 batch)：

```
batch, seq, hid, num_heads = 2, 5, 16, 4
head_dim = hid // num_heads
q = torch.randn(batch, seq, hid)                # [batch, seq, hid], contiguous

q = q.view(batch, seq, num_heads, head_dim)     # [batch, seq, num_heads, head_dim], zero-copy
q = q.permute(0, 2, 1, 3)                       # [batch, num_heads, seq, head_dim], zero-copy
# => [B, num_heads, seq, head_dim]

q = q.reshape(batch * num_heads, seq, head_dim) # [batch*num_heads, seq, head_dim], ⚠️ copy
```

再一个例子（megatron）：

```
batch, seq, hid, num_heads = 2, 5, 16, 4
head_dim = hid // num_heads
q = torch.randn(seq, batch, hid)                 # [seq=S, batch=B, hid=H], contiguous， megatron 情况。strides=[B*H, H, 1]

q = q.view(seq, batch, num_heads, head_dim)      # [seq, batch, num_heads, head_dim], zero-copy (hid 拆成 H=num_heads*head_dim)，连续。strides=[B*H, H, head_dim, 1]
q = q.reshape(seq, batch * num_heads, head_dim)  # [seq, batch*num_heads, head_dim], zero-copy，连续。 strides=[(B*num_head)*head_dim, head_dim, 1]=[B*H, head_dim, 1]

# 下面转成了 [B, seq, head_dim] 
q = q.permute(1, 0, 2)                           # [batch*num_heads, seq, head_dim], zero-copy (stride 改变)，不连续。strides=[head_dim, B*H, 1]
```

这个例子里，全程没有发生内存 copy。
- 如果在 q.shape = [seq, B=batch * num_heads, head_dim] 的时候就打住，k、v 也做同样操作：那么就相当于在 [S, B, H] shape 上直接做 attention，这是可以直接用 strided batched GEMM 处理的。
- 如果像 megatron 那样，再 permute 成 [B, S, H], 这时候内存不连续，但是没发生copy。如果 k、v 也同样处理，那么 torch.bmm 的时候，（猜测可能）也是直接用 strided batched GEMM 来实现了。
- 综上可以看到 megatron sequence-first 的道理：不管算 attn 时是 BSH 还是 SBH，都没发生内存 copy。
  - 算 attn 时是 $Q\times K^T$, 而 $K^T$ 好像可能需要内存 copy 成 contiguous。

### 总结

鉴于上面最后一段所说，那么 megatron 的 [S, B, H] 的好处，看来就是 MHA 的时候， [S, B, H] => [S, B, num_head, head_dim] => [S, B1 = B*num_head, H1=head_dim] => [S, B1, H1] => [B1, S, H1] 这一路都没内存 copy。而有它之后可以用 strided batched GEMM 计算。而 [B, S, H] => [B1, S, H1] 过程中，必然有内存 copy。
