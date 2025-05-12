# CTC 损失函数

### 目的：从长序列解码出短序列
----
seq2seq 建模的时候，input 和 output 长度不一定一样。一种情况是：output 长度会短于 input。比如：语音识别的时候，语音可能按固定几十毫秒为长度，作为 RNN 输入序列的一个时间点。这时候单个字的发音可能会被分到输入的多个连续时间点里，那么对应到output的也会是output序列中的多个时间点。再比如，用 RNN 做单行 OCR 识别时，会把图形按列拆分得很长然后作为输入序列，而输出序列则是识别出的很短的文字。

不但长度不同，output 和 input 序列的对应关系往往也不存在——即没有标注出来。

这都使得一般的 `log(output 序列似然)` 【即 softmax + 交叉熵】的损失函数不可行——你都不知道该用交叉熵预测谁。

因此才引入了处理这类情况的 CTC 损失函数。CTC 的好处是能把 output 序列扩充成input 序列一样的长度，并作自动序列对齐。

注意：如果 seq2seq 用input的固定长度的表示后，塞给某网络解码出 output，则不适用 CTC。input 序列对应位置解码出 output 的建模方式时，才适用 CTC。

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

一个问题是，要遍历所有合法 alignment，不是个容易事。好在有动态规划算法可以高效实现之：总有些 alignment 是有相同的前面部分的，于是可以把这部分的计算合并。于是可以用动态规划的拆分子问题的常规套路解决之。

但要注意，动态规划算法虽然稍显复杂，但是终究只是为了加速而已。

参 https://distill.pub/2017/ctc/ 中内容，简述如下（图也来自它）：

动态规划，解决的其实就是两个序列的某种对齐。所以它可以用一个矩阵来表示对齐路径。每一步要么平着走，要么斜着往下走。斜着走表示两个序列都前进一步：也就是"对齐"在两方都前进一步。横着走表示只在其一上前进，在另一者上原地不动。对于矩阵的一个具体位置：从左上角到该位置，正好对应的就是动态规划的一个所谓子问题。既然行进到这一位置了，表示相应的子问题其实已经得解了，接下来做的就是继续前进，解决更大的子问题，并最终指的原始问题了。

![image](https://github.com/user-attachments/assets/1db40ab5-7fc1-48a6-83d6-4aa0ad567212)

鉴于以上， 在上图矩形形式视角看来，CTC loss 的动态规划是这样的：

首先把 output Y 在首尾以及任两字符之间添加空白字符ε，即变成如下 Z，然后在此 Z 上操作：

$$
Z = [ϵ , y_1 , ϵ , y_2 , … , ϵ , y_U , ϵ]
$$

- 一定可以水平前进一格。表示 output 字符重复一次（即没有识别出新字符）。
  - 无论在 Z 的什么字符位置。
- 总可以右下移一格：只要 output 的 align 扩充没耗尽允许的长度值（不能超 input 长度）。毕竟所谓有效 alignment 是纯规则定义出的，而不管背后是否是真正 align（而这正是要 learn 出的）。
  - 无论在 Z 的什么字符位置。
- 但某些时候，可以斜着 “跳一格” 前进一步：Z 中的 ϵ 是特意插入的，并非都必须。ϵ 前后字符不一样的时候，这个 ϵ 就没必要。于是跳一格就是跳过这样的 ϵ。
  
  ![image](https://github.com/user-attachments/assets/d5150948-b656-4920-aa75-bd0239e9c5b4)


### 解码生成
----

按 CTC 方式解码，理论上的方式是：找出使得总和 log(序列似然) 最大的那个“aligment 序列簇”，该序列簇中任意一个序列都是某一序列的 “上述” 有效合法 alignment，且该簇包含了该序列的所有 aignment。于是找到该簇后，取其中任意一个元素，执行“扩充”时的相反方法，就得到了解码结果。

然而实际中，想找到它谈何容易（就是告诉你答案，你都得动态规划才能算出该簇的总似然得分，何谈遍历所有簇！）。

所以实际中才用贪心算法或者beam search 算法近似之。

前者即对每一个input 位置，算出 argmax(softmax(..)) 当做这个位置的解码结果，然后构建出总的 output 序列，然后对 ε 分隔的重复字符作去重从而得到最终结果。

后者改进前者，但是和 CTC 的真正解码方式比，其实还是差的很远——只是对于训得好的 model，这样解码的结果和真正 CTC 解码结果差不太多而已（CTC 已经把绝大部分概率值给了某一个 alignment 了）。beam search 可以对当前所见作 bean，也可以对解码前缀作 beam。详见  https://distill.pub/2017/ctc/ 。

#### 怎么结合语言模型解码

另还据该文，CTC 解码可以结合语言模型（CTC解码概率P(Y|X) 乘LM概率 P(Y) 作为候选结果的score; 而 L(Y) 含义见该文； $\alpha, \beta$ 是权重调节因子）：

![image](https://github.com/user-attachments/assets/3d27fc9b-2115-4813-a33f-64cf16a54068)

AI 给出的 CTC 解码怎么结合 language model： 

$$score = α ⋅ \log(P_{CTC}(Y)​) + β ⋅ \log(P_{LM}(Y)​)$$

， 和上面大同小异。

再仔细看下 CTC loss 所训出的 model 到底学了个啥：理想情况下，正是学会了 input 的 每个 step 在 output 字符集上的分类。如果数据集一开始就标注了这点，也就不用 CTC 了。鉴于此，解码时当然不是非要用 CTC 的理想解码方式了。


### 参考
- https://distill.pub/2017/ctc/ （很好）
- https://ogunlao.github.io/blog/2020/07/17/breaking-down-ctc-loss.html
- http://www.cs.toronto.edu/~graves/arabic_ocr_chapter.pdf （这个讲得很好）
- http://m.blog.csdn.net/article/details?id=48526479
- https://zhuanlan.zhihu.com/p/21344595
- http://blog.csdn.net/xmdxcsj/article/details/51763886 系列

---

# transducer

见这里 https://lorenlugosch.github.io/posts/2020/11/transducer/ ， 简称 RNN-T 的模型，可以作 CTC 同样的事（自动对齐），但是不走 CTC 的方式。

![image](https://github.com/user-attachments/assets/47ece88c-b1b7-48f4-9443-6a37e9ba3361)

它的思路是先用 input encoder 把 input 的表示学出来， 而 predictor 相当于是 output 的 decoder，把这两者的表示 join 后，joiner 作 next_token 的预测：如果预测为有效输出字符，则拼给 output 作为 "output encoder" 输入，从而 output 加 1， input 不动。如果 joiner 预测为 null，则 output 不动，而 input 位置移动一格。如是或移input或移output，从而实现了动态自定对齐（有如 CTC）：

![image](https://github.com/user-attachments/assets/4349a7a9-30c9-46cf-85d5-4f5906bba865)

训练时，需要和 CTC 一样遍历所有的有效对齐路径，把所有对齐路径概率之和，当做 loss。为实现有效遍历，仍然要用动态规划。

transformer 后面固然也可以接 CTC。若用 transformer 的 cross-attention 实现的 encoder-decoder 模式（乃至更进一步 LLM 的纯 decoder 方式，把 input 作为 prompt 拼入），则 decode时，就不需什么 CTC 之类了。

---

# CIF

来自 2019.05 paper 《CIF: CONTINUOUS INTEGRATE-AND-FIRE FOR END-TO-END SPEECH RECOGNITION》， https://arxiv.org/pdf/1905.11235 。

假设是要做和 CTC 类似的某种事，比如语音识别从audio识别文字 tokens。那么 input 就是audio frames。那么判断每一个 frame 到底属于哪个被识别出的文字就是个问题——怎么对齐？CTC 的方法就是上面所讲那样。而 CIF 呢，则是预测单个 frame 属于一个token 的概率/权重/weight, 不用管到底属于哪个token。这样对于序列的所有 frame，都可以有这样的预测。

然后从左往右扫描weight，并作累加，每累加够一定阈值，比如 1，就认为是一个完整的 token 边界识别出来了（累加就是所谓的CONTINUOUS INTEGRATE=连续积分。而阈值达到，则是所谓的FIRE，而分界点，就是 fire point）。一直扫描到尾部，就识别出了所有的token 边界：还不知道有哪些文字，但是一共有多少字，以及每个字的位置，都是知道的了。扫描的时候，还要构建每个待识别 token 的 hidden 表示，方法也是累加：不过是带权求和，而权重正式求边界点的 weight。

一旦 token 的 hidden 表示有了，那么用它直接来做预测就可以了。 而 funASR 正是用的这样的思路。

![image](https://github.com/user-attachments/assets/8129a84a-41ea-4461-89c9-06a5f087c6c3)
