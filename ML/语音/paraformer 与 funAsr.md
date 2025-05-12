## CIF (CONTINUOUS INTEGRATE-AND-FIRE)
类似 CTC 作序列对齐的一种技术。paraformer 基础就在于此。参 https://github.com/superzhangmch/learning_notes/blob/main/ML/%E7%90%86%E8%AE%BA/CTC%E3%80%81transducer%E3%80%81CIF.md#cif 

![image](https://github.com/user-attachments/assets/ebf189d7-5706-417b-ba9f-02d1cd68edae)

---
## paraformer

### inference
![image](https://github.com/user-attachments/assets/6a18376c-685f-4ecd-a4c8-1cf6e266cbc7)

inference时，工作原理如上图。粗略地说，对于语音 frames：
- 先经标准 CIF 流程：得到文字token的边界点，以及每个待识别文字 token 的 hidden 表示。
- 然后一一对应识别具体 token 即可。

paraformer 特点在于第二步。根据第一步，一共能识别出多少字，已经知道了，每个字的表示也有了，最简单是根据表示来预测该token即可，都不需要 transformer。但是这样彻底忽视了前后文环境信息，更进一步是causal transformer。而  paraformer 用了双向 full-attn transformer。名字中的 para-，乃 parallel 的缩写，表示不像自回归transformer那样只能一个字一个字往外预测，它是可以并行一次预测所有字(鉴于有full attn, 所以是并行但不独立)。

### train

![image](https://github.com/user-attachments/assets/49e58d87-3356-46e4-b834-b50491c38cae)

在某一个 train step，先 inference 一步，看看和 ground  truth 的差异：根据差异率把 CIF 的 embds 中的一些随机替换成 ground-truth token 的 embds。差异率越大，替换的越多。这样容易最终学到 output tokens 之间的依赖关系。

这样分两步的训练方式，正如 paraformer 文中指出，来自 https://arxiv.org/pdf/2008.07905 《Glancing Transformer for Non-Autoregressive Neural Machine Translation》。只是那里是翻译问题，二者手法如出一辙：

![image](https://github.com/user-attachments/assets/11d48860-62df-4ed9-a408-ff3167fe4a46)


---

## funASR



---
### 相关 paper
- https://arxiv.org/pdf/2305.11013 《FunASR: A Fundamental End-to-End Speech Recognition Toolkit》
- https://arxiv.org/pdf/2206.08317 《Paraformer: Fast and Accurate Parallel Transformer for Non-autoregressive End-to-End Speech Recognition》
- https://arxiv.org/pdf/2301.12343 《Achieving Timestamp Prediction While Recognizing with Non-Autoregressive End-to-End ASR Model》--funasr 团队一前作
- https://arxiv.org/pdf/1905.11235 《CIF: CONTINUOUS INTEGRATE-AND-FIRE FOR END-TO-END SPEECH RECOGNITION》

