
weNet 语音识别model，是 end2end 训练的——也就是不需要传统方式的先识别语音(类似拼音）再语音转文字。同时统一处理 batch 与 streaming。【end2end 这点，以及wenet 的设计，可参考 https://placebokkk.github.io/wenet/2021/06/04/asr-wenet-nn-1.html 。】

# weNet-V1 https://arxiv.org/pdf/2102.01547
loss: $L_{combined}(x, y) = λ\cdot L_{CTC}(x, y) + (1 − λ)\cdot L_{AED}(x, y)$ , x 是语音，y是识别出的文字。 AED=attention-based-encoder-decoder。loss 中有两项，这决定了可以有多种解码方式：
- AED 接龙方式生成 asr 结果
- CTC 解码得到结果。
- CTC 解码出topK，用 AED 来给 CTC 候选打分，选出top1。

![image](https://github.com/user-attachments/assets/1c815a7d-c5a2-48e9-8377-fdb9e21136c3)

实验证明，解码效果，AED > CTC, 但是 CTC+AED打分，比 AED 更好，所以采用了CTC+AED打分（分两步，名之为 U2）：

![image](https://github.com/user-attachments/assets/074c3eb9-7025-4f8b-a8a5-f5bf487d2fbd)

# weNet-v2 https://arxiv.org/pdf/2203.15455

相比 wenet-v1，transformer decoder 新增了 R2L=right2left，也就是用到了两个 decoder，从左往右，从右边往左两个方向都可用来优选 CTC 所给出的候选集。如下图：

![image](https://github.com/user-attachments/assets/e006f631-638d-411d-b8bf-e070ee3debdd)

### 关于 R2L decoder

语音是从左到右的，且 weNet 号称统一了流与批，那么 R2L 岂不与此矛盾？原因是，即使 L2R 也是在 CTC 完整结束后才开始的，这时候加一个 R2L 完全没问题。所谓streaming 设计，指的是 CTC 的流式。L2R或者R2L计算很快，耗时不多，就像是一种后处理一样，不会影响流式识别。

那么为啥要用 R2L encoder 呢？ https://bbs.csdn.net/topics/600486705 这里有讲。大约说因为：
1. transformer decoder验证 CTC 的候选时，整个语音已经拿到了，所以可以做双向的 attention 了（可以不只用 L2R decoder 了）。
2. 为了双向：一个方式是用 Bert，即单个 transformer 用双向 attention（而非三角attn mask矩阵）。但是 bert 实现方式是：随机把某些  token 换成 MASK 特殊 token，而不是作用于 attn mask 矩阵。这样一个batch内，只能部分token mask 掉（因此低效吗）。总之用bert的话，“会极大增加训练和解码时的计算量”。
3. 于是作者采用新增一个 decoder的方式。除了实现简单，还可以选择只开启一个decoder（同时 decoder 部分还能脱离CTC 解码，也算好处吧）。

### 解码干预

既然是端到端 asr model，那就是解出是啥算啥。如果只是用 transformer decoder，那真是没办法了。还好 weNet 的两阶段解码第一阶段是 CTC，它是可以被干预的。

实际上 CTC 解码，可以用一个语言模型 LM （文中所用为 n-gram）来加强，并用一个叫 CTC WFST beam search 的解码法。细节未深究。

此外，用户如果有自己的私有词表，WFST 正巧也能支持。对用户custom 词，实时创建出一种干预图，如下图这样作解码干预即可（）：

![image](https://github.com/user-attachments/assets/93625109-09ae-4003-894f-64d08295e6de)

落实到 CTC 解码 score的计算，是这样的：
![image](https://github.com/user-attachments/assets/93b3fbf6-b6e0-4c84-9e4a-7bbe6ce5a92c)

最终的解码流程：
![image](https://github.com/user-attachments/assets/907e8f25-e08c-4cf9-9a54-a08270cb5b5d)

# 其他

### 流式怎么支持的：dynamic chunk
用于加速CTC的解码。不用等语音完全结束才开始CTC解码，而是随着chunk推进就可以做 CTC 解码。CTC 全解完后，开始做 R2L/L2R 的 rescore 优选。而后者并非流式的。

一个 chunk 一般几百毫秒到一两秒。越大的chunk，asr 效果更好（但是实时性会降低）。

encoder 用的是 conformer / transformer，内部有 attention。为了适应chunk机制，training时就要sample 各种长度的chunk来训练。而且attention 也要分块做：chunk 内部，作全 attention，跨越不同的 chunk，则是causal attention。

decoder 也用到了 transformer，但是到它这步，已经见到了全部的序列，所以就不用管chunk的存在了。【weNet2中说：
> And then, the input is split into several chunks with the chosen chunk size. At last, the current chunk does bidirectional chunk-level attention to itself and **previous/following** chunks in **L2R/R2L** attention decoder respectively in training.

看代码，并没体现这一点。】


### VAD 怎么处理的？
wenet 内基于一些规则判断语音开始结束。

参： https://mp.weixin.qq.com/s?__biz=MzU2NjUwMTgxOQ==&mid=2247484024&idx=1&sn=12da2ee76347de4a18856274ba6ba61f&chksm=fcaacaaccbdd43ba6b3e996bbf1e2ac6d5f1b449dfd80fcaccfbbe0a240fa1668b931dbf4bd5&scene=21#wechat_redirect

### weNet 号称流与非流一致处理。怎么和现实情况对应的？
鉴于 wenet 是两阶段的：先ctc弄出多个候选，再用 transformer decoder 选择出最佳候选。而后者要求能看到所有语音，所以，所谓 dynamic chunk 能有助于流式处理，不过是说能降低其时延，也就是能令 CTC 快速流式进行。当ctc 快速进行时，当然可以让用户看到识别过程，但是最终识别结果仍然需要被处理的语音全处理完后才能拿到。

也就是，整体上仍然是一段一段的，并非流式。
