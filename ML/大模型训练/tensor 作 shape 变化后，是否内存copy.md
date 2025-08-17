

tensor 作 transpose、reshape 等操作后，不一定触发内存copy。它内部会记录一个 tensor 的维度有关元信息，它会尽量只是变动这些信息，如果实在没法调整，才会触发一次内存数据的调整。


### 矩阵的访问的 strides

一个矩阵 $A.shape = \[a, b, c, d\]$, 假如是连续的:

则访问它的 $A\[i,j,k,l\]$ 元素的时候，是通过 strides 完成的。它的

$$strides = \[bcd, cd, d, 1\]$$

为了计算 $A\[i,j,k,l\] = data\[offset\]$, 只需决定 offset

$$\text{offset} = i \times (bcd) + j\times(cd) + k \times d + l$$

矩阵 permute 等操作，主要手段就是交换或调整 strides。

### 各种矩阵转置交换操作怎么做的：

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
