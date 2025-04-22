### qw-VL-1（千文-VL-1） （https://arxiv.org/pdf/2308.12966） 2023.08

![image](https://github.com/user-attachments/assets/4121756e-32dc-4a28-ae66-a2215849bba9)

qw-VL-1 还用的blip 那样的 q-former 样的东西。且 input 图片必须先剪切成固定大小，经过 q-former-adapter 转化成固定的 256 个 token，然后参与到 LLM 中。adapter 处用到了 2D 绝对位置编码，img 和 text 在 LLM 中仍用 1d-Rope。

它的亮点之一是 ，支持 Bounding Box 可作为 text 的 input 或 text 的 output。这一特点在后续版本都延续了下来。

它还只是个 10B 的小模型。

### qw-VL-2 （https://arxiv.org/pdf/2409.12191） 2024.09

vision encoder 变成到了 675M（VL-1 是 1.9B），但整个model 变大到了 72B。

主要变化是，input 支持了任意分辨率的图片，支持了视频。

![image](https://github.com/user-attachments/assets/ee01c926-fd4b-4dfc-9697-13bd171c7e00)

假设原始图片分别率是 (a, b), 则最终token 数是 (a/28)*(b/28)——它的 ViT encoder 是 14x14 切块，并最终把 2x2 的 patch 合一，所以是28. 上图的3 个 img，1个 video 即满足此点。不像 VL-1，用  q-former，而是像 LLava 一样，用 MLP 连接 Vit encoding 与 LLM（相邻的 2x2=4 个块作 MLP即为 vision token）。

位置编码：
- 训练ViT的时候，用了 2D-Rope（d维向量，分一半编码x，一半编码y）。
- 拼到 LLM 后，用 M-Rope 3d 位置编码把 text 与 vision 统一处理：每一token  用 (frame_idx, height, width) 三个位置 id 表示。下面讲 VL-2.5 再详述。


训练时，img 与 video 怎么与text 拼一起的（训练数据长啥样）：
![image](https://github.com/user-attachments/assets/793ce02d-e1d6-4133-a2e2-9574333a19b9)

### qw-VL-2.5 (https://arxiv.org/pdf/2502.13923) 2025.02

![image](https://github.com/user-attachments/assets/73dc5f83-1976-42b0-b7e7-6d9a07657cc9)

model 大体上和 VL-2 一样。仍然是 axb 的 img 转成了 (a/28)*(b/28) 个 vision token，用 MLP 桥接 img 与 LLM。且 vision encoder 内部仍是用了 2D-RoPE。为了很好处理video，还有某些特别操作（For video data, two consecutive frames are grouped together, significantly reducing the number of tokens fed into the language model），不论。

#### 关于 MRope 位置编码

MRope 位置编码把 text, image, video 三种模态统一作位置编码，作用于LLM。每个token 用 [t, h, w] == (frame_idx, height_idx, width_idx) 三个位置 id 表示。
- 对于 text 三个 id 取值一样，且顺序增一。
- 对于同一个 img 的多个patch 所形成的 token 序列：height_idx， width_idx 如实填写， 他们共用一个 frame_idx = 0. 然后对此 shape = [1, H, W] 的数组，每个元素统一加上 offset= max(img的前一token 的 t, h, w)值.
- 对于 video 的多个frame 形成的 token序列：height_idx， width_idx 如实填写, 而 frame_idx 则是帧序列。然后对此 shape = [frame_cnt, H, W] 的数组，每个元素统一加上 offset= max(img的前一token 的 t, h, w)值.

例子：
```
messages = [
    {
        "role": "user",
        "content":[{"type": "text", "text": "hello"}],
    },
    {
        "role": "assistant",
        "content": [{"type": "text", "text": "what can i do for you?"}],
    },
    {
        "role": "user",
        "content": [
            {"type": "image", "image": "img1.png", },
            {"type": "image", "image": "img2.png",},
            {"type": "text", "text": "what do you see in the picture?"},
            {"type": "video", "video": "video1.mov",},
            {"type": "text", "text": "what text do you see in the movie?"},
        ],
    }
]
```

转成 M-Rope位置编码id后是：

```
# text: hello , what can i do for you?
1 [0, 0, 0]
1 [1, 1, 1]
1 [2, 2, 2]
1 [3, 3, 3]
...
1 [28, 28, 28]
1 [29, 29, 29]
1 [30, 30, 30]
1 [31, 31, 31]
1 [32, 32, 32]

# img: img1.png
1 [33, 33, 33] # 统一加了前面的32
2 [33, 33, 34]
3 [33, 33, 35]
4 [33, 33, 36]
....
3574 [33, 81, 102]
3575 [33, 81, 103]
3576 [33, 81, 104]
3577 [33, 81, 105]

# text
1 [106, 106, 106] # 从 前面105开始
1 [107, 107, 107]

# img: img2.png
1 [108, 108, 108] # 从前面107开始。统一加了107得到img2.png 的 位置编码 id
2 [108, 108, 109]
3 [108, 108, 110]
4 [108, 108, 111]
...
884 [108, 144, 127]
885 [108, 144, 128]
886 [108, 144, 129]
887 [108, 144, 130]
888 [108, 144, 131]

# text: what do you see in the picture?
1 [145, 145, 145]
1 [146, 146, 146]
1 [147, 147, 147]
...
1 [153, 153, 153]
1 [154, 154, 154]

# video： video1.mov
# - frame 1
1 [155, 155, 155]
2 [155, 155, 156]
3 [155, 155, 157]
4 [155, 155, 158]
...
717 [155, 190, 171]
718 [155, 190, 172]
719 [155, 190, 173]
720 [155, 190, 174]

# - frame 2
1 [157, 155, 155] # frame_id = 155+2
2 [157, 155, 156]
3 [157, 155, 157]
4 [157, 155, 158]
5 [157, 155, 159]
...
716 [157, 190, 170]
717 [157, 190, 171]
718 [157, 190, 172]
719 [157, 190, 173]
720 [157, 190, 174]

# - frame 3: 
1 [159, 155, 155] # frame_id = 155+2+2
2 [159, 155, 156]
3 [159, 155, 157]
4 [159, 155, 158]
...
717 [159, 190, 171]
718 [159, 190, 172]
719 [159, 190, 173]
720 [159, 190, 174]

# text: what text do you see in the movie?
1 [191, 191, 191]
1 [192, 192, 192]
1 [193, 193, 193]
...
1 [203, 203, 203]
1 [204, 204, 204]
1 [205, 205, 205]
```

### 视频支持动态帧率与帧绝对时间编码

VL-2.5 的一个重要特色是对于 video，会把 frame 的绝对时间（指的是相对于视频开始的绝对时间偏移）编码。处理方式是：本来也不可能把每一帧都最终放进 LLM，需要采样某些帧。一般做法是每 n 帧抽一，这样如果原始的 FPS 帧率不固定，所抽出的 第 i 个 frame 的时间就指不定是哪一秒的了。于是 VL-2.5 定义好一个标准的帧率，标准帧率的每一帧对应的是位置编码id 的 1,2,3,4,5..。要想用别的采样帧率，则选用位置编码 id {1,2,3,4,..} 中的某些等差序列子集即可。见下图：

![image](https://github.com/user-attachments/assets/a7ec35fc-b815-49d6-bb10-3741cc657cf3)

训练的时候，会各种帧率的都出现，这样 inference 的时候，给任意帧率的video 都支持。注意图中，是选某一种帧率，而不是一个 video 一次要把各种帧率都放进 model 里。

