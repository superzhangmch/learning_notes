# libsvm: 内部怎样实现多分类

一句话：libsvm 用的 one-versus-one 方法实现的多分类：假设分为K类，则每两类样本之间训练一个svm，总共训练K*(K-1)/2个。

除此外，还有 one-versus-rest 等方法构建（这时候需要构建K个SVM）等别的方式。

参见：
- http://blog.csdn.net/inter_xuxing/article/details/7619242
- http://blog.sina.com.cn/s/blog_5eef0840010147pa.html
