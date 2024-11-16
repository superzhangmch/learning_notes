# hash表与装载因子(loadfactor)

hash表的装载因子(load factor)指的是插入的key的数量与hash表的数组长度的比。一般取在0.6~0.8区间。为什么这样取值呢？

假设hash函数是足够随机的，比如用md5后取模。再假设hash长度是sz；那么插入一个元素命中hash的某个index的概率是 $\frac 1 {sz}$ ; 假设一个插入了n个元素，那么对于某个index来说，其正好有k个key的概率，服从二项分布【大概这样 $C(n, k) * p^k *(1-p)^{(n-k)}$ ；而且即使n很小比如只是几百；那么该分布也和泊松分布足够接近】。这样，我们就可以计算下不同的装载因子下，一个index有k个key的概率（或者说，有百分之多少的index正好有k个key）：
```
from scipy import stats
import sys
sz = 100001 if len(sys.argv) ＜ 2 else int(sys.argv[1])
factor = 0.75 if len(sys.argv) ＜ 3 else float(sys.argv[2])
p, N, tt = 1. / sz, int(sz *factor), 0
for i in xrange(11):
   bp, pp = stats.binom.pmf(i, N, p), stats.poisson.pmf(i, factor) # 用二项分布与泊松分布分别算下；此时泊松分布算是在近似二项分布
   tt += bp
   print i, 'binom_prob', bp, int(bp * sz), 'poisson_prob', pp, "accumulative_prob", tt
```

取hash长度为1亿，load_factor = 0.5:
```
0  binom_prob 0.6065    60653065 poisson_prob  0.6065   accumulative_prob  0.6065
1  binom_prob 0.3033    30326537 poisson_prob  0.3033   accumulative_prob  0.9098
2  binom_prob 0.0758    7581634  poisson_prob 0.0758    accumulative_prob  0.9856
3  binom_prob 0.0126    1263605  poisson_prob 0.0126    accumulative_prob  0.9982
4  binom_prob 0.0016    157950   poisson_prob  0.0016   accumulative_prob  0.9998
5  binom_prob 1.580e-04  15795    poisson_prob 1.580e-04  accumulative_prob 1.0
6  binom_prob 1.316e-05  1316    poisson_prob  1.316e-05 accumulative_prob  1.0
7  binom_prob 9.402e-07  94      poisson_prob  9.402e-07 accumulative_prob  1.0
8  binom_prob 5.876e-08  5       poisson_prob 5.876e-08  accumulative_prob 1.0
9  binom_prob 3.265e-09  0       poisson_prob 3.265e-09  accumulative_prob 1.0
10  binom_prob 1.632e-10  0       poisson_prob 1.632e-10  accumulative_prob 1.0
```
（第一列指某index正好有i个key；第四列指正好有i个key得index数量）


取hash长度为1亿，load_factor = 0.75:
```
0  binom_prob 0.4724    47236655 poisson_prob  0.4724   accumulative_prob 0.4724
1  binom_prob 0.3543    35427501 poisson_prob  0.3543   accumulative_prob  0.8266
2  binom_prob 0.1329    13285310 poisson_prob  0.1329   accumulative_prob  0.9595
3  binom_prob 0.0332    3321327  poisson_prob 0.0332    accumulative_prob  0.9927
4  binom_prob 0.0062    622748   poisson_prob  0.0062   accumulative_prob  0.9989
5  binom_prob 9.341e-04  93412    poisson_prob 9.341e-04  accumulative_prob 0.9999
6  binom_prob 1.168e-04  11676    poisson_prob 1.168e-04  accumulative_prob 1.0
7  binom_prob 1.251e-05  1251    poisson_prob  1.251e-05 accumulative_prob  1.0
8  binom_prob 1.173e-06  117     poisson_prob 1.173e-06  accumulative_prob 1.0
9  binom_prob 9.774e-08  9       poisson_prob 9.774e-08  accumulative_prob 1.0
10  binom_prob 7.330e-09  0       poisson_prob 7.330e-09  accumulative_prob 1.0
```

取hash长度为1亿，load_factor = 1.00:
```
0  binom_prob 0.3679    36787943 poisson_prob  0.3679   accumulative_prob  0.3679
1  binom_prob 0.3679    36787936 poisson_prob  0.3679   accumulative_prob  0.7358
2  binom_prob 0.1839    18393968 poisson_prob  0.1839   accumulative_prob  0.9197
3  binom_prob 0.0613    6131322  poisson_prob 0.0613    accumulative_prob  0.981
4  binom_prob 0.0153    1532830  poisson_prob 0.0153    accumulative_prob  0.9963
5  binom_prob 0.0031    306566   poisson_prob  0.0031   accumulative_prob  0.9994
6  binom_prob 5.109e-04  51094    poisson_prob 5.109e-04  accumulative_prob 0.9999
7  binom_prob 7.299e-05  7299    poisson_prob  7.299e-05 accumulative_prob  1.0
8  binom_prob 9.124e-06  912     poisson_prob 9.124e-06  accumulative_prob 1.0
9  binom_prob 1.014e-06  101     poisson_prob 1.014e-06  accumulative_prob 1.0
10  binom_prob 1.014e-07  10      poisson_prob  1.014e-07 accumulative_prob  1.0
```
（上面用1亿而不是1万，只是想看看大hash表下，能有多少index下key数量较多。但是即使用hash表长度=100，算出的概率值和以上也差不多大小——这是由二项分布的特性决定的）

可以看到，从查询效率上看，0.5~1.0之间几乎没差别。绝大部分index的key数量不超过三四个。所以只要hash函数足够好，hash查找时是不用担心链表法解决冲突时的性能问题的。

但是毕竟还是有少量的index下（但是是这么少，以至于1亿这么大的size下，超10个的数量都是个位数），可能key数量较多。于是有的hash表的实现（看网上比如java的hashMap），会在key数量超过x个后，由链表变成红黑树存储。但是，有些文章（比如 https://zhuanlan.zhihu.com/p/396019103 ）却是倒因为果，先由0.75的合理，倒推出重复key大于8个的概率极其低，然后说0.75合理。实际上，其他数字，这个概率也很低。

虽然 0.5\~1.0 之间查询效率差不多，hash的数组的元素占用率还是有差异的：1.0下有36%浪费；0.75有47%浪费；0.5有 60% 浪费。所以一般选择0.7左右，是在折中下空间占用而已。（note：这里只是说负载因子在某个范围内（比如 0.5\~1.0 ；这里只看了这个范围。显然太小浪费空间；太大则效率低下）查询效率差不多，不是任意值）

另外动态hash的实现，一般会在hash存满装载因子后开始扩容。然后有一种说法是，新插入一个元素发生hash冲突的概率为0.5的时候——也就是hash表空间正好用了一半的时候——就应该扩容了。由此可反解出对应的load factor是log(2) = 0.6931471805599453（见：https://www.zhihu.com/question/271137476 ）。这也是有道理的。
