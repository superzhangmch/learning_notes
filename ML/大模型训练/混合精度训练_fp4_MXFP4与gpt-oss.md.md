
MXFP_n 低精度浮点数据格式的提出在 https://arxiv.org/pdf/2310.10537 《Microscaling Data Formats for Deep Learning》 2023.10，该文还只是以模拟的方式证明它的有效性。后来的 NVDIA Blackwell 系列 GPU 才真正物理上实现了它（如 GB200，在 2024年初发布年末发货；而 H100、H800 并不原生支持）。

它的思路和后来的 deepseek-v3 （ https://arxiv.org/pdf/2412.19437 2024.12）的 fp8 精度训练是很像的。

note： FP4 E2M1 表示的数字集合为：{0.0, ±0.5, ±1.0, ±1.5, ±2.0, ±3.0, ±4.0, ±6.0}, 为非等间隔的（否则用 int4就行了），见下图：

<img width="502" height="280" alt="image" src="https://github.com/user-attachments/assets/e5764bae-718a-4fa1-9895-38dea0c7aac0" />

----

### 原理

它的实现，多于大 tensor，其中的 32 个相邻元素，用同一个 scaling factor：

<img width="826" height="366" alt="image" src="https://github.com/user-attachments/assets/df7e9ed6-c8d7-4c38-9e1b-a44913b0ffdb" />

<img width="1170" height="336" alt="image" src="https://github.com/user-attachments/assets/923b279d-a6d2-429d-976f-c52334ebe379" />

它的 scaling factor 是 E8M0 的，也就是都是 2 的幂次数。这使得 MXFP_n 的表示范围和 FP32 一样大——因为 fp32 的指数是 8bit 的。

deepseek-v3 也是分组 scaling factor, 它的 scaling factor 并非E8M0，只有少数情况如此。而在 deepseek-v3.1 中，看起来都用了 E8M0。

**需要注意的一点：**

对于矩阵来说，他一次只能处理某一维的连续 32个数，如果对矩阵 transpose，则这 32 个数不再连续。因此 transpose 后，原 scaling 生效。也就是说： MXFP 量化与 transpose 顺序不可交换：

> When converting multi-dimensional tensors, a principle axis must be selected for the shared scale
(typically the reduction dimension in matrix multiplication). For a 2D matrix, the scale can be shared
by every k element in a row or column. Transposing a 2D matrix in an MX format changes the axis
of the shared scale — i.e., conversion to MX format and transposing are not commutative operations.

这导致，训练或推理中，如果同时用到一个矩阵与其转置，必须分别存一份：
Due to non-commutative nature of transpose and quantization into MX formats (see Section 3), the quantized weights Wᵢ and their transpose Wᵢᵀ must be stored as two separate tensors

### paper 中怎么用它的

《Microscaling Data Formats for Deep Learning》中有它的具体使用例子。和 deepseek-v3 的 fp8 训练还是很像的。

下面是矩阵乘法 y=XW 在训练时涉及的三种运算（forward 一次，backward 两次）：并和 deepseek-v3 对比

<img width="1130" height="874" alt="image" src="https://github.com/user-attachments/assets/012790d8-38df-4957-bb04-7586267dadf7" />

可以看到都是 gemm 矩阵乘法时，两个矩阵转低精度，而乘法结果是较高精度。

和 deepseek-v3 一样，norm，softmax 等是在高精度进行的。训练主参数是 fp32 的：
> Vector operations (e.g., layernorm, Softmax, GELU, and residual add) are performed in a scalar floating-point format like Bfloat16 or FP32.
>
> ...
> 
> A master copy of the weights is kept in FP32, and this copy is updated in each training step. 

----

### openai gpt-oss 怎么用的 MXFP4

从这里 https://huggingface.co/openai/gpt-oss-120b/tree/main 可看到， gpt-oss-120b，参数是 120B，但是模型文件大小是 65G——如果是你 fp16 存储应该是 240GB 的，按 fp8 也应该有 120GB。这正是因为它在后训练时用了 MXFP4 做了微调。

它也不是所有参数都 MXFP4，但是鉴于 MOE 参数在总参数的占比极大（gpt-oss-120B 中占比 90%），只冲这点，模型文件就应该是120 的差不多一半了。

模型详情在： https://cdn.openai.com/pdf/419b6906-9da6-406c-a19d-1bb078ac7637/oai_gpt-oss_model_card.pdf

| 部件  | 参数量 |
| -------- | ------- |
| MOE：MLP | 114.71B |
| Attention(Q K V O 四映射) | 0.96B |
| Embed + output head | 1.16B |
| 总共 | 116.83B |

只是 MOE 做了 MXFP4，那么估算模型文件大小：
- moe 层一个参数 mxfp4 后占用 4.25 bits；
  - 每32个4bit FP4 共享一个 8bit 的 scaling factor，于是每个数存储占用为： $(32 \times 4 + 8) / 32 = 4.25$
- attn 与 emb 按每参数2字节算。
- 则模型文件为： $114.71 \times 4.25 / 8 + (0.96+1.16) \times 2 = 65.18 GB$, 和他发布的文件大小吻合。

**其他信息：**

根据 https://huggingface.co/openai/gpt-oss-120b/blob/main/config.json，只对 MOE 部分做了 MXFP4 的量化：
```
  "quantization_config": {
    "modules_to_not_convert": [
      "model.layers.*.self_attn",
      "model.layers.*.mlp.router",
      "model.embed_tokens",
      "lm_head"
    ],
    "quant_method": "mxfp4"
  },
```

根据 https://huggingface.co/openai/gpt-oss-120b/blob/main/original/dtypes.json，没有 mxfp4 量化的参数具体为：
```
{
 "embedding.weight": "BF16",
 "norm.scale": "BF16",
 "unembedding.weight": "BF16"
  ...
 "block.0.attn.norm.scale": "BF16",
 "block.0.attn.qkv.weight": "BF16",
 "block.0.attn.qkv.bias": "BF16",
 "block.0.attn.sinks": "BF16",
 "block.0.attn.out.weight": "BF16",
 "block.0.attn.out.bias": "BF16",
 "block.0.mlp.norm.scale": "BF16",
 "block.0.mlp.gate.weight": "BF16",
 "block.0.mlp.gate.bias": "BF16",
 "block.0.mlp.mlp1_bias": "BF16",
 "block.0.mlp.mlp2_bias": "BF16",
 ...
}
```
