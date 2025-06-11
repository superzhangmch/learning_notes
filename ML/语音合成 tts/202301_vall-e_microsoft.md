# vall-e 《Neural Codec Language Models are Zero-Shot Text to Speech Synthesizers》 https://arxiv.org/pdf/2301.02111

其实背后有一系列 paper （ https://www.microsoft.com/en-us/research/project/vall-e-x/ ），这里只看第一篇。

![image](https://github.com/user-attachments/assets/6c7fb018-0710-47fe-9e49-3cf6e8097169)

- text 要抽取 phoneme（比如对汉语则是先汉字转拼音）, 而不是 text token 化。
- 用 EnCodec 作 audio tokenize 后，经过 8 阶段，得到 8 个 token code, 拼起来得到单个 audio token 的最终 token id（每 stage 容量是 1024， 所以 codebook 大小是 8k）。
  - 但是因为 stage-1 的结果所含信息最大，所以对 stage-1 用自回归，令生成梗概后，再用 7 层的 NAR 把余下的 stage-2 ~ stage-8 都生成。这样就完成了 audio 的 tokens list 的生成。
- 没经过 mel 谱中间过程，而是一步到位：`audio tokens list => audio wave`。这是为了方便用现成的东西，比如 EnCodec 的 decoder（EnCodec是 encoder-decoder 结构的，所以还用了它抽取 audio tokens）。 
- 因为语音生成时是先经自回归（再经 7 次 NAR 补充细节，得到最终的 output audio tokens list），语音的节奏速度都可以通过自回归自动决定，这样就不需要 duration predictor 了。
