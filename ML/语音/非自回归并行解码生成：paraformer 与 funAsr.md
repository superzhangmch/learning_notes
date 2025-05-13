## CIF (CONTINUOUS INTEGRATE-AND-FIRE)
乃类似 CTC 作序列对齐的一种技术。paraformer/funAsr 基础就在于它。参 https://github.com/superzhangmch/learning_notes/blob/main/ML/%E7%90%86%E8%AE%BA/CTC%E3%80%81transducer%E3%80%81CIF.md#cif 

![image](https://github.com/user-attachments/assets/ebf189d7-5706-417b-ba9f-02d1cd68edae)

核心在于对于没有对齐的每一个frame，预测一个属于某一 token 的 weight $\alpha_i$ ，最终他会属于某个结果token，但是正巧只占据该token的比例是 $\alpha_i$. 若干个相邻的 weight 和达阈值的 frame 拼起来就是一个 token 的范围了。从左到右依次scan & integrate & fire，如果某个地方的token边界错位，那么会一路能导致余下的所有 token 都错位了。

---
## paraformer

### inference
![image](https://github.com/user-attachments/assets/6a18376c-685f-4ecd-a4c8-1cf6e266cbc7)

inference时，工作原理如上图。粗略地说，对于语音 frames：
- 先经标准 CIF 流程：得到文字token的边界点，以及每个待识别文字 token 的 hidden 表示。
- 然后一一对应识别具体 token 即可。

paraformer 特点在于第二步。根据第一步，一共能识别出多少字，已经知道了，每个字的表示也有了，最简单是根据表示来预测该token即可，都不需要 transformer。但是这样彻底忽视了前后文环境信息，更进一步是causal transformer。而  paraformer 用了双向 full-attn transformer。名字中的 para-，乃 parallel 的缩写，表示不像自回归transformer那样只能一个字一个字往外预测，它是可以并行一次预测所有字(鉴于有full attn, 所以是并行但不独立)。

### train

![image](https://github.com/user-attachments/assets/49e58d87-3356-46e4-b834-b50491c38cae)

在某一个 train step，先 inference 一步，看看和 ground  truth 的差异：根据差异率把 CIF 的 embds 中的一些随机替换成 ground-truth token 的 embds。差异率越大，替换的越多。替换后做预测计算loss，而第一次的预测并不用于梯度回传。

这样容易最终学到 output tokens 之间的依赖关系。infer 时流程只需要 pass-1。

这样分两步的训练方式，正如 paraformer 文中指出，来自 https://arxiv.org/pdf/2008.07905 《Glancing Transformer for Non-Autoregressive Neural Machine Translation》。只是那里是翻译问题（但也是要非自回归并行解码），二者手法如出一辙：

![image](https://github.com/user-attachments/assets/11d48860-62df-4ed9-a408-ff3167fe4a46)

该机制叫 GLM=glancing language model。之所以叫 glancing，指的是在训练遇到困难的时候，偷看下答案。训练后期效果较好后，偷看的也就更少。

为啥work：
(1). 按原文：
> Generally, GLM is quite similar to curriculum learning (Bengio et al., 2009) in spirit, namely first learning to generate some fragments and gradually moving to learn the whole sentences (from easy to hard). 

(2). 在训练的早期，预测的基本都不对，这时候，encoder output embeddings 绝大部分被替换，这时候的训练，就约等于是在训练一个双向 transformer 语言模型。把 encoder output embds 与 target token embds 能互换，说明是把他们等价看待的, 隐式地把两者视为了“在某种语义空间中等价可交换的表示”。这种操作迫使模型把 acoustic 表达和语义 token embedding 对齐到某个“共享空间”中。

(3). 训练中 decoder 的输入中，有些来自 acoustic（预测的），有些是“偷看的” ground-truth（embedding lookup）。decoder 要做到：不管来源是哪种，它都要能利用这些 embedding 来建模 token 之间的上下文关系并生成正确的输出。

---

## funASR

![image](https://github.com/user-attachments/assets/a08e6216-165b-4dcc-9a5e-56ee8ad5e276)

《funASR》主要是《paraformer》基础上的改进。新增了时间戳（每个字在原始audio中的时间offset）预测，支持用户自定义词，支持加标点等后处理。

**loss 变动**: 去掉了 MWER loss，对 pass-1 也变得计算梯度（pass-1 结果接 CE-loss）.

**hotwords**: 对 hotwords 处理获得 embedding 后给到 decoder 参与 cross attn。不过要decoder内部要独立分支处理之。

**后处理**: 作为序列标注问题。(图中 B-RM，I-RM，E-RM 正是model的指示信息)

![image](https://github.com/user-attachments/assets/0a5b71cf-6327-469c-a97f-1a81052f4702)

---
### 相关 paper
- https://arxiv.org/pdf/2305.11013 《FunASR: A Fundamental End-to-End Speech Recognition Toolkit》
- https://arxiv.org/pdf/2206.08317 《Paraformer: Fast and Accurate Parallel Transformer for Non-autoregressive End-to-End Speech Recognition》
- https://arxiv.org/pdf/2301.12343 《Achieving Timestamp Prediction While Recognizing with Non-Autoregressive End-to-End ASR Model》--funasr 团队一前作
- https://arxiv.org/pdf/1905.11235 《CIF: CONTINUOUS INTEGRATE-AND-FIRE FOR END-TO-END SPEECH RECOGNITION》

