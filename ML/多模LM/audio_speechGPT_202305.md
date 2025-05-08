# 《SpeechGPT: Empowering Large Language Models with Intrinsic Cross-Modal Conversational Abilities》 https://arxiv.org/abs/2305.11000 【2023.05】

### 所用 LLM：
用 LLaMA-13B

### 支持模态：
语音可以是 input 也可以是 output。不支持 vision

### 语音处理：
用 huBERT（hubert 内用 k-means 方式聚合出离散 tokens）把 audio 转 speech token。model 对 speech tokens 作自回归后，用 GAN model 还原出语音。会把 speech token 扩充 LLM（LLaMa） 的 text token 表。

语音生成：speech tokens 生成语音用 HiFi-GAN vocoder（speech token ids=> embds, 然后..），而非后来的 qianwen-2.5-omni, glm-4-voice 等所用的 flow-matching。

![image](https://github.com/user-attachments/assets/94af0198-5bbb-4147-8b50-a4e45307cf4c)

知否直接生成 audio：虽然上图看是直接生成，其实不能。生成语音回答，也是要再 一次model交互内部，先生成 text tokens，然后再读出(即紧接着输出 speech tokens)。后来的 glm-4-voice，qw-2.5-omni，都也类似。

paper 中对于语音问，语音回答的 prompt 长这样：

![image](https://github.com/user-attachments/assets/c9ba0a3b-078a-4050-9576-33ed070ca743)

### 不足
1. 生成audio的 emotional tones 不足
2. 必须先生成 text，才能生成相应语音
3. 因为 context length 限制，不支持多轮
