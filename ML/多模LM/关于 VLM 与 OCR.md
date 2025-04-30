无疑 VLM 直接做长篇 OCR，已被证明很成功。

有说 ViT 更偏向低频特征，对高频细节不敏感：ViT 更偏向低频特征，对高频细节不敏感: 在CV界，传统卷积已经彻底输给Transformer了吗？有狮子的那个回答， 以及里面有所提及的 https://arxiv.org/pdf/2202.06709。那么为啥 ViT 用于多模 LM，作 OCR 效果还很好？是这里所说的高频，对于文字细节纹路，并不算高频，也就是高频频段定义不同？或者强大数据加持暴力训练下，一个 vit 的patch 内有啥内容，直接记住了？待究

实验对一张清晰文字图，依次边长缩为原图的1/n，n为10甚至20时候，模型都能认个七七八八，而人看来就是一片糊了。看来它确实不是靠人能看懂的方式看懂的：

![image](https://github.com/user-attachments/assets/8a02bcc1-56f2-4d05-ba95-d1a90d94b4c2)

十分之一：

![image](https://github.com/user-attachments/assets/0a50386c-f25c-4fb7-bd0b-0be27accf49c)

二十分之一：
![image](https://github.com/user-attachments/assets/139b12c7-6d29-4c38-9bb2-4a26d873d0e7)
