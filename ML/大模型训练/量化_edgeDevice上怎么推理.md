# 苹果-2025《Apple Intelligence Foundation Language Models》 https://arxiv.org/pdf/2507.13575

它的方案是两个模型：服务端与设备端相结合(都支持 vision as input)。
- On-device Model 能做到隐私保护
- Server Model 能处理复杂任务，注重处理能力和可扩展性。该设计使得苹果能够根据不同的使用场景提供最合适的解决方案。

它的 server model，有特殊之处【Parallel Track (PT) Transformer】，但这里只说它的 device model。device side model 是个 3B 的小模型，运行于 Apple Silicon 上（mac，iphone 上都用到）。

### 3B LLM 怎么高效执行的

rk-3588 这样的设备，官方 rknn-llm 运行 1.5B model 运行速度大约 15 token/s (https://github.com/airockchip/rknn-llm/blob/main/benchmark.md )，那么 apple 3B 怎么在 edge-device 上运行起来的呢？

（1）、架构优化：不同层的 kv-cache 共享。这样 prefilling 也会很快

将模型分为两个块，块1包含62.5%的Transformer层，而块2包含剩余的37.5%层，但不生成键值对（key-value）。通过共享缓存（KV-cache），块2的计算可以直接使用块1生成的缓存，减少了内存使用。具体待深究。

（2）、量化感知训练（QAT）：整体上来说和一般的 QAT 是一样的
- 将模型参数压缩到2比特
- 2bit: 用更平衡的 {-1.5, -0.5, 0.5, 1.5} 4值
- 缩放因子是学习出的： $s = f · max(|W|) / q_{max}$, f 是学出的; 并通过一种特殊方式初始化 f
  - 而 s 用于模拟量化： $W \leftarrow s · (clamp(⌊ W s + z⌉, q_{min}, q_{max}) − z)$
- 反向传播时，忽略量化操作（即用 STE=Straight-Through Estimator，而一般 QAT 都是这样操作的)。

（3）用 lora 作量化精度修复：也就是先量化，然后用 lora 作量化误差补偿。

> To recover model quality lost during the compression stages, we apply Low-Rank Adaptation (LoRA) adapters to both models and further fine-tune these adapters using the same data recipe as the base model training.

（4）、硬件适配：是否有针对 2bit 或 transformer 的特殊优化？paper 没提到


note： ASTC 只用于 server model。（ASTC：Adaptive Scalable Texture Compression (ASTC) is a block-based lossy compression format originally developed for efficient texture representation in GPU graphics pipelines ）

### 3B LLM 怎么扩展新能力的

用 lora 插件（注意不同于上面的精度回复的 lora)。开发者在 base model 上可以训练自己的 lora。

> We’ve carefully designed the framework to help app developers get the most
out of the on-device model. For specialized use cases that require teaching the∼3B
model entirely new skills, we also provide a Python toolkit for training rank-32
LoRA adapters as well as optionally training a draft model for on-device speculative
decodinpters produced by the toolkit are fully compatible with the Foundation
Models framework.

----

# 小米的端侧大模型推理

实现了超过 180 tokens/s 的端侧推理速度

https://www.infoq.cn/article/wiquyt3je0dqirddwzqm

- 动态输入与动态 context 支持：云端推理天然支持动态输入，而端侧的 NPU 通常只能使用静态图，输入尺寸固定。传统做法是将输入 padding 到固定长度，比如用 128 token 固定输入长度，即使真实输入只有 100 也要补足，这样会浪费大量计算资源。我们通过框架级的能力，让模型在保持静态图性能的前提下支持动态输入，自动切分输入尺寸，从而大幅提升了资源利用率和吞吐率。
- 投机推理（Speculative Decoding）优化：在云端，像 Medusa 或 Eagle 等方案通常能做到 2～3 倍的加速。而我们通过自研策略，在端侧实现了高达 7～10 倍的 decoding 加速，大幅缓解了端侧推理慢的问题。举例来说，原本在资源受限的设备上，推理速度可能只有二十几 tokens/s，通过投机推理可以提升到 200 tokens/s，这一速度已经可以媲美部分云端场景。
- 量化与指令级优化：大部分 CPU 操作通过 Neon 指令集实现加速，比如量化与反量化、sampling 采样等。
- 面对多任务、多业务的实际场景，采用了“共享基座架构”的方案
  > 为每个业务分别部署一个独立模型。所以我们采用了“共享基座模型 + 插件化能力”的思路，让多个业务共用同一个基础模型。
  > 具体做法是，我们为所有业务统一选择一个基础的大模型，然后针对不同业务单独训练对应的 LoRA 模块。例如：
  > A 业务针对这个基础模型训练一个专属的 LoRA；B 业务则训练另一个 LoRA。运行时，如果是 A 业务的请求到来，我们就加载基础模型 + A 的 LoRA 进行推理；当 B 业务请求到来时，我们就卸载 A 的 LoRA，换上 B 的 LoRA。
- prompt cache。它能缓存用户输入的 prompt 前缀，减少重复计算。
