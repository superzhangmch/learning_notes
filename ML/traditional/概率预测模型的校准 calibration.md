# 概率预测模型的校准 calibration

对于概率预测模型——比如LR——我们是希望预测概率和实际概率相符的。但是这往往难以精确做到，至少是有一个 gap 的。其实好多时候，预测概率和实际概率的差别并没那么大，或者说即使有很大的差别，但是这个差别是有规律的，于是可以通过一定的方式作概率校正。这就是所谓的概率 calibration。

好多时候，并不好判断单个sample的实际概率。这时候，校正一般用的是

【参】http://blog.csdn.net/zc02051126/article/details/54379244
