# libsvm 

### 内部怎样实现多分类

一句话：libsvm 用的 one-versus-one 方法实现的多分类：假设分为K类，则每两类样本之间训练一个svm，总共训练K*(K-1)/2个。

除此外，还有 one-versus-rest 等方法构建（这时候需要构建K个SVM）等别的方式。

参见：
- http://blog.csdn.net/inter_xuxing/article/details/7619242
- http://blog.sina.com.cn/s/blog_5eef0840010147pa.html

### C-SVC与nu-SVC有什么区别

C-SVC代表C-Support Vector Classification。在C-SVC中，参数C是一个正则化参数，用于控制错误分类的惩罚。C值越大，模型对错误分类的惩罚就越大，这可能导致模型在训练数据上过拟合。相反，如果C值较小，模型可能对错误分类的惩罚不够，导致欠拟合。因此，C值的选择在模型的性能上起着决定性作用。C-SVC旨在通过找到一个最优的分类超平面来最大化间隔，同时控制错误分类的数量。

nu-SVC是另一种支持向量分类方法，由Schölkopf等人提出。在nu-SVC中，参数nu代替了C作为正则化参数。nu参数在0到1之间，直观上表示错误分类和支持向量的上限比例。nu的值越大，模型对错误分类的容忍度越高。nu-SVC的目标同样是找到一个最优的分类超平面，但是通过一个略有不同的优化问题来实现，这个问题综合考虑了分类的准确性和模型的复杂度。

C-SVC使用C作为正则化参数，而nu-SVC使用nu。

一般性的是C-SVC。nu-SVC 见: http://scikit-learn.org/stable/modules/svm.html#svm-mathematical-formulation

https://www.quora.com/What-is-the-difference-between-C-SVM-and-nu-SVM
- The nu-SVM was proposed by Scholkopf et al has the advantage of using a parameter nu for controlling the number of support vectors. The parameter C in the ordinary SVM formulation is replaced by a parameter nu which is bounded by 0 and 1. Earlier the parameter C could have taken any positive value, thus this additional bound is beneficial in implementation.
- The parameter nu represents the lower and upper bound on the number of examples that are support vectors and that lie on the wrong side of the hyperplane, respectively. 
- Now despite the new bound, the nu-SVM is comparatively difficult to optimize and often the runtime is not scalable as compared to C-SVM.

https://www.csie.ntu.edu.tw/~cjlin/libsvm/faq.html#f411：
- Q: What is the difference between nu-SVC and C-SVC? 
- Basically they are the same thing but with different parameters. The range of C is from zero to infinity but nu is always between [0,1]. A nice property of nu is that it is related to the ratio of support vectors and the ratio of the training error.
