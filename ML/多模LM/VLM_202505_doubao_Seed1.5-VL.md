# https://arxiv.org/pdf/2505.07062 《Seed1.5-VL Technical Report》 即火山云的 doubao-1.5pro-vl-think

乃 vision thinking model。

### 参数量 
- vision encoder：532M 参数
- LLM： MOE 结构，激活 20B 参数

### 模态支持
- 任意分辨率图片，视频。
- seed-ViT 多模态 encoder 在预训练阶段使用了 video-audio-text tuples（具体待细看），但是最终 model 不支持 audio 作为 input

### vision encoder

532M 参数，原生支持各种大小分辨率的图片。用 2D-rope 位置编码。（还支持对 audio 作编码) 三阶段从头开始训的： 
1. Masked Image Modeling + 2D RoPE
2. 图片原生分辨率+对比学习(Native-Resolution Contrastive Learning) 
3. 音频、视频都有的全模态 Pre-training

### 视频支持

如同 qianwen vl，它也支持视频输入。

这要求能适应不同帧率的 video，并能感知一帧的绝对时间。qianwen-vl-2.5 的做法是，3D-rope 位置编码中有一个位置维度专门处理 frame number。定义一个标准帧率，令一个位置 id 代表一定的绝对时间——于是可以通过调整 pos ids 的 id 数值间距，来实现不同的 FPS 帧率。

seed-vl 的方式是在帧之间插入**时间戳 token**，从而表示该帧属于什么绝对时间。

paper 中说它支持 Dynamic Frame-Resolution Sampling，但并不是一个视频中有的片段的帧率 fps 大，有的小，而是一个视频全局用一个 fps，只是这个 fps 可以按需取 1、2、5 等。视频单帧的img分辨率也可以按需调整，用 {640, 512, 384, 256, 160, 128} 之一。但是并不是有的帧用大分辨率，有的用小，而是video内所有帧用统一分辨率。最终会令单个 video 的token数不超 81920。

### 整体原理图

![image](https://github.com/user-attachments/assets/5c46cdd0-0289-4df6-9200-f40c78d1845b)

图片、video 的空间位置关系，是通过 2d-rope 在 vit-encoder 捕获的。在 LLM 层面，只用了 1D 位置编码。

### 支持的比较特殊的任务（一般任务比如 ocr 之类比列）

1. 物体位置定位（识别出物体的 Bounding Box、识别出中心点坐标）、物体计数（因物体定位而带来的能力）
   - 会把坐标归一到 （1~1000）
2. video 中的时间定位
3. Graphical User Interface (GUI) 中的元素定位(给出 bbox）
4. 两个图片找不同

### 思考 ouput 怎么打造的

后训练仍然是 SFT + RL。

SFT 数据中就包括 LongCoT 数据。 RL 包含格式 reward：`<think>{thought}</think>{solution} `。

它不是 pre-training => SFT => RL 线性流程。而是 SFT 与 RL会交叠多次：RL 阶段帮助发现更好的 Chain-of-Thought（CoT）数据，然后这些被选中的高质量输出重新用于 SFT，更新基础模型，再进行下一轮 RL。

![image](https://github.com/user-attachments/assets/8681d9f1-e0f4-49ff-8b5e-762f19456ca9)


### 其他

paper 中提到了它的 scaling law 情况，未究。


