# RNN BPTT 反向传播

BPTT = Backpropagation Through Time，沿着时间的反向传播。RNN 的训练即如此。

开宗明义，对于RNN，其反向传播算法，也就是所谓的BPTT——backpropagation through time——看似与非 RNN 的 BP 不同，其实本质还是一样的，仍然就是数学上的函数求偏导数。

对 RNN： 

$$
\begin{cases}
s_t = \tanh(U \cdot x_t+W \cdot s_{t-1})\\
y_t = softmax(V \cdot s_t)
\end{cases}
$$

, 训练就是要得到 U、V、W 的恰当取值。因为我们是用梯度下降的方法，这归结为对损失函数求关于 U、V、W 的梯度，然后据以 update。

RNN 对于序列输入 { $x_1, x_2, ..., x_n$ }, 会有序列输出 { $y_1, y_2, ..., x_n$ }。最后的损失函数 Loss 是把各个时间点 $y_t$ 的单个 $loss_t$ 加起来。根据导数的性质(和的导数等于导数的和)，可以化解成对每个 $loss_t$ 求导，最后加起来。因此问题归结于对于单个时间点处关于 U、V、W 的偏导数。

上面 RNN 中， $\frac {∂y_t}{∂V}$ 是好求的。 $\frac {∂s_t}{∂U}$ 和 $\frac {∂s_t}{∂W}$ 有些麻烦，因为是递推表达式。单从数学上， $\frac{∂s_t}{∂U}$ 和 $\frac {∂s_t}{∂W}$ 终究还是能求出来的（展开后求解）。RNN 之 BPTT 算法，其实也只是实现了数学上的这个 $\frac {∂s_t}{∂U}$ 和 $\frac {∂s_t}{∂W}$ 的计算而已。所以其实也没特别的。唯一特别之处和一般 BP 一样，还是在于怎样高效求解。

推而广之，其实 BPTT 是在求解下面这样的递推函数的导数： 

--------

### 问题
假设有某二元函数 $f(W, X)$ 和 $S_0$ ,  递归定义 $S_t= f(W, S_{t-1})$。怎样求 $\frac{dS_t}{dW}$？

### 结论
为了免得记号导致的混乱，特别地，令：  
$\frac{∂S_t}{∂W}$ 为偏导数，表示不理会 $f$ 第二个参数（仿佛第二个参数 $S_{t-1}$ 与第一个参数 $W$ 独立）时关于W的偏导数，  
$\frac{dS_t}{dW}$ 为非偏导数，表示把 $S_t$ 展开后的关于 $W$ 的导数。  
则 $\frac{dS_t}{dW} = \sum\limits^t_{i=1}{ \frac{∂S_t}{∂S_i} \frac{∂S_i}{∂W}}$ , 且 $\frac{∂S_t}{∂S_i} =\prod\limits_{k=t}^{i+1}{\frac{∂f_k}{∂S_{k-1}}}$ ( $\frac{∂S_t}{∂S_i}$ 要求 $t>i$ ).

#### 解释
1. 注意在每个时间点 $i$ ， $\frac{∂S_i}{∂W}$ 是容易求得的（注意可以忽略 $f$ 第二个参数 $S_{i-1}$ 直接对 $W$ 求偏导，仿佛 $S_{i-1}$ 不依赖 $W$ 一样）,
   且 $\frac{∂S_i}{∂S_{i-1}}$ 也是容易求得的（忽略 $f$ 的第一个参数 $W$ 直接对 $S_{i-1}$ 求偏导后，把 $S_{i-1}$ 的值代入即可)。这样整个 $\frac{dS_t}{dW}$ 就可以求出来了。
   过程中有些 $\frac{∂S_i}{∂S_{i-1}}$ 需要算多次，可以只算一次把结果存下来。
2. 如果对应到 RNN 中， $t$ 时刻的 $Loss_t$ 传递到 $k$ 时刻后的值，
   $\frac{dLoss_t}{dS_k} = \frac{∂Loss_t}{∂S_t} \frac{∂S_t}{∂S_k}= \frac{∂Loss_t}{∂S_t} \prod\limits_{i=t}^{k+1}\frac{∂S_i}{∂S_{i-1}}$ ，
   $S_i$ 是 $i$ 时刻的输出值， $S_{i-1}$ 是本时刻的输入值（也是前一时刻的输出值），这样 $t$ 时刻的 $Loss_t$ 把梯度传到 $k$ 时刻，就是通过每个时刻的 $\frac{∂S_i}{∂S_{i-1}}$ 传过去的。因为是乘积关系，所以容易出现梯度的传递发生爆炸或梯度消失。

### 简证
1.  $\frac{∂S_t}{∂S_i} =\prod\limits_{k=t}^{i+1}{\frac{∂f_k}{∂S_{k-1}}}$ ：是因为，当不考虑 $W$ 只看 $f(W, X)$ 中 $X$ 的偏导的时候， $S_i$ 就是个最经典的的多次递推嵌套复合函数：令 $g(X) = f(W, X)$ ,
    则 $S_i = g(g(g(..i个..g(S_0))$ , 当然可以把 $\frac{∂S_t}{∂S_k}$ 展开为长长的导数乘链。
2.  $\frac{dS_t}{dW} = \sum\limits^t_{i=1}{ \frac{∂S_t}{∂S_i} \frac{∂S_i}{∂W}}$  ： 对 $\frac{dS_t}{∂W}$ 展开后再用 $\frac{∂S_t}{∂S_i} =\prod\limits_{k=t}^{i+1}{\frac{∂f_k}{∂S_{k-1}}}$ 合并即可得到。
    展开 $\frac{dS_t}{dW} = \frac{∂S_t}{∂W} + \frac{∂S_t}{∂S_{t-1}} \frac{dS_{t-1}}{dW}$ , 这算是递推公式，全展开，再合并就得到了。

--------

### 参看

这里里详细介绍了BPTT的算法: [Recurrent Neural Networks Tutorial, Part 3 – Backpropagation Through Time and Vanishing Gradients](https://dennybritz.com/posts/wildml/recurrent-neural-networks-tutorial-part-3/)

其中的公式，正和上面一致。

![image](https://github.com/user-attachments/assets/abf1deda-f0d0-46f6-886c-015aee235be3)


如上图，也来自那篇文章。红线是梯度沿时间的传递。

BP/BPTT算法常有梯度/误差传递的说法。一旦说到一个东西沿一条线依次传过去，容易让人觉得要么是原封不动地从头传到尾，要么是边传边被割走一块或附加一块（以“加减法”的方式），变得更大或更小。实际上，传递来的梯度/误差，是以“乘法”方式进行的——这也是链式求导导致的——它会乘以本处算出的梯度。在BPTT中也不例外。如图红色梯度传来后，作为乘法因子起作用。正因此，才导致了梯度爆炸或梯度消失。
 
上面文章里还有段BPTT的伪码。如下，第一循环表示格式时间点，第二处循环表示在该时间点处沿时间轴往前传播梯度。是个两层循环。一般BP算法只是一层循环。

```
def bptt(self, x, y):
    T = len(y)
    # Perform forward propagation
    o, s = self.forward_propagation(x)
    # We accumulate the gradients in these variables
    dLdU = np.zeros(self.U.shape)
    dLdV = np.zeros(self.V.shape)
    dLdW = np.zeros(self.W.shape)
    delta_o = o
    delta_o[np.arange(len(y)), y] -= 1.
    # For each output backwards...
    for t in np.arange(T)[::-1]:
        dLdV += np.outer(delta_o[t], s[t].T)
        # Initial delta calculation: dL/dz
        delta_t = self.V.T.dot(delta_o[t]) * (1 - (s[t] ** 2))
        # Backpropagation through time (for at most self.bptt_truncate steps)
        for bptt_step in np.arange(max(0, t-self.bptt_truncate), t+1)[::-1]:
            # print "Backpropagation step t=%d bptt step=%d " % (t, bptt_step)
            # Add to gradients at each previous step
            dLdW += np.outer(delta_t, s[bptt_step-1])              
            dLdU[:,x[bptt_step]] += delta_t
            # Update delta for next step dL/dz at t-1
            delta_t = self.W.T.dot(delta_t) * (1 - s[bptt_step-1] ** 2)
    return [dLdU, dLdV, dLdW]
```
那么的话RNN之类都是需要特别用代码来实现反向传播的了。那么各个框架是怎么实现的呢？

特意查看经看tensorflow，并没有发现对RNN有什么特意对待。只有RNN cell的网络定义。看来tf用自身的机制自动做到了BPTT。

特意写一段 tf v1 有递推定义的代码：
```
import tensorflow as tf
sess = tf.Session()
w = tf.Variable(2.)
def f(input):
    return (1. + w * input) ** 2
y = f(f(f(f(1.))))
sess.run(tf.global_variables_initializer())
print sess.run(tf.gradients(y, w))
```

得到了正确的梯度值12926834988414。另外对于多层嵌套的RNN，以及双层逆向的RNN，其BPTT怎么实现的呢？后来查询得知，tensorflow用到了一种叫做自动微分的技术。在该技术下，没有什么BP与BPTT的区分了。全都一招搞定。
