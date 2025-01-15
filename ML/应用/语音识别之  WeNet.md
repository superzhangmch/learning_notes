# 关于：语音识别之  WeNet

### R2L decoder
wenet 2.0 用了 U2++ 网络结构：也就是新增了一个 right2left（R2L) 的 decoder。从而从左往右，从右边往左两个方向都可用来优选 CTC 所给出的候选集。
那么为啥要用 R2L encoder 呢？ https://bbs.csdn.net/topics/600486705 这里有讲。大约说因为：
1. transformer decoder验证 CTC的候选时，整个语音已经拿到了，所以可以做双向的 attention 了（可以不只用 L2R decoder 了）。
2. 为了双向，一个方式是用 Bert。但是 bert 实现方式是：随机把某些  token 换成 MASK 特殊 token，而不是作用于 attn mask 矩阵。这样一个batch内，只能部分token mask掉（因此低效吗）。总之用bert的话，“会极大增加训练和解码时的计算量”。
3. 于是作者采用新增一个 decoder的方式。除了实现简单，还可以选择只开启一个decoder（同时 decoder 部分还能脱离CTC 解码，也算好处吧）。

###  dynamic chunk
用于加速CTC的解码。不用等语音完全结束才开始CTC解码，而是随着chunk推进就可以做 CTC 解码。CTC 全解完后，开始做 R2L/L2R 的 rescore 优选。而后者并非流式的。

一个 chunk 一般几百毫秒到一两秒。

### VAD 怎么处理的？
wenet 内基于一些规则判断语音开始结束。

参： https://mp.weixin.qq.com/s?__biz=MzU2NjUwMTgxOQ==&mid=2247484024&idx=1&sn=12da2ee76347de4a18856274ba6ba61f&chksm=fcaacaaccbdd43ba6b3e996bbf1e2ac6d5f1b449dfd80fcaccfbbe0a240fa1668b931dbf4bd5&scene=21#wechat_redirect

### eNet 号称流与非流一致处理。怎么和现实情况对应的？
鉴于 wenet 是两阶段的：先ctc弄出多个候选，再用 transformer decoder 选择出最佳候选。而后者要求能看到所有语音，所以，所谓 dynamic chunk 能有助于流式处理，不过是说能降低其时延，也就是能令 CTC 快速流式进行。当ctc 快速进行时，当然可以让用户看到识别过程，但是最终识别结果仍然需要被处理的语音全处理完后才能拿到。

也就是，整体上仍然是一段一段的，并非流式。
