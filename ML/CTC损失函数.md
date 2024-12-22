# CTC 损失函数

### 目的：从长序列解码出短序列
----
seq2seq 建模的时候，input 和 output 长度不一定一样。一种情况是：output 长度会短于 input。比如：语音识别的时候，语音可能按固定几十毫秒为长度，作为 RNN 输入序列的一个时间点。这时候单个字的发音可能会被分到输入的多个连续时间点里，那么对应到output的也会是output序列中的多个时间点。再比如，用 RNN 做单行 OCR 识别时，会把图形按列拆分得很长然后作为输入序列，而输出序列则是识别出的很短的文字。

不但长度不同，output 和 input 序列的对应关系往往也不存在——即没有标注出来。

这都使得一般的 `log(output 序列似然)` 【即 softmax + 交叉熵】的损失函数不可行——你都不知道该用交叉熵预测谁。

因此才引入了处理这类情况的 CTC 损失函数。CTC 的好处是能把 output 序列扩充成input 序列一样的长度，并作自动序列对齐。

### CTC 做法
----

- CTC 首先对 output 序列作扩充使得其长度等于 input 序列。扩充方式是令 output 中每个字符都可以连续重复任意多次，只要扩充后总长度没超 input。另外，为了识别一个字符是某字符的重复扩充还是原本就存在的，引入一个特殊空白字符（ε）。也就是 `hello` 可以变成 `hhh eee ll ε lll oooo` 这样子（若没 ε，就不知道 `lllll` 对应原始的 `l` 还是 `ll` 了）。
- 显然对于一个 output 序列，有多种扩充（学名叫 alignment）方式。CTC 把每一种符合上述规则的 alignment 都当做有效扩充。
- 对于有效 alignment 中的任意一个，鉴于扩充后 output 序列 Y 已经与 input 序列 X 等长了，所以就可以按一般的 `log(序列似然)` 【即逐 step 计算 “softmax + 交叉熵”，再和之】 方式计算该 alignment 的 loss 了：

$$loss(outut=Y|input=X) = \log(\Pi_i P(y_i|x_i) = \sum_i \log(P(y_i|x_i)))$$
  
- CTC 对一个 output 的最终 loss 是：所有有效 alignment 的逐step 交叉熵总和，当做 CTC loss。即：

$$loss_{CTC}(Y_{ori}|X) = \sum_{Y\ 是\ Y_{ori}\ 的\ alignment} loss(Y|X)$$


也就是说，CTC loss 是用**所有合法 alignment 的总体**来计算当前 output 的 loss 的。在解码的时候，只要能正确解出这个"总体"中的任一个，都可以得到正确答案。所以对于具体一个output，该 loss 通过试图最小化这一堆东西来达到目标还是有道理的。

### 动态规划加速 CTC loss 计算
----

一个问题是，要遍历所有合法 alignment，不是个容易事。好在有动态规划算法可以高效实现之：总有些 alignment 是有相同的前面部分的，于是可以把这部分的计算合并。于是可以用动态规划的拆分子问题的常规套路解决之。这部分虽然稍显复杂，但是终究只是为了加速而已。

### 解码生成
----


参考：
- https://distill.pub/2017/ctc/ （很好）
- https://ogunlao.github.io/blog/2020/07/17/breaking-down-ctc-loss.html
- http://www.cs.toronto.edu/~graves/arabic_ocr_chapter.pdf （这个讲得很好）
- http://m.blog.csdn.net/article/details?id=48526479
- https://zhuanlan.zhihu.com/p/21344595
- http://blog.csdn.net/xmdxcsj/article/details/51763886 系列
