HifiGan 与 bigVgan：后者在前者的基础上改进而来。它们都是要把 mel谱直接转化成声波。乃 GAN model。

input mel谱的 shape 是 [bs, seq_len, 80维mel谱], 它们的基本思路都是通过一系列的 1d 的transposeConv（转置卷积）层层升维拉长 seq_len, 直到拉长到最终的 audio wave 的 22k HZ 那么长。卷积过程中，通道数先由 80 升到一个较高维，然后逐步降直到最后一次变为单通道——这时候结果就是声波了。

# bigv-gan https://arxiv.org/pdf/2206.04658 《BIGVGAN: A UNIVERSAL NEURAL VOCODER WITH LARGE-SCALE TRAINING》

![image](https://github.com/user-attachments/assets/8552b6be-7d26-4c9a-91f3-569d744dc1dd)

input mel 谱的 shape是 [bs, seq_len, 80维mel谱], output 声波的 shape 是 [bs, audio 秒数*22k], 其中 22k是声波采样率(22.4k)。可以认为是二维图转一维线，但也可以认为是：80维压缩成了1维，同时mel谱帧数扩展成了audio的采样数，即 [bs, seq_len, 80维mel谱]  => [bs, 声波采样数, 1]。

generator 主要用的是 1d 转置卷积来逐次增加序列长度。在这个过程中，卷积通道数可以自由变化。

而判别器，都用的是二维卷积。也就是把声波设法转二维图后，用 2d conv。
- MRD：1d audio wave 经过 stft 后得到的是 [seq_len, feature_dim] shape 的 2d tensor。取代了 hifi-gan 中的 MSD，变成了这里的 MRD。
  - stft 结果和 mel谱区别：stft结果，再经过 mel 滤波器，就得到了 mel谱。二者结果数据的 shape 不一样，但是都是 [seq_len, feature_dim] 形式的。
- MPD：1d audio wave 有如一根绳子按固定长度折叠出的 2d tensor。
  - 怎样折叠成 2d的：
    - ![image](https://github.com/user-attachments/assets/7750997c-104c-4bd9-b619-aaca04c6b148)

generator 展开是这样的（作为 gan model 的 generator，可以看到**并没有 latent z 出现**。原来 gan 还可以这样！对于没有 noise z 的gan，也可以看作 z ~ dirac单点分布——这样的分布意味着 mode 非常单一）：

![image](https://github.com/user-attachments/assets/f94f60f4-a9fa-4b7f-8b55-79ac2bff7789)

snake 激活函数 $f(x) = x + \frac 1 \alpha \sin^2(\alpha x)$ 的图像如下图样子（有如斜着的正弦函数)：
![image](https://github.com/user-attachments/assets/1af63980-0740-4495-85f7-52e7c9e97d25)

bigv-gan 的loss 和 hifi-gan 一致，见下面 hifi-gan 部分。

### 具体实现

这里用 kimi-audio 中的 bigv-gan 来看看 generator 网络结构（代码见我 fork 后加注释的 https://github.com/superzhangmch/learn_Kimi-Audio/blob/master/kimia_infer/models/detokenizer/vocoder/bigvgan.py ）：

（1）、原始 mel谱 input，先扩充通道维数(即扩充 mel谱对应的维数)

```
input_x.shape = [1, 80, 136] = [bs, dim_of_mel=80, seq_len=136]
[1, 80, 136] => [1, 1024, 136] # 先经conv_1d(kernel=7)，扩充 mel维 80 到 1024  
```

(2)、经过 7 次 transposeConv-1d 上采样(conv-kernel 分别是 9 4 4 4 4 5 4, stride分别是 5 2 2 2 2 3 2)：
```
1：[1, 1024, 136] => [1, 1024, 680] # seq_len * 5, chanel_num / 1
2：[1, 1024, 680] => [1, 512, 1360] # seq_len * 2, chanel_num / 2
3：[1, 512, 1360] => [1, 256, 2720] # seq_len * 2, chanel_num / 2
  AMP-block:
    AMP-resnet-unit(kernel_size=3, dilation=1) # 每个 AMP-resnet-unit 的 output.shape = input.shape
    AMP-resnet-unit(kernel_size=3, dilation=3)
    AMP-resnet-unit(kernel_size=3, dilation=5)
  AMP-block:
    AMP-resnet-unit(kernel_size=5, dilation=1)
    AMP-resnet-unit(kernel_size=5, dilation=3)
    AMP-resnet-unit(kernel_size=5, dilation=5)
  AMP-block:
    AMP-resnet-unit(kernel_size=7, dilation=1)
    AMP-resnet-unit(kernel_size=7, dilation=3)
    AMP-resnet-unit(kernel_size=7, dilation=5)
  AMP-block:
    AMP-resnet-unit(kernel_size=11, dilation=1)
    AMP-resnet-unit(kernel_size=11, dilation=3)
    AMP-resnet-unit(kernel_size=11, dilation=5)
4：[1, 256, 2720] => [1, 128, 5440] # seq_len * 2, chanel_num / 2
5：[1, 128, 5440] => [1, 64, 10880] # seq_len * 2, chanel_num / 2
6：[1, 64, 10880] => [1, 32, 32640] # seq_len * 3, chanel_num / 2
7：[1, 32, 32640] => [1, 16, 65280] # seq_len * 2, chanel_num / 2
```

每次 transposeConv-1d 上采样后都是 4 个 AMP block, 每个内部 3 个 AMP-resnet-unit，共 12 个对应不同卷积核（3,5,7,11）与卷积 dilation（1,3,5）。上面只是在3和4之间示意了下，每两个之间都有。

每个 AMP-resnet-unit(kernel_size=KK, dilation=DD) 结构如下（和paper中有所出入）：

```
xt = snake_act(x)                          # = 低通上采样(transpose_conv_1d) + snake + 低通下采样(conv_1d)
xt = Conv1d(kernel_size=KK, dilation=DD),  # out_channel=in_channel, stride=1。KK=3,5,7,11; DD=1,3,5
xt = snake_act(xt)                         # = 低通上采样 + snake + 低通下采样
xt = Conv1d(kernel_size=KK),               # out_channel=in_channel, stride=1, dilation=1
x = xt + x
```
这里的 snake_act 正是：

![image](https://github.com/user-attachments/assets/fb5a47c2-2824-4d6e-924a-f2cad6d32c38)

low-pass-filter 为 "low-pass filter using a windowed sinc filter with a Kaiser window"，实际上是设法构造的一个具体的常数（而非 learnt) 的卷积核矩阵。所以低通上下采样，就是transpose_conv_1d 与 conv_1d 分别用相应constant 卷积核作卷积。

具体 kaiser_sinc_filter1d 是什么，待究。

(3)、后处理

依次是 (1). snake act,  (2). conv: [1, 16, 65280] => [1, 1, 65280],  (3). tanh 激活(output范围 -1~1)

---

# hifi-gan https://arxiv.org/pdf/2010.05646 《HiFi-GAN: Generative Adversarial Networks for Efficient and High Fidelity Speech Synthesis》

bigv-gan 乃对 hifi-gan 的升级。

### [generator

从代码上（hifi-gan：我fork后加注释 https://github.com/superzhangmch/learn_hifi-gan/blob/master/models.py ），和 kimi-audio中集成的 bigv-gan 代码很像。

![image](https://github.com/user-attachments/assets/0fb67f42-c690-451b-8023-3f7c82a62f9d)

最大区别应该是bigv-gan 用 ”低通上采样 + snake + 低通下采样“ 的 snake 激活替换了 hifi-gan 的  leaky-ReLU 激活。看看 generator 代码（原始paper中有 v1, v2, v3三种配置，这里看 v1）：

（1）、原始 mel谱 input，先扩充通道维数(即扩充 mel谱对应的维数)

（2)、经过 4 次 transposeConv-1d 上采样(conv-kernel 分别是 16, 16, 4, 4, stride分别是 8,  8, 2, 2)【注意 big-vgan 和它很像的】：
```
1：seq_len * 8, chanel_num / 2 减半
2：seq_len * 8, chanel_num / 2 减半
3：seq_len * 2, chanel_num / 2 减半
  block: kernel_size=3
    resnet-unit(kernel_size=3, dilation=1) # 每个 resnet-unit 的 output.shape = input.shape
    resnet-unit(kernel_size=3, dilation=3)
    resnet-unit(kernel_size=3, dilation=5)
  block: kernel_size=7
    resnet-unit(kernel_size=7, dilation=1)
    resnet-unit(kernel_size=7, dilation=3)
    resnet-unit(kernel_size=7, dilation=5)
  block: kernel_size=11
    resnet-unit(kernel_size=11, dilation=1)
    resnet-unit(kernel_size=11, dilation=3)
    resnet-unit(kernel_size=11, dilation=5)
4：seq_len * 2, chanel_num / 2 减半
```

每次 transposeConv-1d 上采样后都是 3 个 resnet-blocks, 每个内部 3 个 resnet-unit，共 9 个对应不同卷积核(3, 7, 11)与卷积 dilation(1, 3, 5)。上面只是在3和4之间示意了下，其实每两个之间都有。

每个 resnet-unit(kernel_size=KK, dilation=DD) 结构如下（big-vgan 和它很像的）：

```
xt = F.leaky_relu(x, LRELU_SLOPE)          # bigv-gan中把它升级成了 snake 激活，且激活前后有 up-sample / down-sample
xt = Conv1d(kernel_size=KK, dilation=DD),  # out_channel=in_channel, stride=1。KK=3, 7,11; DD=1,3,5。bigv-gan在这里仍然保持了和这里的一致
xt = F.leaky_relu(xt, LRELU_SLOPE)         # bigv-gan中把它升级成了 snake 激活
xt = Conv1d(kernel_size=KK),               # out_channel=in_channel, stride=1, dilation=1。bigv-gan在这里仍然保持了和这里的一致
x = xt + x
```

(3)、后处理

依次是 (1). leaky-ReLU act,  (2). conv: 多通道转 audio wave 的 1 通道,  (3). tanh 激活(output范围 -1~1)

### [判别器]

![image](https://github.com/user-attachments/assets/261b929e-870a-4b14-84aa-754c83438a96)

两种。一种是 1d audio wav 折叠成不同 height 的 2d data（MPD），另一种是 1d audio wav 作 avg-pooling（MSD)。

在 bigv-gan 中，只有 MPD 保留，另外一个变成了 MRD。

### [loss]

![image](https://github.com/user-attachments/assets/edbbdd0e-88a6-4d52-b6fb-637e60613c77)

bigv-gan 的loss 和这里 hifi gan 一致。
