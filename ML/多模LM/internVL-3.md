https://arxiv.org/pdf/2504.10479, 《internVL-3》，上海AI实验室

它用的是 "ViT-MLP-LLM" 架构。

### LLM 中的位置编码：用所谓的 V2PE（https://arxiv.org/pdf/2412.09616）方法。

仍然用 1d 位置编码，但是对于一个img的多个tokens，它们的位置顺序id的递增不再是1（text 就是1），而是一个小于1的 $\delta$。 这样好处是，通过间隔能区分出这一块儿时 img，且img占用的位置空间较小，从而能节约有限的 LLM context size(这个size 是由支持的最大位置编码id决定的）。训练时， $\delta$ 可以取用各种值， infer时就支持不同的 $\delta$ 了。

![image](https://github.com/user-attachments/assets/f23cbbee-8f6a-4f38-ac24-5488e41c63ee)

### 是否只能固定分辨率
从它所用的 vision encoder （ https://huggingface.co/OpenGVLab/InternViT-6B-448px-V2_5 ） 看：
> As in the previous version, we applied a pixel unshuffle operation, reducing the number of visual tokens to one-quarter of the original. Besides, we adopted a similar **dynamic resolution** strategy as InternVL 1.5, **dividing images into tiles** of 448×448 pixels. The key difference, starting from InternVL 2.0, is that we additionally introduced support for multi-image and video data.

也就是大图切分成多个448x448 的固定图的方式，支持了任意大小的图。所用 vision encoder 内部应该有（不确，未考） 2d 位置编码。否则LLM中的 1d位置编码怎么区分出img tokens 的位置坐标呢？
