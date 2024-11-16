# 加速 softmax计算：层次化softmax 与 NCE

《word2vec》即用到此作加速。特看怎么回事。

softmax 往往用于预测命中 n个 label 中每个的概率。如果只是算命中特定某个的概率，仍然需要对其余 n-1 个作计算，因为只有这样才能求和做分母把概率归一化。如果n很大，比如几十万、几百万，这是很大的一个计算开销。为了加速这个过程，有两种方法被发明出来：层次化softmax 与 NCE。

### 层次化softmax
----------------
层次化softmax是通过概率分解的方法，把softmax概率用另外的更低成本的方式计算得到。

假设S代表sample，{ $L_i | i=1...n$ } 是n个label。假设有一种分类：{ $C_j$ | j=1...m} 使得任意 $L_i$ 属于其中之一，不妨记为 $C_i$ 。那么概率 $p(L_i|s)$ 可以分解为： $p(L_i | S) = p(C_i | S) \cdot p(L_i | C_i,\ S)$ ，也就是属于 $L_i$ 的概率等于属于 $C_i$ 的概率乘以属于 $C_i$ 情况下属于 $L_i$ 的概率。

> [《Hierarchical Probabilistic Neural Network Language Model》](https://www.iro.umontreal.ca/~lisa/pointeurs/hierarchical-nnlm-aistats05.pdf)
>
> In (Goodman, 2001b) it is shown how to speed-up a maximum entropy class-based statistical language model by
> using the following idea. Instead of computing directly
> P(Y |X) (which involves normalization across all the values that Y can take), one defines a clustering partition for
> the Y (into the word classes C, such that there is a deterministic function c(.) mapping Y to C), so as to write
>
> $$P(Y = y|X = x) =$$
> $$P(Y = y|C = c(y), X)P(C = c(y)|X = x).$$

这意味着对softmax，可以对 $p(L_i|S)$ 作概率分解，来降低计算量。如果 n=10000，m=100，每个 $C_j$ 包含 100 个 $L_i$, 也就是构造一棵 100 叉树，那么这样分解后，为了归一化导致的计算量就由 10000 变成了 100 * 2，效率提高了50倍。如果对 $p(C_i|S)$ 继续作类似分解，那么就可以构造一种层次化树状的结构，使得 $p(C_i|S)$ 的计算复杂度进一步降低。极端情况，可以构造完全(满)二叉、三叉树，令这种计算的复杂度达到最低【note：平衡二叉树可以用sigmoid一步搞定搞走做分支还是右分支，所以二叉树是最优。如果把二叉当softmax来处理，则n足够大（百万级别）后，是三叉树更优。可以具体数值估算验证这点】。

以上来自文章([Hierarchical Probabilistic Neural Network Language Model](https://www.iro.umontreal.ca/~lisa/pointeurs/hierarchical-nnlm-aistats05.pdf))。

上述方式只需要把{ $L_i$, i=1...n} labels 适当组织成树状结构即可。怎样组织，一种方式是按语义，有关联的词，尽量放到同一个节点下。所以有用wordNet的。

后来有文章([Extensions of recurrent neural network language model](https://github.com/yihui-he/Natural-Language-Process/blob/master/Extensions%20of%20recurrent%20neural%20network%20language%20model.pdf))发现，其实按词频划分也是可以的，不同词频的划到同一个Class下。它只是划了两层，没有组织成二叉树。

然后在 word2vec 文章([Efficient Estimation of Word Representations in Vector Space](https://arxiv.org/abs/1301.3781))中，把两者结合了起来，按词频把labels划分组织成平衡二叉树——更进一步，组织成了哈夫曼树。这样，高频词拥有更短的树path，带来全局更小的计算开销。

以上方式训练，以及对单个label的预测都是神速；如果预测时要取softmax概率最大的，则并不能预测，而需要遍历取最大。

### NCE
-----
如果只是关心命中n个 label 中哪个的概率最大，不关心概率值具体取多少，那么可以用n个sigmoid分别对每个 label 作预测。对于命中的，努力预测为概率1，不命中的，努力预测为概率0。而不再努力预测每个label应该有的概率。对于one-hot情况，只需对1个预测1，其他的随机抽样若干个并努力预测概率0。
