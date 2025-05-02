# 《GLM-4-Voice: Towards Intelligent and Human-Like End-to-End Spoken Chatbot》 https://arxiv.org/pdf/2412.02612

### 参数量
LLM 部分是 9B。

### 支持哪些模态
audio input + audio output，不支持 vision。

### audio tokenizer 与 decoder

**（1）、audio tokenizer**

不像 qianwen-2.5-omni 用了 audio-encoder，glm-voice 是用的 tokenizer——也就是把 audio 离散 token 化，然后 embedding。

如下图，在 whisper-large-v3（encoder-decoder 架构的） 的 encoder 的中间插入 vector 量化层（VQ)，然后作一定 fine tune。最后取 encoder 的一半（截止到量化层），作为 tokenizer。

![image](https://github.com/user-attachments/assets/25c239e5-fd5c-449f-a631-6a12bc6bf1e2)

最终的 tokenizer 对一秒 audio 编码出 12.5 个 token (12.5HZ)。根据 glm-4-voice 所依赖的前作 https://arxiv.org/pdf/2411.17607 (也是他们团队的），codebook 大小是 2^14=16384, 即一个 token 占用 14个bit。14*12.5=175，所以文中说，他们的 tokenizer 是 175 bits/sec 的超高压缩率的。

为支持流式 encoding，也有相应改造（卷积以及双向 attention，都变成了 causal 风格的）。

为什么要在 whisper encoder 的中间插入 VQ 层，而不是末尾？大概是这样：原文提到，一般的 audio tokenizer 可以分为两类：声学型（acoustic tokenizer） 和 语义型（semantic tokenizer）。前者能重建高质量音频，但语义信息保留不足，除非以高采样率（高 token/s）或堆叠 codebook；而后者重在压缩语义内容，但牺牲了语音的音质与细节。whisper encoder 的输出是高度语义化的东西，为了兼顾 acoustic & Semantic，于是就用了 encoder 的中间层来提 speech token 化。

**（2）、audio decoder**

上述 audio tokenizer 生成的 speech tokens，既用于audio input 编码，也用于 audio output 生成。

为了从 speech tokens 中生成 audio，要经过两个model：类似扩散模型的 flow matching（tokens => mel谱)，以及 GAN 模型(mel谱 => audio wave)。

![image](https://github.com/user-attachments/assets/43a3af74-3016-4b1e-835d-473f7fd292da)

上面的 tokenizer 方法，据作者讲，受到了 cosyvoice 的 tokenizer 所启发。而 flow_matching + GAN 的 decoder，模型架构直接借自 cosyvoice。

为了低延迟，speech decoder（flowMatching+GAN）是需要分块（block）进行的。作者选用了每 10 个 speech tokens 为一个 block。10 个 tokens=0.8秒（12.5 HZ 的 audio 帧率，12.5*0.8=10）。训练 decoder 时，要把训练数据整成不同的整数个 blocks，以便与 inference 对齐。在qianwen-2.5-omni中，是分块后滑窗方式处理的，flow matching 只关注临近 block，而 glm-4-voice 看起来是关注了整个前序序列。

### 整体怎样工作

最理想状态，当然是 model 直接接龙输出 speech tokens。但作者说，鉴于 text 能表达出语音想表达的大部分东西（当然语气、速度之类不行，否则直接 tts=Text-to-Speech 得了），而 text 的 LLM 已被证明很成功，所以还是要用 text 来中转一下——也就是为了生成 audio output，还是要先生成 text，然后让 model 把 text 读出来。但是读 text 的时候，毕竟 model能看到 audio input 以及整个 context，所以能把语速语气之类的说出来。（也就是，这就是一种高级的 tts 而已。另外，当前多个开源 audio output 的 model，比如 qianwen-2.5-omni，都也是这样操作的。）

一旦最终还是变成了 tts 问题，不可避免的事情是时延：总不能等 text 全生成了才开始"读"。这也是各家 audio-model 处理各不相同的地方。qianwen-2.5-omni 的思路是另外搞出一个talker model，每新看到一个 text output就赶紧念，从而化解了时延问题。

glm-4-voice 的解法是：让 text 和 audio 的生成交错进行，首先生成一定数量 text tokens，一旦数量够（13个），哪怕一句话只说了一半，也要切换成生成 audio tokens（这时候audio 就可以参考前面的text了）。audio token 生成数量够限额（26个），则马上开始继续生成 text tokens，如此交错往复。13 个 text tokens，足足够 26个 audio tokens 来读，所以 audio 总是慢 text 一拍，不用怕读着读着没东西了。当 text 想表达的内容结束了， audio tokens 的生成就不用再和 text 来交错了，而是可以一股脑儿把余下的都生成了。

如下图，text 和 speech 的交错，并不是说一次输出既支持 text，又支持 speech，而是二者在内容上是一致的。speech 是把 text 念了一下而已。【为了吐出第一个audio，需要等待生成13个text token + 10个speech token（10个为一个decoder block）共23个token后，decoder 才能开始工作。所以下图说latency 是大约 20 个 LLM output tokens】

![image](https://github.com/user-attachments/assets/0c31d54f-bd49-41b2-ab2a-6e2f7f322214)

assistant 的回复的一个例子：
```
我虽然不能真正唱歌，但我可以帮你一起回忆这首歌的
<|audio_14295|><|audio_7110|><|audio_11342|><|audio_12579|><|audio_5921|><|audio_10281|><|audio_3230|><|audio_15355|><|audio_5342|><|audio_15444|><|audio_8821|><|audio_1807|><|audio_3376|><|audio_671|><|audio_43|><|audio_3113|><|audio_9872|><|audio_14438|><|audio_8440|><|audio_5450|><|audio_1160|><|audio_3133|><|audio_3090|><|audio_5492|><|audio_11143|><|audio_14165|>
旋律和歌词，让我们一起来哼唱吧！准备好了吗？
<|audio_14343|><|audio_12253|><|audio_15870|><|audio_5266|><|audio_7301|><|audio_10114|><|audio_8064|><|audio_13573|><|audio_16031|><|audio_2476|><|audio_60|><|audio_3268|><|audio_10383|><|audio_1715|><|audio_4176|><|audio_12820|><|audio_1223|><|audio_1944|><|audio_9281|><|audio_14934|><|audio_6157|><|audio_9843|><|audio_2705|><|audio_9000|><|audio_8206|><|audio_16065|>
"小猫旅店，小猫旅店，欢迎来到
<|audio_12076|><|audio_6237|><|audio_11015|><|audio_7458|><|audio_923|><|audio_9534|><|audio_9143|><|audio_5340|><|audio_6774|><|audio_226|><|audio_283|><|audio_5312|><|audio_9252|><|audio_8219|><|audio_852|><|audio_7143|><|audio_14514|><|audio_6963|><|audio_3472|><|audio_3300|><|audio_15312|><|audio_15885|><|audio_15095|><|audio_973|><|audio_9315|><|audio_14102|>
我的小世界..."
<|audio_3938|><|audio_5336|><|audio_11443|><|audio_11005|><|audio_10706|><|audio_1829|><|audio_3566|><|audio_14204|><|audio_7993|><|audio_16313|><|audio_3154|><|audio_4175|><|audio_16218|><|audio_7137|><|audio_1601|><|audio_6963|><|audio_12217|><|audio_12217|><|audio_15526|><|audio_14247|><|audio_1737|><|audio_5291|><|audio_15541|><|audio_11752|><|audio_3888|><|audio_14383|><|audio_13331|><|audio_9312|><|audio_6392|><|audio_11089|><|audio_14696|><|audio_12217|><|audio_3472|><|audio_3472|><|audio_6376|><|audio_12715|><|audio_11495|><|audio_6176|><|audio_14943|><|audio_592|><|audio_10757|><|audio_10549|><|audio_10253|><|audio_15848|><|audio_9914|><|audio_3063|><|audio_554|><|audio_7114|><|audio_3434|><|audio_6963|><|audio_12715|><|audio_11495|><|audio_6176|><|audio_14943|><|audio_592|><|audio_10529|><|audio_1626|><|audio_997|><|audio_2990|><|audio_8612|><|audio_3063|><|audio_5109|><|audio_15503|><|audio_9433|><|audio_2664|><|audio_3300|><|audio_6376|><|audio_3727|><|audio_12184|><|audio_2177|><|audio_2377|><|audio_15548|><|audio_5133|><|audio_8161|><|audio_10679|><|audio_15955|><|audio_9100|><|audio_11795|><|audio_211|><|audio_6287|><|audio_4714|><|audio_2931|><|audio_14383|><|audio_1793|><|audio_8572|><|audio_8275|><|audio_3063|><|audio_13042|><|audio_11940|>
```

解释下：
```
我虽然不能真正唱歌，但我可以帮你一起回忆这首歌的         # 前面是13个token，显然句子还没说完就被打断了
<|audio_14295|> ... 共 26个 ... <|audio_14165|>  # 26 个 speech token
旋律和歌词，让我们一起来哼唱吧！准备好了吗？            # 又是 13 个 text token
<|audio_14343|> ... 共 26个 ... <|audio_16065|>  # 26 个 speech token
"小猫旅店，小猫旅店，欢迎来到                        # 又是 13 个 text token
<|audio_12076|> ... 共 26个 ... <|audio_14102|>  # 26 个 speech token
我的小世界..."                                    # 最后一次的 text tokens。可能不足 13 个
<|audio_3938|>...多于26个  .. <|audio_11940|>    # text token 已经生成完了。接下来的 audio token就要超过26个了
```

### 训练

分两阶段：（1）、包含 audio 的大规模 pretrain （2）、跟着text 读的交错数据上的训练（与 inference 对齐）

![image](https://github.com/user-attachments/assets/936170bd-e843-4e7c-af78-a694eaf61d8b)
