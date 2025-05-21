tts 生成的一种方式是先生成离散的 audio token ids，再用 flow-matching model 转为 mel谱，再用 gan model 转为 audio wave。

这里考察下 kimi-audio 中的 flow-matching。flow-matching 本身不作记述。

### DiT block

model 由多个 DiT（diffusion transformer） block 组成：
```
# 我加了注释的： https://github.com/superzhangmch/learn_Kimi-Audio/edit/master/kimia_infer/models/detokenizer/flow_matching/dit_block.py
class DiTBlock(nn.Module): ## 乃 transformer 结构
    def __init__(...):
        super().__init__()
        self.norm1 = nn.LayerNorm(hidden_size, elementwise_affine=False, eps=1e-6)
        self.attn = Attention(hidden_size, num_heads=num_heads, qkv_bias=True, **block_kwargs)
        self.norm2 = nn.LayerNorm(hidden_size, elementwise_affine=False, eps=1e-6)
        ...
        self.adaLN_modulation = nn.Sequential(nn.SiLU(), nn.Linear(hidden_size, 6 * hidden_size, bias=True))

    def forward(self, x,   # x_t
                      c,   # condition 
                      seq_len, ...,):

        # x.shape = torch.Size([1, 120, 2304])=[bs, seq_len, dim], c.shape = torch.Size([1, 120, 2304])
        
        shift_msa, scale_msa, gate_msa, shift_mlp, scale_mlp, gate_mlp = self.adaLN_modulation(c).chunk(6, dim=2) # adaLN_modulation = Silu + linear， input 条件 c 只用于这里
                                                                                                                  # 从这行可见，条件 c 只是通过 modulate 方式参与到model，而非通过 cross-attn

        ############ 1. ATTN ##############
        
        x_ = modulate(self.norm1(x), shift_msa, scale_msa)  # => x * (1 + scale) + shift， scale shift 来自 c.
                                                            # 这种特征融合方式叫 FiLM 

        ...

        x_ = self.attn(x_,   # x.shape = (B, N, C), 所以 attn 是 N 的不同元素之间做的，也就是类似 LLM 的不同token之间那样。
                       seq_len=seq_len, ... )

        if not nopadding:
            x_ = x_ * mask[:, :, None]

        x = x + gate_msa * x_ # x 是原始input x， gate_msa 来自 c。 这行是 transformer 中的 ATTN 的 resnet 结构

        ############ 2. FFN / MLP ##############
        
        x_ = modulate(self.norm2(x), shift_mlp, scale_mlp) # shift_* 来自c

        x_ = self.mlp(x_) # 

        if not nopadding:
            x_ = x_ * mask[:, :, None]

        x = x + gate_mlp * x_ # gate_mlp 来自 c。 这行是 transformer 中的 FFN 的 resnet 结构

        ## DiTBlock 内部先是 ATTN，然后是 FFN, 所以确实是一个 transformer block
        return x
```
block 其实就是一个 transformer block：有 attn，有 ffn。且input x.shape = [bs, seq_len, dim], 所以像 LLM 一样作 attn 即可。

![image](https://github.com/user-attachments/assets/cb6e6ebe-07f8-4531-a7fb-d3b53c81ad5b)

图中：
- FiLM: x_new = x * (1 + scale_c) + shift_c
- gate: x_new = x * gate_c
- attn: 乃沿着时间(seq_len)做的。
- 多个该block stack起来，就是整个model。

### model 主体：

```
我加了注释的： https://github.com/superzhangmch/learn_Kimi-Audio/blob/master/kimia_infer/models/detokenizer/flow_matching/model.py

class DiTPrefix(nn.Module):
   
    def __init__(...):
        self.t_embedder = TimestepEmbedder(hidden_size)
        self.semantic_token_embedding = nn.Embedding(semantic_vocab_size, hidden_size)
        self.input_linear = nn.Linear(input_size, hidden_size)

        ...

        self.blocks = nn.ModuleList(
            [
                DiTBlock(
                    hidden_size,
                    num_heads,
                    mlp_ratio=mlp_ratio,
                    ffn_type=ffn_type,
                    ffn_conv_kernel_size=ffn_conv_kernel_size,
                    ffn_gated_glu=ffn_gated_glu,
                    ffn_act_layer=ffn_act_layer,
                )
                for _ in range(depth)
            ]
        )
        self.final_layer = FinalLayer(hidden_size, output_size) 
 
    def forward(self, x,   # input: x_t.shape = [bs, seq_len, 80(维的mel谱)]
                position_ids,
                t,
                condition, # audio-tokens-id-list
                ...,):
        
        # condition.shape = torch.Size([1, 120])= [batch_size, seq_len]， 120是可变的，下面的120都是可变的seq length
        condition = self.semantic_token_embedding(condition)  # (N, T, D),  audio-tokens-id-list 转为他们的 embedding
        # condition.shape = torch.Size([1, 120, 2304])， 2304=256*9

        # x.shape = torch.Size([1, 120, 80])
        x = self.input_linear(x)
        # x.shape = torch.Size([1, 120, 2304])

        if self.position_embedding is not None:
            position_emb = self.position_embedding(position_ids)
            x = x + position_emb

        if self.use_rope:
            ...

        t = self.t_embedder(t)          # (N, D)，           t.shape = torch.Size([1, 2304])
        c = t.unsqueeze(1) + condition  # (N, T, D), condition.shape = torch.Size([1, 120, 2304])

        for block_idx, block in enumerate(self.blocks):
            # x = block(x, c, attn_mask)  # (N, T, D)
            # XXX mask could be None because we always use full mask

            x = block(
                x=x,  # x.shape = torch.Size([1, 120, 2304])
                c=c,  # c.shape = torch.Size([1, 120, 2304])， c = audio_tokens_id_embedding + time_steps_embs
                      # block 内部： c 转化成 "x * (1 + scale) + shift" 里的 scale、shift，从而参与进 model
                ...
            )

        # x.shape = torch.Size([1, 120, 2304]) c.shape = torch.Size([1, 120, 2304])
        x = self.final_layer(x, c)  # (N, T, C)。 final_layer 内部： c 转化成 "x * (1 + scale) + shift" 里的 scale、shift，从而参与进 model
        # x.shape = torch.Size([1, 120, 80]) # 已经变回 mel 谱的 shape 了

        # output.x_{t_1}.shape = [bs, seq_len, 80(维的mel谱)]
        return x
```

model 内部： input x_t.shape [ bs, N, mel谱80]，最终output 也需要这样shape。dim 先由 input_linear 把 80 升到 2304，按 2304 一路操作，最后经过 final_layer 又降到了 80.

condition 为整数类型的tokens id。它需要先作 embedding。

condition 和 timestep 的 embedding 加起来，然后作为 modulate 方式给到 transformer，而非经过 cross attn。

上面 model 只是基于 $x_t$ 预测怎样得到 $x_{t-1}$ 的 v，只负责生成过程中的一步。按 flow-matching 的这是，该model只是列出了 ODE 常微分方程 $\frac {dx} {dt} = v$

### 整体

首先是生成随机噪声(它会作为 ODE 方程的初始状态)：

```
x_t = torch.randn(semantic_tokens.shape[0], 80).to(self.device).to(self.dtype) # [seq_len,  mel-80-维]
```

然后就是用标准 ODE 的方程解法来解方程即可了。它默认用了 `from torchdyn.core import NeuralODE` 来解的方程，30 步完成。且没有用 classfier guidance 技术。

### 其他

1. mel-谱是二维图片，那么容易觉得用文生图那样的方式就行了，毕竟后者也是图。但是 mel-谱的二维img，其中一条边是不定长的。如何理解此差异？

其实文生图的 out.shape = [BS, H，W， RGB三通道], H*W 相当于是  seq_len, mel-谱的二维图片，out.shape = [BS, seq_len, mel-80维]. 也就是 H x W 对应的是 seq_len, RGB3 通道对应 mel-80维（或者说80通道）
