# 深度学习之CTC损失函数 

RNN 用于预测的时候，input 和 output 长度一样。有的时候，output 长度会短于 input。

比如：语音识别的时候，语音可能按固定几十毫秒为长度，作为RNN 输入序列的一个时间点。这时候单个字 的发音可能会被分到输入的多个连续时间点里，那么对应到output的也会是output序列中的多个时间点。再比如，用RNN做单行OCR识别时，会把图形按列拆分得很长然后作为输入序列，而输出序列则是识别出很短的文字。

这都使得一般的softmax + 交叉熵的损失函数不可行。因此才引入了处理这类情况的CTC损失函数。

简单说，CTC 的第一步仍然是softmax，但是 softmax 的label总个数会比实际多1（多加一个 blank 类别）。从任何方式沿时间序列逐个选取出 的softmax output序列（按专业说法是输出路径）到最终output序列的转化方式是这样的：先对非blank label去重，再去除所有blank。可以认为，损失函数仍然是交叉熵（或者说最大似然估计），只是针对的是按前述转化后的output（当然要求转化后等于样本标注）。样本标注可以对应未转化前的多个可能，因此其概率就是把这些可能性全加起来（可以动态规划算法加速）的结果。预测的时候，则是找出给定input下，能给出转化后最大概率的序列。

参考：
- http://m.blog.csdn.net/article/details?id=48526479
- https://zhuanlan.zhihu.com/p/21344595
- http://blog.csdn.net/xmdxcsj/article/details/51763886 系列
- http://www.cs.toronto.edu/~graves/arabic_ocr_chapter.pdf （这个讲得很好）
