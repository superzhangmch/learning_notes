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
- 可看这里：https://www.zhihu.com/question/5653967704
  - 据[here](https://math.stackexchange.com/questions/4144986/how-to-show-sum-1-ns-doesnt-converge-for-0-leq-res-leq-1?noredirect=1&lq=1), 由[Apostol的书11.6节](https://dl.icdst.org/pdfs/files1/ebc2974176a03ab93756026a97b6d370.pdf)，
> **Theorem 11.8** if the series $\sum \frac {f(n)}{n^s}$ converges for $s = \sigma_0 + i t_0$, then it also
> converges for all s with $\sigma > \sigma_0$. If it diverges for $s = \sigma_0 + i t_0$, then it
> diverges for all s with $\sigma < \sigma_0$. 【zeta(1)不收敛，从而不可能有 real(s) < 1 使得 zeta(s) 收敛】

其证明截图如下：

![image](https://github.com/user-attachments/assets/7eb7be5d-bbfc-4ad7-bf19-647a81ed12ed)


可以[程序](https://github.com/superzhangmch/riemann_zeta_some_scripts/blob/main/zeta_diverge_for_real_le1.py)验证下，确实不太收敛的:
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

所以对 zeta(s), 只有 real(s) > 1 时，才可按原始级数部分和逼近求值。

然而 $\sum_n 1/N^s$, s.real > 1 收敛较慢，可借助[欧拉-麦克劳林求和公式](https://en.wikipedia.org/wiki/Euler%E2%80%93Maclaurin_formula)——该公式擅长的正是级数求和，要么计算不收敛级数的部分和，要么加速慢收敛级数。对应到 zeta 函数，该公式形式为：

$$\sum_{k=1}^{n} \frac{1}{k^s} \sim \zeta(s) - \frac{1}{(s-1)n^{s-1}} + \frac{1}{2n^s} - \sum_{i=1}^{\infty} \frac{B_{2i}}{(2i)!} \frac{(s+2i-2)!}{(s-1)!n^{s+2i-1}}$$

从而 

$$\zeta(s) \sim \sum_{k=1}^{n} \frac{1}{k^s} + \frac{1}{(s-1)n^{s-1}} - \frac{1}{2n^s} + \sum_{i=1}^{\infty} \frac{B_{2i}}{(2i)!} \frac{(s+2i-2)!}{(s-1)!n^{s+2i-1}}$$

python [代码](https://github.com/superzhangmch/riemann_zeta_some_scripts/blob/main/zeta_using_euler_maclaurin_formula.py)验证之：
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

[程序](https://github.com/superzhangmch/riemann_zeta_some_scripts/blob/main/zeta_by_eta.py)验证下：
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

它在 real(s) <=1 一侧，除了 s=1 之外都有定义（在 real(s) > 1一侧，s 在整数点 gamma(1-s) 无定义，但这不属于延拓部分）。不管怎样推出的，实际[python 计算](https://github.com/superzhangmch/riemann_zeta_some_scripts/blob/main/zeta_by_int.py)验证下：
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
承上代码，扫描下可能的零点（仅仅为感受下。趋近0不代表就是0。得靠 ξ(1/2+it) $\in \mathbb{R}$ 在疑似点前后的正负号的变化说明存在零点）：

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


### 零点计数（虚部大于 0 的）
----

截止 T 的零点数量大约是 $\frac T {2\pi} \log \frac T {2\pi} - \frac T {2\pi}$。根据复分析理论，零点数量可以通过 $N(s) = \int_C \frac {\zeta'(s)} {\zeta(s)} ds$ 算出，其中 C 是围绕被统计区域的曲线。直接强力作数值积分来算，速度太慢。

代码承上：
```
def get_zeta_val_by_int(y1, y2):
    def f_int(z):
        return mpmath.zeta(z, derivative=1) / mp.zeta(z)
    x = do_path_int(f_int, [1+y1*1j, 1+y2*1j, 0+y2*1j, 0+y1*1j, 1+y1*1j])
    x = x / (2*3.14159265)
    return x
get_zeta_val_by_int(y1=10, y2=200)
```
把路径的切分点改少到1000， 算的结果为 `(-2.387988805e-6 + 79.00026278j)`，即79个零点。

但是那个号称是“估算”零点数的公式，其实特别特别的准(截止306亿以内，误差基本在1以内)， 数据来自[here](https://www.lmfdb.org/zeros/zeta/)：

|截止(T) | 实际零点数 | $\frac T {2\pi} \log \frac T {2\pi} - \frac T {2\pi}$ |
|----|----|----|
| 15.134725142 | 1 | -0.2911844017848635 |
| 22.022039639 | 2 | 0.8908330071384682 |
| 26.01085758 | 3 | 1.7413347116608353 |
| 31.424876126 | 4 | 3.0494822025336044 |
| 33.935061588 | 5 | 3.708127495799163 |
| 38.586178159 | 6 | 5.005167318537804 |
| 41.918719012 | 7 | 5.990106454581973 |
| 44.327073281 | 8 | 6.728363144935223 |
| 49.005150881 | 9 | 8.22095731956653 |
| 50.773832478 | 10 | 8.804180244548434 |
| 78.144840069 | 20 | 18.912992957149605 |
| 102.317851006 | 30 | 29.152433541433425 |
| 123.946829294 | 40 | 39.09793850391171 |
| 144.111845808 | 50 | 48.916137263669995 |
| 164.030709687 | 60 | 59.05705699868447 |
| 183.207078484 | 70 | 69.18509424463494 |
| 202.264751944 | 80 | 79.56758381426826 |
| 220.067596349 | 90 | 89.52552634071438 |
| 9878.782654004 | 10000 | 9999.975683899125 |
| 74921.827498994 | 100000 | 100000.02396720872 |
| 600270.677012445 | 1000000 | 1000000.5213654237 |
| 10000000 | 21136125 | 21136124.330718227 |
| 100000000 | 248008025 | 248008023.25115368 |
| 1000000000 | 2846548032 | 2846548031.951251 |
| 10000000000 | 32130158315 | 32130158313.90965 |
| 30610046000 | 103800788359 | 103800788357.75623 |

看 [zhihu:读懂黎曼猜想（6）——非平凡零点的分布](https://zhuanlan.zhihu.com/p/163513405)：对 $\int_C \frac {\xi'(s)} {\xi(s)} ds$ 作围道积分是可以直接求出 $\frac T {2\pi} \log \frac T {2\pi} - \frac T {2\pi}$ 的【不考虑平凡零点, ξ(s) 与 ζ(s) 零点重合。凭啥用前者而不是后者？】，因为，该文指出：

令围道为以 1/2 为对称轴的矩形，因 ξ(s) 关于 1/2 竖线对称，从而对它积分可以只考虑右边一半。 $\xi(s) = \frac{1}{2} s(s-1) \pi^{-s/2} \Gamma\left(\frac{s}{2}\right) \zeta(s)$, 于是取log拆开再取导数有：

$$\frac{\xi'}{\xi}(s) = \frac{d}{ds} \left[ \log \frac{s(s-1)}{2} \right] + \frac{d}{ds} \left[ \log \Gamma\left(\frac{s}{2}\right) - \frac{s}{2} \log \pi \right] + \frac{1}{2\pi i} \int_\Gamma \frac{\zeta'}{\zeta}(s) ds$$

而对展开中除了 ζ(s) 项的右半矩形（反“匚”形的路径）上的积分的结果是： $\frac{T}{2\pi} \log \frac{T}{2\pi} - \frac{T}{2\pi} + \frac{7}{8} + \mathcal{O}\left(\frac{1}{T}\right)$——注意这就是计数公式了。这意味着 $\int_{反“匚”} \frac {\zeta'(s)} {\zeta(s)} ds$ 的取值很小——实际上该文证实是 O(log(T)) 的。因为 $\int_{口} \frac {\zeta'(s)} {\zeta(s)} ds$ 是零点计数，而再右半路径上积分值很小，那么也意味着另一半路径“匚”上的积分 $\int_{匚} \frac {\zeta'(s)} {\zeta(s)} ds$ 值很大。

可代码验证下：
```
def get_zeta_val_by_int(y1, y2，tp=0):
    def f_int(z):
        return mpmath.zeta(z, derivative=1) / mp.zeta(z)
    # 三种路径
    if tp == 0: x = do_path_int(f_int, [1+y1*1j, 1+y2*1j, 0+y2*1j, 0+y1*1j, 1+y1*1j]) # 矩形框“口”上进行
    if tp == 1: x = do_path_int(f_int, [0.5+y1*1j, 1+y1*1j, 1+y2*1j, 0.5+y2*1j]) # 反“匚”上进行。总值很小
    if tp == 2: x = do_path_int(f_int, [0+y2*1j, 0+y1*1j]) # 比左半矩形“匚”还少掉两横的竖线上进行。它的值占据了整个封闭曲线积分的几乎全部。
    x = x / (2*3.14159265)
    return x
# 令积分路径的每个线段切分3000段，则
get_zeta_val_by_int(y1=10, y2=2000, 1) # (-0.2533675701 - 0.1320660197j), 只看虚部 < 1
get_zeta_val_by_int(y1=10, y2=2000, 2) # (-0.1291483142 + 1516.868159j), 只看虚部 1516 个零点。而实际是 1517 个.非常接近。完整左半矩形“匚”计算：则是(0.2533384046 + 1516.83671j)
```

### 零点与素数公式关系
----

黎曼研究 zeta(s), 目的是给出小于 x 的素数个数公式 $\pi(x)$。不同于别人的近似公式，他的公式是精确的：

$$\begin{align}
J(x) &= \text{Li}(x) - \sum_{Im(\rho)>0} [\text{Li}(x^{\rho}+\text{Li}(x^{1-\rho})] + \int_x^\infty \frac {dt} {t(t^2-1) \ln t} - \ln 2 \\
\pi(x) &= \sum_n \frac {\mu(n)} n J(x^{1/n}) \\
\end{align}$$

$\mu(n)$ 是莫比乌斯函数， { $\rho$ } 是按虚部大于 0 且升序的 zeta(s) 零点集合。

上式有一个近似形式， $\pi(x) ≈ \sum_{n=1}^\infty \frac {\mu(n)} n \cdot (Li(x^{1/n})-\sum_\rho [Li(x^{\frac {\rho} n})+]Li(x^{\frac {1-\rho} n})) - \frac 1 {\log(x)} + \frac 1 {\pi} \arctan(\frac {\pi} {\log(x)})$ 。

把求和项中只剩下 Li(.), 则： $\pi(x) ≈ \sum_{n=1}^\infty \frac {\mu(n)} n Li(x^{\frac 1 n}) = 1+\sum_{n=1} \frac {\log^n(x)} {n \cdot n! \cdot \zeta(n+1)}$.

而还有近似式： $\pi(x) ≈ Li(x)$, 以及 $\pi(x) ≈ \frac x {\ln(x)}$. 

把它们[代码](https://github.com/superzhangmch/riemann_zeta_some_scripts/blob/main/prime_count_using_riemann's_formula.py)【需要注意因 log 为多值函数 $Li(x^{\rho/n})$ 得用 $Ei[log(x) \frac {\rho} n]$ 才行】验证。比较下, 可以得到:

| 截止 | $\pi(x)$ | 精确公式 | 精确公式之近似 | $\sum_n \frac {\mu(n)} n Li(x^{\frac 1 n})$ | $1+\sum_n \frac {\log^n(x)} {n \cdot n! \cdot \zeta(n+1)}$ | Li(x)| $\frac x {\log(x)}$ |
|----|----|----|----|----|----|----|----|
|10e1|4|0|1|0|0|2|0|
|10e2|25|0|1|0|0|5|4|
|10e3|168|0|1|0|0|9|24|
|10e4|1229|0|0|3|3|17|144|
|10e5|9592|1|1|5|5|37|907|
|10e6|78498|4|4|29|29|129|6116|
|10e7|664579|7|7|88|88|339|44159|
|10e8|5761455|7|7|96|96|754|332774|
|10e9|50847534|16|16|79|79|1700|2592592|
|10e10|455052511|188|188|1828|1828|3103|20758030|
|10e11|4118054813|587|587|2319|2319|11587|169923160|
|10e12|37607912018|926|926|1476|1476|38262|1416705193|
|10e13|346065536839|1357|1357|5774|5774|108971|11992858452|
|10e14|3204941750802|26170|26170|19201|19201|314889|102838308636|
|10e15|29844570422669|30945|30945|73217|73217|1052618|891604962453|
|10e16|279238341033925|45410|45410|327052|327053|3214632|7804289844393|
|10e17|2623557157654233|323360|323360|598255|598253|7956590|68883734693928|
|10e18|24739954287740860|773152|773152|3501392|3501408|21949524|612483070893536|
|10e19|234057667276344607|3175041|3175041|23885089|23884993|99878497|5481624169369983|

可见 Riemann 的精确公式确实很准（如果用更多零点参与计算，可以更准）。

但是，对于不是特别巨大的数(10e17, 也不过1.34s)，竟然有算法（比如[github:primecount](https://github.com/kimwalisch/primecount)）直接快速求出 $\pi(x)$ 的精确值，可比上面 Riemann 精确公式要快多了。

### 再看基于 zeta(s) 零点的 Riemann 素数公式
----

#### (1). π(x) 的莫比乌斯展开

对 π(x), 本来就有下面的莫比乌斯展开成立：

$$\begin{cases}
\pi(x) &= Σ_{n=1}^\infty \frac {\mu(n)} n J(x^{1/n})\\
J(x) &= Σ_{n=1}^\infty \frac {π(x^{1/n})} n
\end{cases}$$

因为 $\pi(x^{\frac 1 n})$ 是小于 $x^{\frac 1 n}$ 的素数，所以 $x^{\frac 1 n} < 2$ 后, $\pi(x^{\frac 1 n}) = 0$，从而上面求和其实只有有限项。且 $\frac {\mu(n)} n J(x^{\frac 1 n})$ 逐项很快衰减, 比如 $\pi(10e8)$

|n| $\frac {\mu(n)} n J(x^{\frac 1 n})$ | 截止n: $\sum_{i=1}^n \frac {\mu(i)} i J(x^{\frac 1 i})$ |
|---|---|---|
| 1 | 5762113.053 | 5762113.053 |
| 2 | -623.549 | 5761489.504 |
| 3 | -32.223 | 5761457.281 |
| 4 | 0 | 5761457.281 |
| 5 | -2.923 | 5761454.358 |
| 6 | 1.597 | 5761455.955 |
| 7 | -1.048 | 5761454.908 |
| 8 | 0 | 5761454.908 |
| 9 | 0 | 5761454.908 |
| 10 | 0.350 | 5761455.258 |
| 11 | -0.318 | 5761454.940 |
| 12 | 0 | 5761454.940 |
| 13 | -0.192 | 5761454.747 |
| 14 | 0.143 | 5761454.890 |
| 15 | 0.133 | 5761455.023 |
| 16 | 0 | 5761455.023 |
| 17 | -0.059 | 5761454.965 |
| 18 | 0 | 5761454.965 |
| 19 | -0.053 | 5761454.912 |
| 20 | 0 | 5761454.912 |
| 21 | 0.048 | 5761454.960 |
| 22 | 0.045 | 5761455.005 |
| 23 | -0.043 | 5761454.962 |
| 24 | 0 | 5761454.962 |
| 25 | 0 | 5761454.962 |
| 26 | 0.038 | 5761455.000 (得到了最终值 $\pi(10e8)$ |
| 27 | 0 | 5761455.000|

$\pi(x) = \sum_{n=1}^\infty \frac {\mu(n)} n J(x^{\frac 1 n})$ 只有有限项，且有内外两重循环，把它展开一个个看，会发现第一项可不就是 π(x) 呗，也就是说该公式全展开后，第一项之外所有项的和是 0。所以用该公式算完后确实得到了 π(x) 的正确值，但其实第一项就偷偷算出它来了。后面的都是无用功装模作样而已。

#### (2). 黎曼 π(x) 公式和上面关系

对比 $\pi(x) = \sum_n \frac {\mu(n)} n J(x^{1/n})$, 其实可以证明，正有这里的 J(..) = 上面的 J(..)，或者说把它们放一起：

$$\begin{cases}
\pi(x) &= Σ_{n=1}^\infty \frac {\mu(n)} n J(x^{1/n})\\
J(x) &= Σ_{n=1}^\infty \frac {π(x^{1/n})} n = \text{Li}(x) - \sum_{Im(\rho)>0} [\text{Li}(x^{\rho}+\text{Li}(x^{1-\rho})] + \int_x^\infty \frac {dt} {t(t^2-1) \ln t} - \ln 2
\end{cases}$$

但要注意：riemann 的 π(x) 若只取有限项，则其实是关于x 的连续函数，若 x 正好是素数，则 π(x-ε) 比 π(x+ε) 会多1，从而 π(x) 取值会是 (π(x-ε)+π(x+ε))/2。这要求 π(x) 在素数点的取值要比实际多 1/2, 或者说令 π₀(x):=(根据x是否素数，取值π(x) 或 π(x)+1/2), 黎曼的素数计数公式其实是在拟合这个 π₀(x)。好在在这样的 π₀(x) 下，上面的莫比乌斯展开依然成立： $π_0(x) = Σ_{n=1}^\infty \frac {\mu(n)} n J(x^{1/n}), where \ J(x) = Σ_{n=1}^\infty \frac {π_0(x^{1/n})} n$。所以所有提到 π(x) 的地方，其实应该是 π₀(x).

于是为了用基于 zeta(s) 零点的 Riemann 公式算 π(x), 其实也只需作有限项，且这有限项里，除了开头几项，后面的可以直接拿 $J(x) = Σ_{n=1}^\infty \frac {π(x^{1/n})} n$ 精准算出（这些项急速衰减，展开后涉及到的 π(x^..) 值都很小）。

对应[代码](https://github.com/superzhangmch/riemann_zeta_some_scripts/blob/main/prime_count_using_mobius.py)，及[代码](https://github.com/superzhangmch/riemann_zeta_some_scripts/blob/main/prime_count_using_riemann's_formula_more.py)。

关于x是素数点的时候，π(x) 比实际多 0.5：
```
# 格式：final x=.. pi(x)=..
final 10.91 4.05953855431767345341642006770
final 10.92 4.02655991632880922043871734252
final 10.93 4.01621566679161013402879426265
final 10.94 4.05364134240102155821970003118
final 10.950000000000001 4.09198809579432206244871397389
final 10.96 4.06269723723855446042369385490
final 10.97 3.98191720048856569216097034726
final 10.98 3.97687469811888973049545511214 # ≈ 4.5
final 10.99 4.17214642872205023461860461143
final 11.0 4.54597763431172957569677638665 # x=11 乃素数点, ≈ 4.5
final 11.01 4.92214452818260576921324313292
final 11.02 5.12126574225224918394538107857 # ≈ 5
final 11.03 5.11605492458871283466779534596
final 11.040000000000001 5.03022809620685664366010637858
final 11.05 4.99622278297851396275403595503
final 11.06 5.03510238988078968973454756156
final 11.07 5.07653668094377145002207183379
final 11.08 5.06734181306185941916468589442
final 11.09 5.03035054090664112658063261497
```

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
