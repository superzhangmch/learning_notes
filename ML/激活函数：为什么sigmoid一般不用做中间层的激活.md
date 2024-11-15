# 为什么sigmoid一般不用做中间层的激活 

对一个神经元 $f(\sum_i [w_i x_i+b_i])$ , 如果所有 $x_i$ 总是正的，令 $y=\sum_i [w_i*x_i+b_i]$ ，那么
 $\frac {df}{dw_i} = \frac {df}{dy} \frac {dy}{dw_i} = \frac {df}{dy} x_i$
 
在一次具体的反向传播中， $\frac {df}{dy}$ 的符号是确定的，而 $x_i$ 总是正的，那么对所有的 i， $\frac {df}{dw_i}$ 的正负号都是一样的。这样对 { $w_i$ } 参数的梯度更新方向是多样性不足的。当然对训练不利。

如果sigmoid用作中间层的激活，那就导致下一层的输入都是正的。因此一般中间层激活函数不选用sigmoid。

【参】
http://cs231n.stanford.edu/slides/2017/cs231n_2017_lecture6.pdf 第21页。

