HifiGan 与 bigVgan：后者在前者的基础上改进而来。它们都是要把 mel谱直接转化成声波。乃 GAN model。

input mel谱的 shape 是 [bs, seq_len, 80维mel谱], 它们的基本思路都是通过一系列的 1d 的transposeConv（转置卷积）层层升维拉长 seq_len, 直到拉长到最终的 audio wave 的 22k HZ 那么长。卷积过程中，通道数先由 80 升到一个较高维，然后逐步降直到最后一次变为单通道——这时候结果就是声波了。

# hifi-gan https://arxiv.org/pdf/2206.04658 

![image](https://github.com/user-attachments/assets/8552b6be-7d26-4c9a-91f3-569d744dc1dd)

input mel 谱的 shape是 [bs, seq_len, 80维mel谱], output 声波的 shape 是 [bs, audio 秒数*22k], 其中 22k是声波采样率(22.4k)。可以认为是二维图转一维线，但也可以认为是：80维压缩成了1维，同时mel谱帧数扩展成了audio的采样数，即 [bs, seq_len, 80维mel谱]  => [bs, 声波采样数, 1]。

generator 主要用的是 1d 转置卷积来逐次增加序列长度。在这个过程中，卷积通道数可以自由变化。

而判别器，都用的是二维卷积。也就是把声波设法转二维图后，用 2d conv。
- MRD：1d audio wave 经过 stft 后得到的是 [seq_len, feature_dim] shape 的 2d tensor。
  - stft 结果和 mel谱区别：stft结果，再经过 mel 滤波器，就得到了 mel谱。二者结果数据的 shape 不一样，但是都是 [seq_len, feature_dim] 形式的。
- MPD：1d audio wave 有如一根绳子按固定长度折叠出的 2d tensor。

generator 展开是这样的：

![image](https://github.com/user-attachments/assets/f94f60f4-a9fa-4b7f-8b55-79ac2bff7789)

snake 结果的图像如下图样子（斜着的正弦图的样子)：
![image](https://github.com/user-attachments/assets/1af63980-0740-4495-85f7-52e7c9e97d25)

### 具体例子（用 kimi-audio 用的 hifi-gan）

代码见我加注释的 https://github.com/superzhangmch/learn_Kimi-Audio/blob/master/kimia_infer/models/detokenizer/vocoder/bigvgan.py 。
