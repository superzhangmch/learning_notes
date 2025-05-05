# [《Step-Audio: Unified Understanding and Generation in Intelligent Speech Interaction》](https://arxiv.org/pdf/2502.11946)

### 参数量
LLM 部分是 130B。比其他各家的不到 10B 大很多。

### 支持哪些模态
paper 中：整个 model 是支持 audio、vision input，以及 audio output 的。

开源出的 model 里：不支持 vision，而且即使 audio，也只是先生成 text，然后经 tts 步骤变成语音。

### audio 怎么处理

首先它对于 audio 的input、output，都是 tokenize 成 audio tokens 来处理，且 input、output 用同一个 tokens 空间。

glm-4-voice 中就提到 audio 的声学(acoustic)与语义(sementic)特征的矛盾与权衡问题。step-audio 也面临差不多问题（不过不是简单平衡这两者）。它经过实验，最终选用方法是，同时采用两种tokenizer：把两者获得的 tokens 交错排布到一个数组里。

具体说来：
- linguistic tokenization（编码语音phonemic、语言结构等）：Paraformer encoder 结果量化成 16.7 Hz token 率，codebook size=1024。
- semantic tokenization（编码语义与粗粒度声学特征）：直接用 CosyVoice 的 tokenizer，25 Hz 的 token 率。codebook size=4096。

16.7:25 = 2:3, 为了平衡两者不同的每秒token数，于是按 2:3 的比例把两种 tokens 交错混合。在生成 audio 的时候，也是从交错的 audio tokens 中解码出音波（ audio tokens => wave, 经过 flow_matching 等，和别家 model 方式就是一样的了）。

### 整体怎样工作

![image](https://github.com/user-attachments/assets/e8756678-78d2-43f9-8751-e7869bd48f88)

