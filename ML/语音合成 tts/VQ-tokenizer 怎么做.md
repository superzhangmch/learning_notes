假设 **codebook size = 1024**，本质上就是：

> 建立一个包含 **1024 个 D 维向量**的集合（也叫“码本”），每个向量是 $\mathbb{R}^D$ 中的 prototype。

这些向量可以表示 1024 个“离散语音单位”（就像词典里的词条），在训练过程中不断被优化。

## 使用过程：**就是最近邻查找**

给定一个输入连续向量 $\mathbf{z} \in \mathbb{R}^D$，执行以下步骤：

1. **遍历所有 codebook 向量** $\mathbf{c}_i \in \mathbb{R}^D, i=1,\dots,1024$
2. **计算欧几里得距离（L2 距离）**： $d_i = \|\mathbf{z} - \mathbf{c}_i\|_2$
3. **选出最小距离的索引**： $q(\mathbf{z}) = \arg \min_i d_i$
4. 输出的是一个整数 index（0\~1023），作为这个连续向量的离散表示。

## 实际部署时的 token 使用：

* 在 **推理阶段**，所有语音向量都被映射为这些 index；
* 模型（如 LLM）只需要处理这些离散 token，不处理原始连续向量；
* 最终可以用这些离散 index 来合成语音（通过 vocoder）或建模语音结构（如 LLM-TTS）。

## 多 codebook（如 VQ-VAE-2）情况：

* 有时会用多个并行 codebook，每个输出一个 index；
* 最终 token 是多个 index 的组合（比如 4个codebook，每个1024，总组合是 $1024^4$）。

## 原始连续向量映射到 codes 是否均匀

在实际训练中，这种平均覆盖并不会自动出现。实际上，大多数VQ方法并不优化 token 分布：VQ-VAE、VQ-GAN 中都观察到**codebook collapse，在 《CosyVoice v1》 中也指出，VQ codebook 的使用率只有 23%。
