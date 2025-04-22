### qw-VL-1 （https://arxiv.org/pdf/2308.12966） 2023.08

![image](https://github.com/user-attachments/assets/4121756e-32dc-4a28-ae66-a2215849bba9)

qw-VL-1 还用的blip 那样的 q-former 样的东西。且 input 图片必须先剪切成固定大小，经过 q-former-adapter 转化成固定的 256 个 token，然后参与到 LLM 中。adapter 处用到了 2D 绝对位置编码。

它的亮点之一是 ，支持 Bounding Box 可作为 text 的 input 或 text 的 output。还只是个 10B 的小模型。

### qw-VL-2 （https://arxiv.org/pdf/2409.12191） 2024.09

vision encoder 变成到了 675M（VL-1 是 1.9B），但整个model 变大到了 72B。


