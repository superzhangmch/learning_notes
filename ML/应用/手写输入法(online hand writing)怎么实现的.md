# 手写输入法(online hand writing)怎么实现的

对于汉字，比较早期的方法，是靠笔顺的。笔顺错了，即使写得再好，也识别不出（或者结果中排不到前面）。而且是一个字一个字识别的。一个有 demo 可体验的例子： https://github.com/gugray/hanzi_lookup （用它教小学生写字很好）。

后来，基本都是可以识别多个字，且笔顺错了也没问题，连笔叠字都也可以。特考察几篇 paper 管窥一下怎么做到的：
- 偏规则的方法（虽然内部步骤也用到了神经网络模型），多语言支持。[google 2016: Multi-Language Online Handwriting Recognition](https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=7478642)
- 上篇之改进，用 LSTM + CTC：[google 2019: Fast Multi-language LSTM-based Online Handwriting Recognition](https://arxiv.org/pdf/1902.10525)
- transformer：[2022：Transformer-based Models for Arabic Online Handwriting Recognition](https://thesai.org/Downloads/Volume13No5/Paper_102-Transformer_based_Models_for_Arabic_Online_Handwriting.pdf)

### google 2016: Multi-Language Online Handwriting Recognition

![image](https://github.com/user-attachments/assets/66c69b67-48fd-489c-8bd5-8e8a5ba85c3d)

多语言支持，一次识别多字，不怕连笔。乃 segment & decode 法。 先oversegment——不怕切错，就怕漏（然后下一步过滤即可）。最后构建了有向带权图，于是从图中找最优秀路径就是结果。找路径的方法是 beam search, 还要有（char以及word级别的）语言模型以及一些其他的先验知识（比如候选char的频率先验，类型先验等）的辅助来作解码。

该文比较了 lstm，但是效果不如该文方法。

### google 2019: Fast Multi-language LSTM-based Online Handwriting Recognition

对上文方法，该文做了极大简化。

按时间序列处理input，把序列化的input 灌给双向 lstm，然后 CTC loss，即可得到识别结果。

CTC 来处理这类seq2seq问题的合理性自不待言。它的input 特征处理方法是：先得到 fea_i = (x坐标，y坐标，时间t，是起笔还是落笔以便区分不同笔画)，归一化，以及笔迹点重采样（使得总点数合理）后，作按时间的差分： $feaFinal_i = fea_i - fea_{i-1}$，然后就可以丢给 lstm 了。解码的时候用 CTC 的惯常解码做法即可（一般用 beam search，可以结果语言模型来做加强）。

另外为了加速inference 速度，该文还用了 bezier curve（即三次曲线）拟合笔迹从而只用bezier 曲线特征的方式。

![image](https://github.com/user-attachments/assets/4f20486e-5775-496e-9c1c-3d27814621fe)

如上，图中 bezier 曲线的彩色的六个特征数值，被该文直接当做了 stroke 特征来用。但是还需考虑时间特征，决定 t(s)性质的系数γ₁, γ₂, γ₃也当做了特征用。除了这9个，还有一个当前segment是否属于落笔起笔的特征（对原始stroke会做适当的切分或合并）。

