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
