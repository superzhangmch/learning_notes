# 黎曼 zeta 函数

黎曼 zeta (或 ζ) 函数，即 $\zeta(s) = \sum_{n=1}^{\infty} \frac 1 {n^s}$。

#### 1. 在 s=a+ib, a > 1, $b \in \mathbb{R}$ 时

易证它是收敛的。因为 

$$\frac 1 {n^s} = \frac 1 {n^{a+ib}} = \frac 1 {n^a} \exp^{(\log n) (-ib)} = \frac 1 {n^a} (\cos(-b \log n)+i \sin(-b \log n)).$$

#### 2. 在 a <= 1 时

按一般说法，它发散，所以才需要“解析延拓”。单就此级数论，为啥就发散？发散这意味着 $\sum_n \frac 1 {n^a} \cos(b \log n)$, $\sum_n \frac 1 {n^a} \sin(b \log n)$ 发散，而**为啥后者发散**？有一个[解释](https://math.stackexchange.com/questions/2700579/how-to-prove-the-divergence-of-zetas), 未察看究竟。

不过可以程序验证下，确实不太收敛的:

```
from mpmath import mp # 他可以高精度计算 zeta(s) 的值

def zeta_approximation(s, N=100):
    sum_terms = sum(1.0 / n**s for n in range(1, N+1))
    return sum_terms

mp.dps = 10
s = -0.1 + 49.773832478 * 1j  # Example complex number
s = 1 + 1.0 * 1j  # Example complex number
x = mp.zeta(s)
approx_zeta = zeta_approximation(s, N=1000000)
print 'appr', approx_zeta.real, "\t", approx_zeta.imag
print 'real', float(x.real), "\t", float(x.imag)

s = 0.5 + 1.0 * 1j
for N in [100, 1000, 10000, 100000, 1000000]:
    approx_zeta = zeta_approximation(s, N=N)
    print 'appr', approx_zeta.real, "\t", approx_zeta.imag

# 有解析延拓的 zeta(s) 的真实取值
mp.dps = 10
x = mp.zeta(s)
print 'should_be', float(x.real), "\t", float(x.imag)
```

输出：
```
appr -8.24344142357     2.44850303408
appr 25.2110006318      12.3943927543
appr -21.9209636088     -87.4027792214
appr -157.170356008     234.336644821
appr 885.569923597      -127.297062687
should_be 0.143936427077     -0.722099743529
```

### 求值
---

所以对 zeta(s), 只有 s > 1 时，才可按原始级数部分和逼近求值。

然而 $\sum_n 1/N^s$, s > 1 收敛较慢，可借助[欧拉-麦克劳林求和公式](https://en.wikipedia.org/wiki/Euler%E2%80%93Maclaurin_formula)——该公式擅长的正是级数求和，要么计算不收敛级数的部分和，要么加速慢收敛级数。对应到 zeta 函数，该公式形式为：

$$\sum_{k=1}^{n} \frac{1}{k^s} \sim \zeta(s) - \frac{1}{(s-1)n^{s-1}} + \frac{1}{2n^s} - \sum_{i=1}^{\infty} \frac{B_{2i}}{(2i)!} \frac{(s+2i-2)!}{(s-1)!n^{s+2i-1}}$$

从而 

$$\zeta(s) \sim \sum_{k=1}^{n} \frac{1}{k^s} + \frac{1}{(s-1)n^{s-1}} - \frac{1}{2n^s} + \sum_{i=1}^{\infty} \frac{B_{2i}}{(2i)!} \frac{(s+2i-2)!}{(s-1)!n^{s+2i-1}}$$

python2 代码验证之：
```
#encoding: gbk

from mpmath import mp
import numpy as np
from scipy.special import bernoulli
from scipy.special import loggamma as gammaln

def compute_expression(s, i):
    '''
    直接算阶乘/gamma 函数，要过大溢出。用 log 形式
    '''
    i = float(i)
    
    # Calculate the logarithm of the factorial terms
    log_numerator = gammaln(s + 2*i - 1)  # (s + 2*i - 2)!
    log_denominator = gammaln(2*i + 1) + gammaln(s)  # (2*i)! * (s-1)!
    
    # Compute the expression using the exponential of the difference
    result = np.exp(log_numerator - log_denominator)
    
    return result

def zeta_approximation(s, N=100):
    # Initial sum of the series
    sum_terms = sum(1.0 / n**s for n in range(1, N+1))
    
    # Calculate the correction term using Euler-Maclaurin formula
    correction = 1. / N**(s-1) / (s-1) - 0.5 * N**(-s)
    
    # Bernoulli numbers for the correction terms
    #B = bernoulli(2 * np.arange(1, 10)) # python3
    m = 50
    B = bernoulli(2*m) # bernoulli 数列奇数项取值为0
    
    # Add the Bernoulli correction terms
    correction1 = 0.
    for k in range(1, m+1):
        xxx = compute_expression(s, k)

        dd = 1. * B[2*k] / N**(s-1+2*k) * xxx
        if abs(dd.real) < 1e-20 and abs(dd.imag) < 1e-20: break # 动态决定为达一定精度，要用多少项
        print ('xx', k)
        correction1 += dd
    return sum_terms + correction + correction1

def calc(s):
    mp.dps = 10
    x = mp.zeta(s)
    for N in [100, 1000]:
        approx_zeta = zeta_approximation(s, N=N)
        print 'appr', approx_zeta.real, "\t", approx_zeta.imag
    print 'should_be', float(x.real), "\t", float(x.imag)

calc(0.5 + 14.134725141*1j)
```
output:
```
('xx', 1)
('xx', 2)
('xx', 3)
('xx', 4)
('xx', 5)
('xx', 6) # N=100，,只用了 6 项
appr 9.162109038032135e-11      -5.754777319825002e-10
('xx', 1)
('xx', 2) # N=1000, 只用了 2 项
appr 9.16337586146096e-11       -5.75611212710788e-10
should_be   9.16161231436e-11  -5.7548264844e-10
```
这是选了 zeta 函数第一个零点位置，确实算得可以（另外，这里没选用 s.real > 1， 但是欧拉麦克劳林公式也 work 得很好。多验证几个，都很好。所以**为啥呢**）。

如果算 `calc(-1+0.0000001*1j)`, N=100时得出 `-0.08333333333332066-1.654211440989384e-08*1j`, 很接近 -1/12。

如果算 `calc(-1+0*1j)`, mpmath给出-1/12. 欧拉法给出NaN。

### 零点
---

仍然感性感受下 zeta(s) 在 s.real=0.5 时的零点。承上代码，扫描下可能得零点：

```
fp = open("out.txt", "w") # 保存下来，画图看看
for i in range(1, 5000): 
    s = 0.5 + 0.01 * i * 1j
    x = mp.zeta(s)
    a, b = float(x.real), float(x.imag)
    c = (a*a+b*b)**.5

    x = zeta_approximation(s, N=100)
    a, b = float(x.real), float(x.imag)
    c1 = (a*a+b*b)**.5
    if i % 10 == 0:
        fp.write("%.3f\t%.3f\t%.3f\n" % (0.01*i, c, c1))
    if c <= 0.005 or c1 <= 0.005:
        print i*0.01, c, c1

```
output:
```
14.13 0.00374633835569 0.00374633835571
14.14 0.00418561897356 0.00418561897357
21.02 0.00231899011248 0.00231899011247
21.03 0.00904580966191 0.00904580966191
25.01 0.00117623010327 0.00117623010328
30.42 0.00636521715498 0.00636521715495
30.43 0.00667342072459 0.00667342072461
32.93 0.00698625096906 0.00698625096903
32.94 0.00683445171425 0.00683445171427
37.59 0.00739818950383 0.00739818950378
40.92 0.00190917286252 0.00190917286251
43.33 0.00537080960925 0.00537080960925
48.0 0.0080954125155 0.00809541251551
48.01 0.00758696882517 0.00758696882524
49.77 0.0054312352536 0.00543123525362
49.78 0.00876876309239 0.00876876309243
```
大概在 14.1, 21.02, 25.01, 30.43, 32.94, 37.59, 40.92, 43.33, 48.0, 49.77 的位置。而实际上前10个零点为（可见还是一致的）：

![image](https://github.com/user-attachments/assets/fe1e40de-3614-429a-8bed-48d1b9407529)

再把zeta(0.5+x*1j)的模长画出来（横坐标要除10），可清晰看出零点位置：

![image](https://github.com/user-attachments/assets/df4058c9-4520-425d-b45e-1b32cad833a6)

