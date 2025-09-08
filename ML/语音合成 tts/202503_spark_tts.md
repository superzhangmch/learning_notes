# 《Spark-TTS: An Efficient LLM-Based Text-to-Speech Model with Single-Stream Decoupled Speech Tokens》 https://arxiv.org/pdf/2503.01710

它的基本方法，和 cozyvoice 一样，用通用预训练的 LLM 作为主干，对于语音都 token 化。所以很天然支持语音 clone。

----

### tokenizer

<img width="886" height="532" alt="image" src="https://github.com/user-attachments/assets/e4b016c8-85ba-40f6-8126-78c7fc844ed9" />

### 主流程

<img width="1158" height="696" alt="image" src="https://github.com/user-attachments/assets/b6c0a787-edd8-494f-8390-2d5d1c47da01" />
