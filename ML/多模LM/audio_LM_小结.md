对最近半年来的多个 audio 大模型，简探其实现，大体说来：

1. 对于 audio input，为传给 LLM：可以用 audio encode 直接编码成连续特征（qianwen-2.5-omni），也可 tokenizer 离散成 audio token（多用此）。多用 whisper。
2. 对 audio 编码时，需要权衡语义与声学等特征的提取，最好兼而有之，或者设法兼具。
3. 为让 LLM 输出 audio，自然是在 audio tokens 上作自回归接龙。但似乎没有一款 audio-LLM 直接这样做，而是要先生成 text，然后让 model 照着读。只是一般照读时仍然要让 model 看到 audio / text 等 input context。少数是后接一个 tts 模块。
4. 生成 audio token id list 后，一般都是先经类扩散模型的 flow-matching 转为 mel-谱，然后再经 GAN 模型转为声波。（但是audio token ids 直接经 gan model 得到 wave 也不是不能，见《speechGPT》）

所看各 model 为： qianwen-2.5-omni(2025.03)、glm-4-voice(2024.12)、kimi-audio(2025.04)、step-audio(2025.02)。。

另外，也有不用 mel谱，而直接 speech tokens => audio wave 的。稍早2024年的《speechGPT-202305》、《LLaMa-omni-202409》是用的 HuBert 经 k-means 搞出的离散 tokens，然后对 speech-tokens 序列，经过 unit-Hifi vocoder 不经 mel-谱，直接一步得到的 audio wave。

