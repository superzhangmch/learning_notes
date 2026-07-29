$\dfrac{\ln|\sin\ n|}{n}\to 0\ (n\to\infty,\ n\in\mathbb{N})$

---

下面来自AI. 

这个结论**不是纯粹的分析事实，必须用到 $\pi$ 的丢番图性质**（ $\pi$ 不是 Liouville 数）。因为 $|\sin n|\le 1$ ， $\ln|\sin n|\le 0$ ，命题等价于

$$\forall \varepsilon>0,\ \ |\sin n|\ \ge\ e^{-\varepsilon n}\quad(n \text{ 充分大}),$$

即 $n$ 不能"指数级地"接近 $\pi$ 的整数倍。这需要一个 $\pi$ 的有理逼近下界作为输入。

---

## 用到的算术输入

**Mahler 定理 (1953).** 存在绝对常数使得对一切整数 $p,q$ 且 $q\ge 2$ ：

$$\left|\pi-\frac{p}{q}\right| > \frac{1}{q^{42}}.$$

（即 $\pi$ 的无理性度量有限， $\mu(\pi)\le 42$。现在最好的结果是 Salikhov 2008： $\mu(\pi)<7.11$，可把下面的指数 $41$ 换成 $6.2$，不影响结论。）
 
## 证明

**第一步：化归为"到 $\pi\mathbb{Z}$ 的距离"。**

设 $n\ge 5$，取 $m=\left[\frac{n}{\pi}+\frac12\right]$ 为离 $n/\pi$ 最近的整数，记
$$\delta_n=|n-m\pi|\le \frac{\pi}{2}.$$
由 $n\ge 5$ 得 $n/\pi\ge 1.59$，故 $m\ge 2$；又由 $\pi$ 无理， $\delta_n>0$。

由 $\sin$ 的周期性与奇偶性， $|\sin n|=|\sin(n-m\pi)|$。而 $\sin$ 在 $[0,\pi/2]$ 上是凹函数，故 $\sin t\ge \frac{2}{\pi}t$ 对 $t\in[0,\pi/2]$ 成立，于是

$$|\sin n| \ge \frac{2}{\pi}\,\delta_n$$

**第二步：估计 $\delta_n$ 的下界。**

$$\delta_n=|n-m\pi|=m\left|\pi-\frac{n}{m}\right| \overset{\text{Mahler}}{>} m\cdot \frac{1}{m^{42}}=\frac{1}{m^{41}}.$$

又 $m\le \frac{n}{\pi}+\frac12\le n$（ $n\ge1$ 时成立），故
$$\delta_n>\frac{1}{n^{41}}. \tag{2}$$

**第三步：合并。**

由 (1)(2)，对一切 $n\ge5$：
$$1\ \ge\ |\sin n|\ >\ \frac{2}{\pi}\cdot n^{-41},$$
取对数：
$$0\ \ge\ \ln|\sin n|\ >\ -41\ln n-\ln\frac{\pi}{2}.$$

因此
$$\left|\frac{\ln|\sin n|}{n}\right|\ <\ \frac{41\ln n+\ln(\pi/2)}{n}\ \xrightarrow[n\to\infty]{}\ 0 .$$

$\blacksquare$

顺带得到等价形式： $|\sin n|^{1/n}\to 1$，以及更强的定量结论 $\ln|\sin n|=O(\log n)$。
 
## 为什么必须用算术输入

如果把整数序列 $n$ 换成 $\sin(n\pi\alpha)$，结论对某些 $\alpha$ **不成立**。用 Liouville 型构造取无理数 $\alpha$，使存在有理数列 $p_k/q_k$ 满足
$$\left|\alpha-\frac{p_k}{q_k}\right|<\frac{e^{-q_k^2}}{q_k},$$
（这样的 $\alpha$ 可由级数 $\sum_k 10^{-a_k}$ 递归构造）。则取 $n=q_k$：
$$|\sin(q_k\pi\alpha)|=|\sin(\pi(q_k\alpha-p_k))|\le \pi\,|q_k\alpha-p_k|< \pi e^{-q_k^2},$$
于是 $\frac{\ln|\sin(q_k\pi\alpha)|}{q_k}\le -q_k+O(1)\to-\infty$。

所以本题的真正内容就是"$\pi$ 不是 Liouville 数"这一非平凡事实；对 Lebesgue 几乎所有的实数 $\alpha$，由 Borel–Cantelli 可初等地得到 $\mu(\alpha)=2$，从而同样的论证给出 $\ln|\sin(n\pi\alpha)|=O(\log n)$——但"几乎所有"不包含具体的 $\pi$，故仍需引用 Mahler（或 Salikhov）的结果。
