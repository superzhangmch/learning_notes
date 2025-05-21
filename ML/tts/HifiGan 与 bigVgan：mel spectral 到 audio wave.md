HifiGan 与 bigVgan：后者在前者的基础上改进而来。它们都是要把 mel谱直接转化成声波。乃 GAN model。

input mel谱的 shape 是 [bs, seq_len, 80维mel谱], 它们的基本思路都是通过一系列的 1d 的transposeConv（转置卷积）层层升维拉长 seq_len, 直到拉长到最终的 audio wave 的 22k HZ 那么长。卷积过程中，通道数先由 80 升到一个较高维，然后逐步降直到最后一次变为单通道——这时候结果就是声波了。

