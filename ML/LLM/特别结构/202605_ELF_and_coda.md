下面 by ai. 暂时没整理

- ELF: 《ELF: Embedded Language Flows》 https://arxiv.org/abs/2605.10938 by he-kaiming
- cola: 《Continuous Latent Diffusion Language Model》 https://arxiv.org/abs/2605.06548 by 字节 

## 0. 起点:两条看起来很像的管道

**ELF**:`tokens → contextual embeddings → flow matching 去噪 → 最后一步 unembed → tokens`
没有独立 decoder,最后一个 time step 复用同一张去噪网络切到 decode 模式 + 一个 unembedding 矩阵 W。flow 全程在**和 token 对齐的、高维、未压缩的 embedding 空间**里跑。

**Cola DLM**:`tokens →(Text VAE encoder)latent z0 → flow 学 latent 的先验 →(独立 VAE decoder)→ tokens`
flow 不还原观测,而是建模一个**压缩、变分、低维(16~128)语义 latent** 的先验分布;一个独立的因果 decoder 负责把 latent 变回文字。

第一眼:形状几乎一样。于是开始逐点怀疑。

## 1. flow 训练时是在"还原 z"吗?

形式上像,本质不是。

- 机械层面:FM loss 确实回归"指向那个具体 z0 的速度",看着像还原。
- 本质层面:网络只看到带噪 `z_t` + 上下文,**看不到真正的 z0**;同一个噪点能来自无数个 z0,MSE 最优解是期望/条件分布。
- 聚合后,逐样本回归收敛成"把噪声搬到 latent 分布"的**边际/条件向量场** = 先验 `p(z0^(b)|z0^(<b))`。

> 结论:flow 学的是 **latent 的(条件)分布**,不是还原某个具体 z。这也是论文坚持叫 "prior transport" 而非 "reconstruction" 的原因。

## 2. 条件生成怎么做?像 text2img 那样注入吗?

不是 cross-attention,而是 **prefix / in-context 条件**:

1. prompt 经 VAE encoder 编成干净 latent `z^pre`;
2. 把 `z^pre` 钉在序列最前面当"历史",后续 response 块通过 **block-causal self-attention mask** attend 回去,逐块自回归地生成 latent;
3. VAE decoder 读 `z^pre` + 生成的 latent 块 → 文本。

> 本质上是把 AR LLM 的"前缀 prefill"搬到了 latent 空间,共用一条序列、一种模态、一套 self-attention(块内双向、块间因果)。能 KV-cache、能流式。

## 3. 一个关键自洽性问题:VAE 是逐 token 独立压缩吗?

不是独立,也不是双向,而是**严格因果(strictly causal)**。

我担心的是:如果 encoder 双向,prompt 的 latent 会随后文变化,那"单独编码 prompt 再拼接"就不自洽了。

论文正好用"causal VAE"堵掉了这个洞:**因果性保证前缀 latent 不依赖后文** ⇒ 单独编码 prompt 得到的 `z^pre` == 完整序列里那段前缀的 latent ⇒ 拼接/prefill 自洽 ⇒ 支持流式 + KV-cache。和 AR 的 KV-cache 同一个道理。

## 4. 那 VAE encoder 本质不就是一种 embedding 吗?

**是。而且 ELF 的 T5 encoder 也是。** 都是"带上下文、非查表"的 embedding。

所以"是不是 embedding"根本不是区别。真正不同的是**那个表示空间被施加了什么约束**:

| | ELF | Cola |
|---|---|---|
| 概率瓶颈 | 无(确定性、高维、无 KL) | 有(变分 + KL + 低维 + BERT mask) |
| ELBO 里的 `I(X;Z)` 压缩项 | 没有 | 有 |
| decoder | 近 1:1 线性 unembed | 真正的 one-to-many 生成式 decoder |
| latent 性质 | token 对齐的"可逆特征" | 有损的"语义码" |

> 把 Cola 的 KL→0、维度拉高、decoder 退化成线性,它就变回 ELF 了。两者在一条**连续谱**上。

## 5. 变长生成 / EOS / buffer 浪费

flow 本身没有"自然 EOS"。Cola 的办法:

- **块层面**:block-causal = 半自回归,能"决定要不要再生成下一块"(纯并行扩散做不到);
- **token 层面**:因果 decoder 在 token 空间吐 EOS/pad,作为真正的截断信号;
- 训练用**随机长度 + padding** 保证一致性。

浪费对比(一条"浪费 vs 并行"光谱):

| | buffer 粒度 | EOS 后浪费 |
|---|---|---|
| AR | 逐 token | 零 |
| Cola | 逐块(~16) | ≤ 1 个块的尾巴 |
| ELF / 纯并行扩散 | 整条序列 | 整条尾巴 |

## 6. 但是——block-wise AR 是正交的!

我意识到:**ELF 也能做 block-wise 自回归**(改个块因果掩码即可,业界早有 semi-AR / block diffusion)。

所以 block-AR、EOS、变长这些**全是正交的生成调度选择**,两边都能各自取舍,**不是 ELF/Cola 的分水岭**。我前面那张三行表的横轴其实是"生成粒度",不是模型身份。

进一步:条件生成的**模板也一样**——都是"在序列前面填 prompt 编码后的向量,后面从噪声去噪"。这是所有序列扩散 LM 的通用 inpainting 式条件。

## 7. 剥到最后:唯一的真区别

把 block-AR、EOS、条件模板全排除后,剩下的唯一不可互换的差异 = **生成模型的拓扑**:

> **ELF = 在"观测"上跑 flow(一层)。**
> **Cola = 在"latent 先验"上跑 flow + 独立 decoder(两层隐变量模型)。**

这正是图像世界里 **像素扩散 vs Latent Diffusion(Stable Diffusion)** 那条分界线,也是 DALL·E 2 "diffusion prior + decoder" 的同一手。形式化的把手:**有没有一个被真正边际掉的隐变量** `p(x)=∫ p(x|z)p(z)dz`,以及 ELBO 里那个压缩项 `I(X;Z)`。

诚实的一刀:这个差异在**图像**里是质变;在**文本**里、尤其 Cola 几乎不压缩时,两者**几乎收敛成同一条谱上的邻近点**。所以"从灵感看好像没区别"——这个判断站得住。

## 8. 作者本人的回应(印证)

Cola 一作在知乎说的,几乎和上面的结论重合:

- **"我们不是为了做 diffusion 而做 diffusion;diffusion/flow 只是建模 latent prior 的 solver。真正重要的是 representation。"** —— 主动把 diffusion 这层降级。
- ELF = 证明 "embedding-space flow 可以很强";Cola = 系统回答 "什么样的 latent space 值得建模、怎么用 flow 建模"。**不是优劣,是互补。**
- 强调 "连续" 本身不自动带来优势;token-aligned embedding 没真正改变状态空间假设。
- Cola 的 encoder 不是冻结,而是**受控地和 prior 共同演化**(stop-gradient + reference regularizer + BERT loss 防 latent collapse)。
- 反直觉发现:**压缩 latent 可能更好**(patch=2 在长度对齐的样本上反超 patch=1),劣势只来自边界错位;压缩还能缩短生成深度、提速。
- **Gen. PPL ≠ 生成质量**(低熵复读 PPL 反而低),所以更看下游任务。
- 长期野心:text/image/video 各自 encoder → 共享 block-causal MMDiT prior → 统一多模态。

## 9. 一句话总纲

> `language modeling ≠ next-token prediction only`
> 也许是 `semantic representation + continuous prior modeling + token realization`

ELF 和 Cola 在 diffusion 机制层面是同族;**唯一货真价实的分叉是"要不要一个显式的、可压缩的、能参与边缘化的 latent variable,以及如何学它"。** Cola 押的不是"更妙的生成机制",而是 **representation > diffusion**,并以此通向统一多模态。

---

*相关链接*
- Cola DLM: arxiv.org/abs/2605.06548 · blog: hongcanguo.github.io/posts/2026-cola-dlm.html
- ELF: arxiv.org/pdf/2605.10938
