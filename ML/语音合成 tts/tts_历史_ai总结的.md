以下是一些**著名的 TTS（Text-to-Speech）模型**，按技术演进顺序和代表性结构分类列出，涵盖了从早期的 RNN 到最新的多模态 LLM 驱动模型：

### 一、基于 RNN 的早期模型

| 名称                   | 出品机构            | 特点                                                              |
| -------------------- | --------------- | --------------------------------------------------------------- |
| **Tacotron**         | Google          | 基于 seq2seq + attention，输入字符或音素，输出 mel-spectrogram，再接 vocoder 合成 |
| **Tacotron 2**       | Google          | 前端用 Tacotron 输出 mel，后端接 WaveNet；语音自然度高                          |
| **Deep Voice 1/2/3** | Baidu           | 模块化设计，强调多说话人支持和端到端训练                                            |
| **Char2Wav**         | Google DeepMind | 用字符直接生成 waveform 的尝试                                            |

### 二、基于 Transformer 的模型

| 名称                            | 出品机构      | 特点                                     |
| ----------------------------- | --------- | -------------------------------------- |
| **Transformer TTS**           | Google    | 用 Transformer 替代 RNN，提高并行性和建模长距离依赖能力   |
| **FastSpeech / FastSpeech 2** | Microsoft | 非自回归，极大加快推理速度，引入时长预测模块                 |
| **Glow-TTS**                  | NVIDIA    | 流模型（flow-based），支持可控性和更稳定的训练过程         |
| **Parallel Tacotron**         | Google    | 使用 flow 模型解码 mel谱，无需 autoregressive 推理 |

### 三、Vocoder 模型（waveform 生成器）

| 名称           | 出品机构        | 特点                          |
| ------------ | ----------- | --------------------------- |
| **WaveNet**  | DeepMind    | 首个高质量神经 vocoder，生成音质极佳，但速度慢 |
| **WaveGlow** | NVIDIA      | flow-based，高效快速             |
| **HiFi-GAN** | Kakao Brain | 高速 + 高质量的非自回归 vocoder，广泛使用  |
| **BigVGAN**  | MIT         | 音质极高的 GAN vocoder，适用于多样音色合成 |

### 四、多说话人 / 可控风格模型

| 名称                        | 出品机构      | 特点                                          |
| ------------------------- | --------- | ------------------------------------------- |
| **YourTTS**               | Coqui AI  | 支持跨语言语音克隆                                   |
| **VITS**                  | NAVER     | Variational + flow + GAN 联合建模，端到端直接从文本到语音波形 |
| **StyleTTS / StyleTTS 2** | Microsoft | 支持风格迁移和控制，生成可调的语音风格                         |

### 五、大模型驱动的多模态 TTS

| 名称                    | 出品机构        | 特点                                                  |
| --------------------- | ----------- | --------------------------------------------------- |
| **Bark**              | Suno.ai     | 支持多语言、音效、音乐，基于 transformer 的生成式语音模型                 |
| **Tortoise TTS**      | independent | 高质量但推理慢，支持风格迁移、长文本朗读                                |
| **VALL-E / VALL-E X** | Microsoft   | few-shot 语音克隆，输入几秒音频即可模仿声音                          |
| **GPT-SoVITS**        | 社区          | 基于 So-VITS + GPT 模拟人的说话方式，实现自然过渡                    |
| **CosyVoice**         | Paper系列     | 与多模态 LLM 联动，支持情感、节奏、说话人控制，生成 speech token 送 vocoder |
| **GPT-4o（OpenAI）**    | OpenAI      | 端到端从文本到语音，能进行自然语调的对话回应，已融合语音识别和生成能力                 |

----

在基于 RNN 的早期 TTS 模型（如 Tacotron）出现**之前**，TTS 技术主要采用的是传统的**统计建模方法和拼接式技术**。大致可以分为以下两类：

### 一、拼接式语音合成（Concatenative TTS）

#### 核心思想：

将真实人类录制语音切成小单元（如音节、词素、音素），存储在数据库中，然后根据输入文本**查找并拼接**这些语音单元。

#### 关键技术：

* 单元选择（Unit Selection）：根据上下文选择最自然的片段拼起来
* HMM/DTW 动态时间规整用于对齐与评分

#### 优点：

* 音质好（因为是真人语音）
* 不需要学习声音本身

#### 缺点：

* 库太大，维护困难
* 灵活性差（风格、说话人难控制）
* 无法生成未录制的音素组合（Out of Vocabulary 问题）

### 二、参数式语音合成（Parametric TTS）

#### 核心思想：

用统计模型（如 GMM 或 HMM）来**建模语音参数**（音高、时长、频谱等），然后通过声码器（Vocoder）合成声音。

#### 代表技术：

* **HTS (HMM-based Speech Synthesis System)**：东京大学等提出，用 HMM 建模音素到频谱的映射
* **STRAIGHT / WORLD vocoder**：高质量语音合成器
* **Festival / MaryTTS**：早期开源系统，支持多语言

#### 优点：

* 占用资源小
* 可控性强（如语速、音调可调）

#### 缺点：

* 语音听起来“电子”、“机器人”感强（音质差）
* 参数化建模过于简化，丢失语音细节

### 三、向神经网络过渡的关键技术节点

| 年代     | 技术名             | 说明                                        |
| ------ | --------------- | ----------------------------------------- |
| \~2012 | HMM-based TTS   | 如HTS，仍是主流                                 |
| 2014   | Deep Voice 1 原型 | DNN 替代 GMM，用于预测声学参数                       |
| 2016   | WaveNet         | 首个神经网络直接生成波形模型，开启新时代                      |
| 2017   | Tacotron        | seq2seq + attention，端到端预测 mel-spectrogram |
| 2018   | Tacotron 2      | 联合 WaveNet + Tacotron，更自然的语音              |
