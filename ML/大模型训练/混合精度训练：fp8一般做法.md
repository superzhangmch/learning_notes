可以参 《FP8 FORMATS FOR DEEP LEARNING》（下面用《FP8》代替） by nvidia/intel/arm, https://arxiv.org/pdf/2209.05433 

简单说
- fp8 主要是和计算单元的接口层而言，存储于带宽效率高
- 因 trian-inference 一致比 int8 量化好。
- 需要更精细的 rescale 控制

### fp8 格式

GPU 内， fp8 有 E5M2 与 E4M3 两种格式
- E5M2：1bit 符号位，5bit指数位，2bit 尾数(mantissa)位
  - 完全遵循 IEEE754，保留了 ±∞、NaN、0。
  - 动态范围大(-57344 ~ 57344)，但精度稍低，用于梯度。
    > 《FP8》：The recommended use of FP8 encodings is E4M3 for weight and activation tensors, and E5M2 for gradient tensors 
- E4M3：1位符号 + 4位指数 + 3位尾数
  - 不表示 ±∞，只有一个 NaN 编码，从而多出一段动态范围
  - 动态范围较小(-448 ~ 448)，但精度高，用于权重与激活

### gpu 内怎么做的

gpu (H100) 内部作 fp8 计算的时候，其实是先把 input tensor 转为 fp16 高精度表示，然后在高精度表示上做的计算。也就是说 FP8 只是**存储和接口**格式。这样看，不算真正的 fp8。

具体说来，在 H100 上执行类似 `D = A * B + C` 这样的 FP8 操作时，在 GPU 的 Tensor Core 里，这个过程大致如下：

1. **输入数据存储**：
   * A 和 B 可以以 FP8 格式存储（E4M3 或 E5M2，视任务选择）。
   * C（加数）通常不会用 FP8，而是用更高精度（例如 FP16/FP32/BF16）存放。
2. **计算时的内部提升 (accumulation promotion)**：
   * A 和 B 先从 FP8 **解码**到更高精度（通常是 FP16/BF16）。
   * Tensor Core 执行 **FMA（Fused Multiply-Add）**：

     $$
     D = (A_{fp8} \to fp16) * (B_{fp8} \to fp16) + (C \ in \ higher\ precision)
     $$
   * 结果 D 会先累加在 FP16 或 FP32 的寄存器里，避免数值误差爆炸。
3. **输出存储 (可选量化回 FP8)**：
   * 如果模型需要继续保持低精度存储，D 会再量化回 FP8——但是只是临近输出时转回而已。
   * 如果是中间结果或最终输出，可以保存在 FP16/BF16/FP32。

如果是 `D = A * B`, 不用加 C，过程仍然是先提升精度再计算。

### 好处

虽然内部并没按 fp8 计算，但是可以用一半显存，一半带宽（提高吞吐效率）。所以能提高训练效率。

而且用 fp8 方式训，则 inference 的时候——虽然 weight 保存为了 fp32——可以按 forward 方式转 fp8，train-inference 一致，精度可以不受损。而 int8 量化，则是有损的。
> 《FP8》：8-bit inference deployment is greatly simplified by FP8 training, as inference and training use the same datatypes.
This is in contrast to int8 inference with networks trained in 32- or 16-bit floating point, which require post-training
quantization (PTQ) calibration and sometimes quantization-aware training (QAT) in order to maintain model accuracy.
Furthermore, even with quantization aware training some int8-quantized models may not completely recover the
accuracy achieved with floating point.

### 实际怎么用

fp8 train，不只是 gpu 内部计算时，即使在代码层，也需要结合高精度（比如主权重一般存 fp32），所以其实是混合精度训练。

fp16 混合训练的时候，因为表示范围和 fp32 的差异，需要作 rescale。fp16主要是防止 underflow，主要是在 loss 处统一做 rescale。而 fp8 混合训练，则需要更细粒度的 rescale。一般是不同 tensor 不同的 rescale 因子，甚至tensor的不同片段不同的 rescale 因子（deepseek-v3 如此）。

另外，优化器所托管的参数，以及优化器状态，都不是 fp8 存储，仍用原做法。
