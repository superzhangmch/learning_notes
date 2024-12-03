# 黎曼 zeta 函数

下面为感性认识下黎曼 zeta 函数，感受下黎曼零点问题说了个啥。

----

黎曼 zeta (或 ζ) 函数，即 $\zeta(s) = \sum_{n=1}^{\infty} \frac 1 {n^s}$。

#### 1. 在 s=a+ib, a > 1, $b \in \mathbb{R}$ 时

易证它是收敛的。因为 

$$\frac 1 {n^s} = \frac 1 {n^{a+ib}} = \frac 1 {n^a} \exp^{(\log n) (-ib)} = \frac 1 {n^a} (\cos(-b \log n)+i \sin(-b \log n)).$$

#### 2. 在 a <= 1 时

按一般说法，它发散，所以才需要“解析延拓”(可延拓到只有s=1上没法定义)。单就此级数 $\sum_{n=1}^{\infty} \frac 1 {n^s}$ 而论，为啥就发散？发散则意味着 $\sum_n \frac 1 {n^a} \cos(b \log n)$, $\sum_n \frac 1 {n^a} \sin(b \log n)$ 发散，而为啥后者发散？

关于 zeta(s) 在 0 < real(s) < 1 的发散：
- 有一个[解释](https://math.stackexchange.com/questions/2700579/how-to-prove-the-divergence-of-zetas), 未察看究竟。
- 看这里：https://www.zhihu.com/question/5653967704
- 另据[here](https://math.stackexchange.com/questions/4144986/how-to-show-sum-1-ns-doesnt-converge-for-0-leq-res-leq-1?noredirect=1&lq=1), 由[Apostol的书11.6节](https://dl.icdst.org/pdfs/files1/ebc2974176a03ab93756026a97b6d370.pdf)，
> **Theorem 11.8** if the series $\sum \frac {f(n)}{n^s}$ converges for $s = \sigma_0 + i t_0$, then it also
> converges for all s with $\sigma > \sigma_0$. If it diverges for $s = \sigma_0 + i t_0$, then it
> diverges for all s with $\sigma < \sigma_0$. 【zeta(1)不收敛，从而不可能有 real(s) < 1 使得 zeta(s) 收敛】

其证明截图如下：

![image](https://github.com/user-attachments/assets/7eb7be5d-bbfc-4ad7-bf19-647a81ed12ed)


可以程序验证下，确实不太收敛的:

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

这是选了 zeta 函数第一个零点位置，确实算得可以（另外，这里没选用 s.real > 1， 但是欧拉麦克劳林公式也 work 得很好。多验证几个，都很好。所以为啥呢，[here](http://numbers.computation.free.fr/Constants/Miscellaneous/zetaevaluations.html)提到了成立条件）, 另外多处看到 euler-maclaurin其实正是zeta(s)的解析延拓，参[这里](https://math.stackexchange.com/questions/3159749/for-what-real-part-of-s-as-a-function-of-q-is-the-euler-maclaurin-formula-a), [这里](https://travorlzh.github.io/2020/12/26/bernoulli-polynomials.html)。

如果算 `calc(-1+0.0000001*1j)`, N=100时得出 `-0.08333333333332066-1.654211440989384e-08*1j`, 很接近 -1/12。这正是所谓自然数之和为 -1/12 的来源。

如果算 `calc(-1+0*1j)`, mpmath给出-1/12. 欧拉法给出NaN。

### 解析延拓
---

所谓解析延拓指的是，用 A 式子定义的函数，能解析的定义域区域是 D，用 B 式子定义的函数，解析的定义域是 D1，而 D 与 D1 的交集含有开集，则非交集部分即为对方的延拓。比如: $A=\sum x^n$, $B=1/(1-x)$, 它们定义域不同，但是有交集，后者为前者延拓。

延拓方式不一，下举几种。

#### 1. 对 0 < real(s) <= 1 的延拓

$\zeta(s) = \sum_{n=1}^{\infty} \frac 1 {n^s},\ \  real(s) > 1$  可以解析延拓到 0 < real(s) <=1 （注意 s=1 时，仍没法定义）：

$$\zeta(s) = \frac {1} {1 - 2^{1-s}} \eta(s) = \frac 1 {1 - 2^{1-s}} \sum_{n=1}^{\infty} \frac{(-1)^{n-1}}{n^s}.$$

为啥：η(s) := ∑交错 = ∑奇 - ∑偶 = (∑奇+∑偶) - 2∑偶， 而 ∑奇+∑偶=ζ(s), 且 $∑偶 = \sum_n \frac 1 {(2n)^s} = 2^{-s} \sum_n \frac 1 {n^s}=2^{-s} ζ(s)$，所以 $η(s) = ζ(s)-2 \cdot 2^{-s}ζ(s)$, 从而推出上式。

在 0 < real(s) <= 1 区间，ζ(s) 也差不多是交错的，为啥 η(s) 收敛，而 ζ(s) 发散？

根据[here](https://math.stackexchange.com/questions/2188438/proving-convergence-of-the-dirichlet-eta-function),  $n^s−(n+1)^s=s∫^{n+1}_n x^{−s−1}dx$, 令 s=a+bi， c=|s| 则 $|n^s−(n+1)^s| ≤ c ∫^{n+1}_n |x^{−s−1}|dx = c ∫^{n+1}_n |x^{−a−1}|dx ≤ c n^{−a−1} = c \frac 1 {n^{a+1}}$, 而 $\sum_n \frac 1 {n^{a+1}}$ 在 a > 0时是收敛的。

程序验证下：
```
import cmath
from mpmath import mp

def calc_zeta_by_eta(s, N=1000):
    def eta(s):
        r = 0
        for n in range(1, N, 1):
            r += 1. * (-1)**(n+1) / n **s
        return r
    return eta(s) / (1.-2**(1-s))

mp.dps = 10
for s in [0.5 + 14.134725141*1j, 0.5+1j, 2, 2.00001, 2.000001,  1+1j, 2+2j, 20+20j]:
    #x = get_zeta_val_by_int(s)
    x = calc_zeta_by_eta(s, 1000000)
    print ('calc', s, x)

    x1 = mp.zeta(s)
    print ('should_be', s, x1)
    print ('__')

```
output:
```
('calc', (0.5+14.134725141j), (0.000202381631061822-5.8421068595907595e-05j))
('should_be', (0.5+14.134725141j), mpc(real='9.161612314364e-11', imag='-5.754826484396e-10')) # match
__
('calc', (0.5+1j), (0.14339954678105482-0.7222224653614551j))
('should_be', (0.5+1j), mpc(real='0.1439364270773', imag='-0.7220997435288')) # match
__
('calc', 2, 1.6449340668491672)
('should_be', 2, mpf('1.644934066848')) # match
__
('calc', 2.00001, 1.6449246914661195)
('should_be', 2.00001, mpf('1.644924691471')) # match
__
('calc', 2.000001, 1.6449331293019531)
('should_be', 2.000001, mpf('1.644933129297')) # match
__
('calc', (1+1j), (0.5821574820565929-0.9268490203508495j))
('should_be', (1+1j), mpc(real='0.5821580597549', imag='-0.9268485643333')) # match
__
('calc', (2+2j), (0.867351829635518-0.275127238807934j))
('should_be', (2+2j), mpc(real='0.8673518296346', imag='-0.2751272388086')) # match
__
('calc', (20+20j), (1.000000257966888-9.180469499612744e-07j))
('should_be', (20+20j), mpc(real='1.000000257962', imag='-9.180469499534e-7')) # match
_
```
在 real(s) > 0 上，都匹配。看来确实是其延拓。

#### 2. 全复空间延拓

$\zeta(s) = \sum_{n=1}^{\infty} \frac 1 {n^s},\ \ real(s) > 1$ 可以解析延拓到除了 s=1 外的整个复空间(其中积分是围着正实轴： $+\infty \stackrel {实轴上方} {\rightarrow } 环绕原点0 \stackrel {实轴下方}{\rightarrow } +\infty$)：

$$zeta(s) = \frac {\Gamma(1-s)} {2 \pi i} \int_C \frac {(-z)^s} {(e^{z}-1) \cdot z} dz,\ \ \ s != 1$$

它在 real(s) <=1 一侧，除了 s=1 之外都有定义（在 real(s) > 1一侧，s 在整数点 gamma(1-s) 无定义，但这不属于延拓部分）。不管怎样推出的，实际计算验证下：

```
import cmath
from mpmath import mp
import numpy as np
from scipy.special import gamma

def do_path_int(f, arr_path):
    '''
    离散化计算下沿路径的复积分
    '''
    if type(arr_path) == type([]): arr_path = np.array(arr_path)
    
    integral = 0.0

    # Loop over each consecutive pair of points to form line segments
    for i in range(len(arr_path) - 1):
        z_start = arr_path[i]
        z_end = arr_path[i + 1]
        
        # Calculate the small change in z for each subdivision
        if abs(z_end.real-z_start.real) > 10 or  abs(z_end.imag-z_start.imag) > 10:
            num_subdivisions = 100000
        else:
            num_subdivisions = 1000  # number of subdivisions per line segment
        dz = (z_end - z_start) / num_subdivisions
        
        # Sum up contributions from each sub-segment
        last_v = None
        for j in range(num_subdivisions):
            z0 = z_start + j * dz
            z1 = z_start + (j + 1) * dz
            
            # Approximate integral over the small segment by trapezoidal rule
            v = 0
            try:
                f1, f2 = f(z0), f(z1)
                if f1 is None or f2 is None:
                    v = last_v
                    if v is None:
                        print ('aaaavvvv', i, j, z0, z1, f1, f2)
                else:
                    v = 0.5 * (f1 + f2) * dz
                    last_v = v
            except:
                v = last_v
                print ('bbb', v)
            integral +=v

    return integral

def get_zeta_val_by_int(s):
    def f_int(z):
        try:
            ret = (-z)**s / (cmath.exp(z)-1) / z
            return ret
        except:
            print ('aaaa', z)
            return None
    x = do_path_int(f_int, [500.+1j, -.1 + 1j, -0.1-1j, 500.-1j]) # 用 500 当做 infity
    # 路径积分。从实轴下方的500+1j到上方500-1j之间不需要路径积分 
    zeta_s = gamma(1-s) / (2*cmath.pi*1j) * x 
    return zeta_s

mp.dps = 10
for s in [0.5 + 14.134725141*1j, 2, 2.00001, 2.000001,  1+1j, -2-2j, 2+2j, -20+20j]:
    x = get_zeta_val_by_int(s)
    print ('calc', s, x)

    x1 = mp.zeta(s)
    print ('should_be', s, x1)
    print ('__')

```
output:
```
('calc', (0.5+14.134725141j), (-1.589580733999144e-06+3.1161849872000368e-06j))
('should_be', (0.5+14.134725141j), mpc(real='9.161612314364e-11', imag='-5.754826484396e-10')) # match
__
macll.py:99: RuntimeWarning: invalid value encountered in divide
  zeta_s = gamma(1-s) / (2*cmath.pi*1j) * x
('calc', 2, (nan+nanj))  # 无定义
('should_be', 2, mpf('1.644934066848')) 
__
('calc', 2.00001, (1.6581786099366211+3.665468959566902e-10j))
('should_be', 2.00001, mpf('1.644924691471')) # 基本match
__
('should_be', 2.000001, (1.777473800519907+3.9043379294062815e-09j))
('calc', 2.000001, mpf('1.644933129297')) # 不大match。大概只是误差导致
__
('calc', (1+1j), (0.5821575680493829-0.9268478056954552j))
('should_be', (1+1j), mpc(real='0.5821580597549', imag='-0.9268485643333')) # match
__
('calc', (-2-2j), (0.08635155276513681-0.020543236862247207j))
('should_be', (-2-2j), mpc(real='0.08638207303284', imag='-0.02053604281696')) # match
__
('calc', (2+2j), (0.8673519647118549-0.2751268457031929j))
('should_be', (2+2j), mpc(real='0.8673518296346', imag='-0.2751272388086')) # match
__
('calc', (-20+20j), (7.014837841351859e+22-1.2214195900731435e+23j)) 
('should_be', (-20+20j), mpc(real='295261595076.0', imag='167640361564.0')) # bad。大概是数值积分不准的缘故
```

两者大体是匹配的。在 real(s) > 1 一侧两者相等所以它确实是原始形式的解析延拓。

不过如果 s 模长稍为过大（几十之后），则算出的差别很大，乃数值积分不准的问题。

#### 3. 关于 zeta(s) 的 functional equation

对于延拓后能覆盖 real(s) > 0 的延拓，可以推得 $$\zeta(s) = 2^s \pi^{s-1}\sin\left(\pi s\over 2 \right) \Gamma(1-s) \zeta(1-s)$$，从而再次延拓到全空间。

如果定义 $ξ(s)=\frac {s(s-1)} 2 \pi^{−\frac s 2}\Gamma (\frac s 2)ζ(s)$，则上式可以简化成 $ξ(s)=ξ(1−s)$。可证 ξ(s) 的零点和 zeta(s) 的非平凡零点重合，且 ξ(s) 在 s.real=1/2 时是实函数，从而研究 ξ(s) 更方便。

为啥 ξ(1/2+it) $\in \mathbb{R}$：
- 由 ξ(s) 的定义有 $\overline {ξ(s)}=ξ(\overline s)$。需对 s(s-1)、 $\pi^{−\frac s 2}$、 $\Gamma (\frac s 2)$、 ζ(s) 逐项考察，他们都满足 $\overline {f(s)}=f(\overline s)$，再注意 $\overline {ab} = \overline a \overline b$。
- $s=1-s=\overline s$ 而 $ξ(s)=ξ(1−s)$, 故 $ξ(\overline s) =ξ(s)$
- 从而 $\overline {ξ(s)} = ξ(s)$，故 ξ(1/2+it) 为实的。



### 零点
---

仍然感性感受下 zeta(s) 在 s.real=0.5 时的零点（而由 $\zeta(s) = 2^s \pi^{s-1}\sin\left(\pi s\over 2 \right) \Gamma(1-s) \zeta(1-s)$ 可以得到平凡零点：s=2n, 即能满足 sin(.)=0的）。
承上代码，扫描下可能的零点（仅仅为感受下，就不考虑高级方法方法比如 Riemann-Siegel 公式了）：

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

### 其他
---

- http://numbers.computation.free.fr/Constants/Miscellaneous/zetaevaluations.html
- https://math.stackexchange.com/questions/3963153/why-is-the-riemann-zeta-function-defined-with-limits-when-0-s-1
- https://math.stackexchange.com/questions/4144986/how-to-show-sum-1-ns-doesnt-converge-for-0-leq-res-leq-1?noredirect=1&lq=1
- https://www.zhihu.com/question/421044878
- https://math.stackexchange.com/questions/2700579/how-to-prove-the-divergence-of-zetas
- https://www.asmeurer.com/blog/posts/verifying-the-riemann-hypothesis-with-sympy-and-mpmath/
- https://math.stackexchange.com/questions/4144986/how-to-show-sum-1-ns-doesnt-converge-for-0-leq-res-leq-1?noredirect=1&lq=1
- Dirichlet Eta 收敛：https://math.stackexchange.com/questions/2188438/proving-convergence-of-the-dirichlet-eta-function
- 为啥原始 zeta 函数不延拓则不收敛：https://www.zhihu.com/question/5653967704
- https://dl.icdst.org/pdfs/files1/ebc2974176a03ab93756026a97b6d370.pdf
