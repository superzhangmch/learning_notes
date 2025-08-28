
MXFP_n 低精度浮点数据格式的提出在 https://arxiv.org/pdf/2310.10537 《Microscaling Data Formats for Deep Learning》 2023.10，该文还只是以模拟的方式证明它的有效性。后来的 NVDIA Blackwell 系列 GPU 才真正物理上实现了它（如 GB200，在 2024年初发布年末发货；而 H100、H800 并不原生支持）。

它的思路和后来的 deepseek-v3 （ https://arxiv.org/pdf/2412.19437 2024.12）的 fp8 精度训练是很像的。

----

### 原理

它的实现，多于大 tensor，其中的 32 个相邻元素，用同一个 scaling factor：

<img width="826" height="366" alt="image" src="https://github.com/user-attachments/assets/df7e9ed6-c8d7-4c38-9e1b-a44913b0ffdb" />

<img width="1170" height="336" alt="image" src="https://github.com/user-attachments/assets/923b279d-a6d2-429d-976f-c52334ebe379" />

它的 scaling factor 是 E8M0 的，也就是都是 2 的幂次数。这使得 MXFP_n 的表示范围和 FP32 一样大——因为 fp32 的指数是 8bit 的。

**需要注意的一点：**

对于矩阵来说，他一次只能处理某一维的连续 32个数，如果对矩阵 transpose，则这 32 个数不再连续。因此 transpose 后，原 scaling 生效。也就是说： MXFP 量化与 transpose 顺序不可交换：

> When converting multi-dimensional tensors, a principle axis must be selected for the shared scale
(typically the reduction dimension in matrix multiplication). For a 2D matrix, the scale can be shared
by every k element in a row or column. Transposing a 2D matrix in an MX format changes the axis
of the shared scale — i.e., conversion to MX format and transposing are not commutative operations.

这导致，训练或推理中，如果同时用到一个矩阵与其转置，必须分别存一份：
Due to non-commutative nature of transpose and quantization into MX formats (see Section 3), the quantized weights Wᵢ and their transpose Wᵢᵀ must be stored as two separate tensors

### 用于训练的实例

《Microscaling Data Formats for Deep Learning》中有它的具体使用例子。和 deepseek-v3 的 fp8 训练还是很像的。

下面是矩阵乘法 y=XW 在训练时涉及的三种运算（forward 一次，backward 两次）：并和 deepseek-v3 对比

<img width="1130" height="874" alt="image" src="https://github.com/user-attachments/assets/012790d8-38df-4957-bb04-7586267dadf7" />

可以看到都是 gemm 矩阵乘法时，两个矩阵转低精度，而乘法结果是较高精度。



----

