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

snake 激活函数 $f(x) = x + \frac 1 \alpha \sin^2(\alpha x)$ 的图像如下图样子（有如斜着的正弦函数)：
![image](https://github.com/user-attachments/assets/1af63980-0740-4495-85f7-52e7c9e97d25)

### 具体实现

这里用 kimi-audio 中的 hifi-gan 来看看 generator 网络结构（代码见我加注释的 https://github.com/superzhangmch/learn_Kimi-Audio/blob/master/kimia_infer/models/detokenizer/vocoder/bigvgan.py ）：

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

每次 transposeConv-1d 上采样后都是 4 个 AMP block, 每个内部 3 个 AMP-resnet-unit，共 12 个对应不同卷积核与卷积 dilation。上面只是在3和4之间示意了下，每两个之间都有。

每个 AMP-resnet-unit(kernel_size=KK, dilation=DD) 结构如下：

```
xt = snake_act(x)                          # = 低通上采样 + snake + 低通下采样
xt = Conv1d(kernel_size=KK, dilation=DD),  # out_channel=in_channel, stride=1,
xt = snake_act(xt)                         # = 低通上采样 + snake + 低通下采样
xt = Conv1d(kernel_size=KK),               # out_channel=in_channel, stride=1, dilation=1
x = xt + x
```
这里的 snake_act 正是：

![image](https://github.com/user-attachments/assets/fb5a47c2-2824-4d6e-924a-f2cad6d32c38)

(3)、后处理

依次是 (1). snake act,  (2). conv: [1, 16, 65280] => [1, 1, 65280],  (3). tanh 激活(output范围 -1~1)

