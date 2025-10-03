# deepseek-DSA《DeepSeek-V3.2-Exp: Boosting Long-Context Efficiency with DeepSeek Sparse Attention》

MLA 有两种等价模式： MHA 或 MQA

<img width="1790" height="904" alt="image" src="https://github.com/user-attachments/assets/0cc7725f-97f9-4367-85ac-842ab4d9193e" />

deepseek-DSA 着眼于 MQA 模式：在 MQA 模式上的示意图如下：

<img width="1366" height="596" alt="image" src="https://github.com/user-attachments/assets/688ae9c1-abf2-43d6-8a42-98fb61f718ef" />

简单说：当前位置的 q 和历史所有的 k 计算出 k 的重要性 score，然后根据 score 取 top，过滤出要实际参与 attn 的 kv。

## kv 重要性 indexer score

score 公式是：

$$
I_{t,s} = \sum_{j=1}^{H^I} w_{t,j}^I \cdot \text{ReLU} (q_{t,j}^I \cdot k_s^I)
$$

- 其中所需各项：w, k 从 hidden_states 经线性变换得到, q 从 q_latent_lora 经线性变换得到。q 是多 heads 的，所以上式 $\sum$ 就是遍历 q 的各个 head。
- 上图中的 "partially apply RoPE"，其实就是和 MLA 一样，分成 rope 与 非rope 两个分支。
- 上面score 算的时候，是在 fp8 上算的，为此要做 fp8 量化。
  - 量化一般会遇到数据的 outliers 问题，从代码中看到它是通过对 q、k 施加 hadamard 变换完成的。更多参考：https://zhuanlan.zhihu.com/p/1908616046874699007 、 https://github.com/deepseek-ai/FlashMLA/pull/54 （打开后搜 hadamard)
  - hadamard 变换有关知识，看下面代码。
- 从公式看，这就仿佛 q 和 历史 {k} 算了一遍 softmax 一样，按说也不是轻量级的，但是它没算 softmax，所以还是容易了很多。

计算重要性 score 的 Indexer 的我加了注释的代码： https://github.com/superzhangmch/learn_DeepSeek-V3.2-Exp/blob/main/inference/model.py#L431 ，并摘录如下：

```
class Indexer(torch.nn.Module):
    def __init__(self, args: ModelArgs):
        ...

    def forward(self, x: torch.Tensor, # x: hidden_state
                     qr: torch.Tensor, # qr: MLA 的 latent_lora_q
                    start_pos: int, freqs_cis: torch.Tensor, mask: Optional[torch.Tensor]):
        bsz, seqlen, _ = x.size()
        end_pos = start_pos + seqlen

        q = self.wq_b(qr)                                                # qr: latent_lora_q; 这一样把它升维到 index_n_heads * index_head_dim，也就是 Index 内把 q 转成了多个 heads.
                                                                         # index_n_heads = 64, index_head_dim=128
        q = rearrange(q, 'b s (h d) -> b s h d', d=self.head_dim)
        q_pe, q_nope = torch.split(q, [self.rope_head_dim, self.head_dim - self.rope_head_dim], dim=-1)
        q_pe = apply_rotary_emb(q_pe, freqs_cis)
        q = torch.cat([q_pe, q_nope], dim=-1)
        
        k = self.wk(x)                                                   # k.shape = [..., index_head_dim]，Index 内把 k 转成了1 个 head
        k = self.k_norm(k)
        k_pe, k_nope = torch.split(k, [self.rope_head_dim, self.head_dim - self.rope_head_dim], dim=-1)
        k_pe = apply_rotary_emb(k_pe.unsqueeze(2), freqs_cis).squeeze(2)
        k = torch.cat([k_pe, k_nope], dim=-1)

        def rotate_activation(x):
            # 为什么要有 scale=1/sqrt(hidden_size): hadamard变换，并不是真的正交，而是 HH' = H'H = n*I, H.shape = [n,n], 所以要除以 1/sqrt(n)
            return hadamard_transform(x, scale=hidden_size ** -0.5)

        q = rotate_activation(q) # 内部其实就是做了一个 hadamard 变换。 hadamard变换是正交的，而正交矩阵其实就是旋转，所以叫 rotate_activation
        k = rotate_activation(k) 
        # 为什么上面 q 与 k 要做 hadamard 变换。
        #   (1) 首先，它不影响结果正确性： (qH)(kH)' = qHH'k'=qk', HH'=I 因为 H 正交。
        #   (2) 接下来要对 q、k 作量化，而 q、k 中的 outliers 值会导致量化的效果下降，于是希望降低 outliers。而 hadamard 变换正好可以使得输入维度上的相关性被打散，使得分量更接近独立、均匀。
        #       所以，这是为了fp8 量化而做的准备。
        
        q_fp8, q_scale = act_quant(q, block_size, self.scale_fmt)      # q，k 要 fp8 量化
        k_fp8, k_scale = act_quant(k, block_size, self.scale_fmt)
        self.k_cache[:bsz, start_pos:end_pos] = k_fp8
        self.k_scale_cache[:bsz, start_pos:end_pos] = k_scale
        
        weights = self.weights_proj(x) * self.n_heads ** -0.5          # weight = (xW) / sqrt(n_heads)
        weights = weights.unsqueeze(-1) * q_scale * self.softmax_scale

        # 下面是做 fp8 量化的重要性 score 计算：
        #  按 paper，计算公式是：index_score(s,t) = \sum_h weights_h Relu(q_h k), 其中q_h 是未知 s 的，k 是位置 t 的。q是多heads的，k 是单head的
        #  下面的 fp8_index 就是实现了 fp8 下的该操作。看代码其实现的大约是：
        #       logits = accum_fp32(q_8 * k_8')
        #       logits <- ReLU(logits) * weight
        #       logits_sum = \sum_{j=1}^{N_heads} logits_{:, :, :, j}
        #       index_score = logits_sum * k_s,  k_s 是量化恢复用的
        index_score = fp8_index(q_fp8.contiguous(), 
                                weights, 
                                self.k_cache[:bsz, :end_pos].contiguous(), 
                                self.k_scale_cache[:bsz, :end_pos].contiguous())

        # 下面是取 topK
        if mask is not None: index_score += mask
        topk_indices = index_score.topk(min(self.index_topk, end_pos), dim=-1)[1] # index_topk=2048
        topk_indices_ = topk_indices.clone()
        dist.broadcast(topk_indices_, src=0)
        assert torch.all(topk_indices == topk_indices_), f"{topk_indices=} {topk_indices_=}"
        return topk_indices
```

### 算 indexer score 看起来也挺重的，为啥总计算量是大大减少的

### 怎么训练的

### 用于 train/prefill 和用于 decoding 的区别
