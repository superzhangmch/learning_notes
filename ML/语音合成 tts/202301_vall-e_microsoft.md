# vall-e 《Neural Codec Language Models are Zero-Shot Text to Speech Synthesizers》 https://arxiv.org/pdf/2301.02111

其实背后有一系列 paper （ https://www.microsoft.com/en-us/research/project/vall-e-x/ ），这里只看第一篇。

![image](https://github.com/user-attachments/assets/6c7fb018-0710-47fe-9e49-3cf6e8097169)

text 要抽取 phoneme（比如对汉语则是先汉字转拼音）, 而不是 text token 化。用 EnCodec 作 audio tokenize 后，经过 8 阶段，得到 8 个 token_id, 拼起来得到最终的单个 audio token。但是因为 stage-1 的结果所含信息最大，所以对 stage-1 用自回归，令生成梗概后，再用 7 层的 NAR 把余下的 stage-2 ~ stage-8 都生成。这样就完成了 audio 的 tokens list 的生成。

然后 `audio tokens list => audio wave`, 没经过 mel 谱中间过程，而是一步到位。这用了现成的东西，比如 EnCodec。 
