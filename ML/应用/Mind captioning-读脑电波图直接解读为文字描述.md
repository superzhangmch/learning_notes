《Mind captioning: Evolving descriptive text of mental content from human brain activity》

它用 线性模型把 fMRI 脑信号映射到大语言模型的语义向量空间，再用 Transformer 优化生成与该语义向量匹配的文本。

能做什么：在实验室里，从一个人的大脑活动（看或回忆视频时）生成大致描述该视觉内容的句子。

要点: 只能每个人独立做, 不能跨人; 这类脑机接口的, 全是每个人独自做的.

fMRI = functional MRI, 是“功能性磁共振成像”, 看大脑活动（血氧变化）, 通过检测这个, 从而获得脑活动信号, 然后用 model 转文字. 

### 两阶段: brain → semantic space → text

阶段 1：脑信号 → 语义向量: 
- 被试看视频（或回忆视频）, 用 fMRI 记录脑活动（血氧变化）
- 同时给视频提前做好人工 caption. 并用大语言模型（DeBERTa）把 caption 转成语义向量
- 训练 线性回归模型：fMRI 体素信号 对齐 caption 语义向量

阶段 2：语义向量 → 文本
- 用训练好的模型把脑信号解码成语义向量
- 从 <unk> 开始, 用 RoBERTa（MLM Transformer）反复 mask + 填词, 优化句子，使其语义向量接近脑解码向量

### 实验构造

一共六个人. 每个人训练自己的 model, 测试时也是各自测试, 不能交叉(不能 A 用 B 的 model). 

- 每个被试总共扫描时间约 17.1 小时: 训练11.8h, test 1.8h; 想象（回忆）实验, 约 3.6 小时 

每小时扫描成本极高, 人必须全程躺着不动, 机器价格极贵. 所以没法大规模实验. 
