# SVM 与核函数

线性 SVM 如果用纯数学的角度去理解，则是再自然不过了，就是在高维空间插入一个高维板子把两种label的数据，一分为二。其技巧只是在于怎么恰当地找板子。

<br>

如果平直的板子没法把数据区分开，则可以把板子扭曲从而分开。但是从另一个角度，也可以保持板子不变，而扭曲数据。对数据作变换，使得平板子继续可以切分数据。

这就是所谓的核技巧的想法。

很显然很自然的想法。实际上，SVM 核技巧比这个走得更远一步。它只是相当于有那么一个映射对数据做了变换，但是具体操作上却不关心到底这个映射长什么样，而是直接跳过去了。具体来说，它只需明确映射前后的内积变化：只要知道 inner_product(x1, x2) ==> inner_product(f(x1), f(x2)) 就可以了, 不用知道 f 是什么。当然，之所以可以这样，是与 SVM 的优化特性有关的，就不细究了。

所以说，SVM 的核函数只是数据重新映射的想法，但不代表就是该映射。

<br>

既然核函数背后有映射，那么这个映射是唯一的吗？答案是不唯一。且这个映射往往会对原始数据的维度作升维或降维。且同一个核函数，可能对应变换到不同维空间的多个映射。特别的，也可能背后的映射是映向无穷维空间的（比如高斯核）。http://blog.csdn.net/leonis_v/article/details/50688766 ，http://blog.csdn.net/lpsl1882/article/details/53529618

正由于核函数背后的映射可能把原空间映向很高甚至无穷维的空间，所以核化SVM才有非常强的分类能力。以前没太注意，把核函数误解为就是映射（还以为成了原空间内的映射）了，于是以为两个圆环这样的数据集，SVM很难区分。实际上，这对SVM当然是小意思了。

<br>

SVM 和 LR 一道可以说是最最典型的两种机器学习方法。大体上说，两者都是线性的分类器，也都可以用 tensorflow 等框架来实现，只需接不通的激活函数与 loss 函数。对于SVM，hinge loss 在框架不提供的情况下，可以自己用基本操作组合得到。

对于带核函数的非线性 SVM，则没那么容易。非线性核化SVM并没有（似乎也有，但我也不想深究，只就一般情形来说）hinge loss 那样的损失函数，而且其预测函数形式也没那么友好（线性 SVM 最终形式 w_i*x_i + b，只和样本特征数目有关），其最终表达形式会牵扯到所有训练样本，因此，如果想用 tensorflow 等来实现下，是没那么容易与自然的。

（网上有实现，但是没怎么看明白：http://blog.csdn.net/lpsl1882/article/details/55252067?winzoom=1

https://github.com/nfmcclure/tensorflow_cookbook/blob/master/04_Support_Vector_Machines/04_Working_with_Kernels/04_svm_kernels.py）

<br>

另外，实际上，非线性 SVM 在大数据的今天，其表现得也是很不力的。预测不方便，训练也慢。见：https://www.quora.com/Why-is-kernelized-SVM-much-slower-than-linear-SVM
