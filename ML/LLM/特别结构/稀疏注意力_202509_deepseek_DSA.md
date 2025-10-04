# deepseek-DSA《DeepSeek-V3.2-Exp: Boosting Long-Context Efficiency with DeepSeek Sparse Attention》

MLA 有两种等价模式： MHA 或 MQA

<img width="1790" height="904" alt="image" src="https://github.com/user-attachments/assets/0cc7725f-97f9-4367-85ac-842ab4d9193e" />

deepseek-DSA 着眼于 MQA 模式：在 MQA 模式上的示意图如下：

<img width="1384" height="626" alt="image" src="https://github.com/user-attachments/assets/0023b5ff-ef78-48b1-b992-01bec4c53c23" />

简单说：当前位置的 q 和历史所有的 k 计算出 k 的重要性 score，然后根据 score 取 top，过滤出要实际参与 attn 的 kv。

## kv 重要性 score 怎么算 （indexer score）

score 计算公式是：

$$
I_{t,s} = \sum_{j=1}^{H^I} w_{t,j}^I \cdot \text{ReLU} (q_{t,j}^I \cdot k_s^I)
$$

- 其中所需各项： $w_{t,j}^I$, $k_s^I$ 从 hidden_states 经线性变换得到, $q_{t,j}^I$ 从 MLA 压缩后的 q_latent 经线性变换得到。q 是多 heads 的，所以上式 $\sum$ 就是遍历 q 的各个 head。
  - $H^I$ 是 q head 数。
- 上图中的 "partially apply RoPE"，其实就是和 MLA 一样，分成 rope 与 非rope 两个分支。
- 上面score 算的时候，是在 fp8 上算的，为此要做 fp8 量化。
  - 量化一般会遇到数据的 outliers 问题，从代码中看到它是通过对 q、k 施加 hadamard 变换完成的。更多参考：https://zhuanlan.zhihu.com/p/1908616046874699007 、 https://github.com/deepseek-ai/FlashMLA/pull/54 （打开后搜 hadamard)
  - hadamard 变换有关知识，看下面代码。
- 从公式看，q 和 历史 {k} 会遍历算相关性，按说也不是轻量级的，但是它没算 softmax，所以还是容易了很多。

我加了注释后的 forked 的代码在： https://github.com/superzhangmch/learn_DeepSeek-V3.2-Exp/blob/main/inference/model.py#L431 ，并摘录如下：

```
class Indexer(torch.nn.Module):
    def __init__(self, args: ModelArgs):
        ...
        
        # 这是是类似 kv-cache 一样的 indexer-k-cache，需要把历史都存下来。存的是 fp8 的，k 一个head，head_dim=128, 这样一个token 占 128字节的cache；再加上1字节的 scale，共129字节。
        self.register_buffer("k_cache", torch.zeros(args.max_batch_size, args.max_seq_len, self.head_dim, dtype=torch.float8_e4m3fn), persistent=False)
        self.register_buffer("k_scale_cache", torch.zeros(args.max_batch_size, args.max_seq_len, self.head_dim // block_size, dtype=torch.float32), persistent=False) # block_size=128

    def forward(self, x: torch.Tensor, # x: hidden_state
                     qr: torch.Tensor, # qr: MLA 的 latent_lora_q
                    start_pos: int, freqs_cis: torch.Tensor, mask: Optional[torch.Tensor]):
        bsz, seqlen, _ = x.size()
        end_pos = start_pos + seqlen

        q = self.wq_b(qr)                                                # qr: latent_lora_q; 这一样把它升维到 index_n_heads * index_head_dim，也就是 Index 内把 q 转成了多个 heads.
                                                                         # index_n_heads = 64, index_head_dim=128
        q = rearrange(q, 'b s (h d) -> b s h d', d=self.head_dim)
        q_pe, q_nope = torch.split(q, [self.rope_head_dim, self.head_dim - self.rope_head_dim], dim=-1)  # 各占 64 维
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

class MLA(nn.Module):
    def __init__(self, args: ModelArgs):
        ...
        self.indexer = Indexer(args)

        # MLA 显存占用，每个元素是 fp32 四字节，kv_lora_rank+qk_rope_head_dim=512+64, 一个 token的显存占用是（512+64）*4；而一个token在indexer 上只占用 129个字节。可见新增的显存占用不多
        #   note: attn 一般需要高精度。实际中，高效推理到底是 fp16，还是 fp32？
        self.register_buffer("kv_cache", torch.zeros(args.max_batch_size, args.max_seq_len, self.kv_lora_rank), persistent=False)
        self.register_buffer("pe_cache", torch.zeros(args.max_batch_size, args.max_seq_len, self.qk_rope_head_dim), persistent=False)
        ...

    def forward(self, x: torch.Tensor, start_pos: int, freqs_cis: torch.Tensor, mask: Optional[torch.Tensor]):
        ...

        scores = torch.einsum("bshd,bthd->bsht", q.float(), k.float()) * self.softmax_scale # 全序列的 QK'

        # indexer： 怎么在 MLA 中使用
        topk_indices = self.indexer(x, qr, start_pos, freqs_cis, mask)
        index_mask = torch.full((bsz, seqlen, seqlen), float("-inf"), device=x.device).scatter_(-1, topk_indices, 0) # topk_indices位置为0其余是 -inf
        index_mask += mask                                                                                           # mask：0 和 -inf 组成。所以这一句相当于是两个 mask 求交集
        scores += index_mask.unsqueeze(2)                                                                            # exp(-inf) = 0, 所以把 mask 加进 score

        scores = scores.softmax(dim=-1, dtype=torch.float32)                                                         # 按说这里需要作稀疏计算，这里通过施加 mask的方式，只是模拟了稀疏计算。真正线上并不能用这句，它不提速
        # 上面 scores 已经是经过 indexer 过滤后的只针对 2048 个 token的（其余的是0）

        ... go on ..
        return ..

```

超参数配置：

```
{
    ...
    # MLA 的配置
    "n_heads": 128,

    "q_lora_rank": 1536,       # q 被压成 1536 维 
    "kv_lora_rank": 512,       # k 被压成 512 维

    "qk_nope_head_dim": 128,   # 非rope 分支 head dim
    "qk_rope_head_dim": 64,    # rope 分支 head dim

    "v_head_dim": 128,

    # indexer 的配置
    "index_n_heads": 64,
    "index_head_dim": 128,     # indexer 总 head_dim=128。其中会分 rope、 非rope 两部分，看代码是各占64维
    "index_topk": 2048         # 序列再长，也只一次优选出 2048 个 token 作attn
}
```

- indexer 相比 MLA attn： head数减半（128=>64), head_dim 变三分之二(128+64 => 128).
- cache 显存占用：indexer 也需要有类似 kv-cache 一样的东西，它是 k-cache。
  - indexer 对单个 token 用 129字节（包括 128字节的 fp8 格式的 k，以及1字节的 fp8量化 scale 因子）
  - 而 MLA 的 kv-cache 一个token 用 （512+64）* sizeof(dtype); dtype=fp32（attn 需要高精度），则 总共 (512+64)*4=2304
  - 新增显存占用 129/2304 = 5.6%，确实新增不多
- 计算量：
  - xx


### 怎么训练的

在已经用 MLA 训练的模型上，新增 indexer 继续训练即可新增该功能。分预训练与后训练。

**预训练分两步：**

（1）、冻结其他参数，只训练 indexer：令 indexer 预测 MLA 的 attn softmax 的 input QK' score。indexer 不选取top2048，而是选取所有 token

$$
Loss = \sum_t D _ {KL}( p _ {t,:} || softmax(I _ {t,:}))
$$

$p _ {t,:}$ 是 softmax(QK'), 而 softmax(Indexer_score)= $softmax(I _ {t,:})$ 应该逼近它。学习率 1e-3，训练 1000 步，每步 16 个 128K token 序列，总计 21 亿 token。

（2）、在全量参数上训，且 indexer 选取 topK=2048

**后训练：**

流程和 DeepSeek-V3.1-Terminus 保持一致，以便严格对比 DSA 稀疏注意力的影响。

- Specialist Distillation（专家蒸馏），为不同任务单独训练专家模型（数学、竞赛编程、逻辑推理、智能代码、智能搜索）。
- Mixed RL Training：使用 GRPO 算法。

### 用于 train/prefill 和用于 decoding 的区别
