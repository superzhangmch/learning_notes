# RNN BPTT 反向传播

BPTT = Backpropagation Through Time，沿着时间的反向传播。RNN 的训练即如此。

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
   $\frac{dLoss_t}{dS_k} = \frac{∂Loss_t}{∂S_t} * \frac{∂S_t}{∂S_k}= \frac{∂Loss_t}{∂S_t}  *\prod\limits_{i=t}^{k+1}\frac{∂S_i}{∂S_{i-1}}$ ，
   $S_i$ 是 $i$ 时刻的输出值， $S_{i-1}$ 是本时刻的输入值（也是前一时刻的输出值），这样 $t$ 时刻的 $Loss_t$ 把梯度传到 $k$ 时刻，就是通过每个时刻的 $\frac{∂S_i}{∂S_{i-1}}$ 传过去的。因为是乘积关系，所以容易出现梯度的传递发生爆炸或梯度消失。

### 简证
1.  $\frac{∂S_t}{∂S_i} =\prod\limits_{k=t}^{i+1}{\frac{∂f_k}{∂S_{k-1}}}$ ：是因为，当不考虑 $W$ 只看 $f(W, X)$ 中 $X$ 的偏导的时候， $S_i$ 就是个最经典的的多次递推嵌套复合函数：令 $g(X) = f(W, X)$ ,
    则 $S_i = g(g(g(..i个..g(S_0))$ , 当然可以把 $\frac{∂S_t}{∂S_k}$ 展开为长长的导数乘链。
2.  $\frac{dS_t}{dW} = \sum\limits^t_{i=1}{ \frac{∂S_t}{∂S_i} \frac{∂S_i}{∂W}}$  ： 对 $\frac{dS_t}{∂W}$ 展开后再用 $\frac{∂S_t}{∂S_i} =\prod\limits_{k=t}^{i+1}{\frac{∂f_k}{∂S_{k-1}}}$ 合并即可得到。
    展开 $\frac{dS_t}{dW} = \frac{∂S_t}{∂W} + \frac{∂S_t}{∂S_{t-1}} \frac{dS_{t-1}}{dW}$ , 这算是递推公式，全展开，再合并就得到了。
