rwkv 要多个版本迭代，其第一篇 paper https://arxiv.org/abs/2305.13048 《RWKV: Reinventing RNNs for the Transformer Era》，是 rwkv-v4 的。

一篇关于它综述： https://arxiv.org/pdf/2411.02795

rwkv 架构历史（来自其官网）： https://rwkv.cn/docs/RWKV-Wiki/RWKV-Architecture

----

这里重点看下它的 v4，也就是 https://arxiv.org/abs/2305.13048 。

### RWKV 名字由来

RWKV=Receptance Weighted Key Value。如下图有 R W K V 出现，所以叫 RWKV。K/V 类似于 transformer attn 中角色。 

<img width="1220" height="484" alt="image" src="https://github.com/user-attachments/assets/8ad57334-1ea2-4230-a591-c2ceeafd4635" />

### RWKV 结构啥样

如下图右，多个 rwkv block 上下 stack 后，底部是 token，顶部是 softmax，就可以作 transformer 那样的自回归语言模型了。

而每个 rwkv block 由两部分组成（下图左）： time-mixing 与 channel-mixing。
- time-mixing：对应 transformer 的 attention 部分，负责序列处理。说 rwkv 是 RNN，也是体现在这里：水平方向旧 hidden state 从它进，新 hidden state 从它出
- channel-mixing：对应 transformer 的 FFN 部分。这里有 W_1*act(W_2 x) 操作，带来了channel之间的信息mix，从而这样叫。

<img width="1208" height="1172" alt="image" src="https://github.com/user-attachments/assets/df6f4a25-2685-4a05-8efd-05441de2ea10" />

不考虑 token-shift 的 rwkv block 详情如下：

<img width="1328" height="1064" alt="image" src="https://github.com/user-attachments/assets/8a763bd0-a85d-44f1-a374-765e1fe7ccce" />

**channel-mixing：**

对 channel-mixing： 若定义激活函数 $\text{maxAct}(x) = max(x^2, 0)$, 则 channel-mix 中的 k'-v' 那一分支就是 

$$W'_v \cdot \text{maxAct}(W'_k \cdot x_t)$$

这和 FFN 的公式是一样的【 $\text{FFN}(x) = W_2 \cdot \phi(W_1 \cdot x) + b_2$，比如 $\text{FFN}(x) = W_2 \cdot \text{ReLU}(W_1 \cdot x)$ 】，所以说 channel-mix 算是 FFN。

**time-mixing：**

**（1）WKV_t 公式解释**
时间 t 时的 wkv_t 的原始公式是：

$$WKV_t = \frac{[\sum_{i=1}^{t-1} e^{-(t-1-i)w + k_i} \odot v_i] + e^{u + k_t} \odot v_t} {[\sum_{i=1}^{t-1} e^{-(t-1-i)w + k_i}] + e^{u + k_t}}$$

假设 hidden dim=d，即 kᵢ, vᵢ 都是d维向量。w, u 也都是 d 维可训练参数向量，他们每个维度对应 hidden dim 的一个维度。

上面 wkv 公式，kᵢ, vᵢ 是d维向量，则分母是 d 维向量，除法定义无意义。所以这个式子只是示意性的，表示每个维度怎么做的（逐维怎么做）。当然也可以把 kᵢ, vᵢ，w，u 重定义理解为就代表d个维度中的某一维度，则式子就数学上成立了。

wkv_t 计算中，以及 $\sigma(r_t)\odot wkv_t$ 中，都是维度独立进行的。这种方式，paper 中说是受了 AFT（attention-free-transformer）启发。

**（2）WKV_t 中 u 的作用**

若对当前位置 t 不想做特殊处理，也就是不需要用 u，则是这样更统一形式的 
$WKV1_t = \frac{\sum_{i=1}^{t} e^{-(t-1-i)w + k_i} \odot v_i} {\sum_{i=1}^{t-1} e^{-(t-1-i)w + k_i}}$

引入 u 的好处是, 按原文是：

> To circumvent any potential degradation of W, we introduce a vector U that separately attends to the current token

若不引入 u，即当前 token 也用通用的 $e^{-(t-1-i)w + k_i}$， 则把 i=t 代入 得到 $e^{w + k_i}$。也就是引入 u 只是代替了 w 而已。那么引入 u 就是为了特殊化处理当前 token 了。w 是用于所有历史时间步的，u 专用于当前 token。

**（3）相对位置**

式子中 $-(t-1-i)w$ 乃位置 t 与 i 的差的形式，起到的是相对位置编码的作用。若令 $a_{t,i} = -(t-1-i)w$, 则 $WKV2_t = \frac{\sum_{i=1}^{t} e^{a_{t,i} + k_i} \odot v_i} {\sum_{i=1}^{t-1} e^{a_{t,i} + k_i}}$，更容易看出它想干啥。

rwkv 是否需要位置编码：可以说 WKV_t 公式中的 $-(t-1-i)w$ 就是相对位置编码，所以不需要额外添加。

**（4）time-mixing 相当于每一维都做 attention**

关于 $\sigma(r_t)\odot wkv_t$： R 就相当于 attention 中的 Q。各维上独立操作的，假设就只一个维度，令 $q_t:= \sigma(r_t) \in \mathbb{R}$, 并用上面 $WKV2_t$ 形式，有 $\sigma(r_t)\cdot wkv_t = q_t \cdot wkv_t = \frac{\sum_{i=1}^{t} (q_t \cdot e^{a_{t,i} + k_i}) \cdot v_i} {\sum_{i=1}^{t-1} e^{a_{t,i} + k_i}}$, 这基本就是 attention 的 $\sum_j sim(q_i, k_j) v_j$ 形式了。所以 rwkv 的 time-mixing，约等于是每个维度上的 attention。

**token shift：**

rwkv block 的 time-mix 与 channel-mix 的 input，按说只用接收当前 token 即可。 rwkv 令它接收当前 token 和前一个 token 加权和。用来融合相邻位置的权重 $\mu$ 是与时间无关的可学习参数向量。

如下图，把 time-mix 与 channel-mix 的 input 都展开成了 token-shift：

<img width="1376" height="1128" alt="image" src="https://github.com/user-attachments/assets/c4abb863-3c57-473a-bbfb-feda0a48fcd4" />

如下图：

<img width="438" height="690" alt="image" src="https://github.com/user-attachments/assets/0d8c45fe-c52c-4528-b857-77aac8e9fdfe" />

具体自回归场景的例子：

<img width="1478" height="1064" alt="image" src="https://github.com/user-attachments/assets/4aac82fd-368d-4ce4-bff8-d6d180623c79" />

####


hidden state dim：
并行train：
