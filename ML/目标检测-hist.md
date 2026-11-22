# 目标检测发展史

梳理深度学习之后的发展历史. 

目标检测, 主要难在检测多目标. 如果只是一个目标. 直接回归方法预测中心点与半径; 或左上右下坐标就行了. 为解决多目标检测, 就难免遍历: 
- (1). anchor based 遍历, 提前定义好每个位置有啥可能的 bbox;
- (2). anchor-free, 仍然要遍历位置(只是一个位置的 bbox 啥样, model 来 predict 好了).

到了 transformer 时代, 终于是不需要遍历了. 直接突出model 认为的最佳的多个结果. 

## 两阶段检测(选框集合 + 单框独立判断): R-CNN 系列

### (1). R-CNN（2014）: 深度学习只负责特征提取

核心思路：先 rule based 方法找出一堆候选，再用CNN逐个提取特征, 最后 svm 分类

```
原图
 ↓
Selective Search → ~2000个候选框(Region Proposal)
 ↓
每个框 → 缩放到固定大小 → CNN提取特征
 ↓
SVM 分类 + 线性回归修正坐标
```

- Selective Search: 本身不走深度学习 Model，它是一个纯传统计算机视觉算法，基于图像的底层特征（颜色、纹理、尺寸、形状等）来生成候选区域（Region Proposals）。
- R-CNN 里深度学习只负责特征提取，分类和回归都是传统方法。

### (2). Fast R-CNN（2015）: 仍然依赖于selective search(rule based)

做一次 cnn 网络得到feature map; 同时在原图上做 selective search, 得到好多候选; 然后对每个候选: 
- 在 feature map 上映射, 得到这个候选 box 的feature sub-region, 经过 ROI Pooling, 就能获得固定大小的表示(无论候选多大), 然后就可以经过一定网络做分类/回归.
  - ROI Pooling：对任意大小的候选框, 在feature 上映射截取, 再弄成固定大小, 方便接 FC
    - ROI = Region of Interest
  - 可以端到端训练，Loss = 分类Loss + 回归Loss
    - 分类（是什么）+ 回归(定位, 在哪里）
- 瓶颈在 Selective Search

### (3). Faster R-CNN（2015）

借助 RPN, 用神经网络来生成候选框:
- RPN（Region Proposal Network）：遍历画面的每个位置(通过feature-map), 每个位置看k个框
  - feature map 上每个点 → 预设 k 个 Anchor（k个pre-defined 尺度/比例: 128², 256², 512²/1:1, 1:2, 2:1）
    - <img width="300" alt="image" src="https://github.com/user-attachments/assets/cd077d2b-249e-43e6-ba75-8b88e095f3d0" />
  - 每个 Anchor 预测：
    - 是否有物体（2分类)
    - 坐标偏移量（x1, y1, x2, y2, 4个值）. anchor 已经有了尺度/比例的粗值, 这个坐标偏移量是用来精调的

有了候选框, 仍然是用 ROI Pooling(对任意大小的候选框, 在feature 上映射截取, 再弄成固定大小, 方便接 FC), 然后做对这个候选的预测.

整体上算是 end2end, 但是候选框集合, 仍然是笨拙的遍历式的. "端到端"是相对SS而言的，内部训练还是有点麻烦:
- RPN 和 检测头 共享同一个 Backbone, 但是:
  - 早期训练是交替训练的（4步法）：1. 单独训练 RPN; 2. 用RPN结果训练检测头; 3. 再微调 RPN; 4. 再微调检测头
  - 后来才有近似联合训练的方式

note: 送入 "ROI Pooling + 检测头" 的候选集合, 是需要筛选的(fea_map_H * fea_map_W * K 是很大的, 所以要一定方式取top)

---

## 单阶段检测（2015–2018）

### YOLO —— You Only Look Once

(1). yolo-v1（2015）
```
原图 → CNN → 7×7 网格
每个格子预测：
  - 2个框的坐标 (x,y,w,h,confidence) × 2
  - 20个类别概率
输出：7×7×30 的张量 → 直接解码出最终框
```

问题: 每个格子只能预测2个框，密集小目标检测差.

(2). yolo-v2 

引入了和 faster-r-cnn 一模一样的 anchor 机制(也是 pre-define 的 (h,w) 固定的 anchor, predict 的是偏移; 不过yolo-v2 的 anchor 是根据数据集 k-means 选出的, 而不是拍脑袋定的).

那么这时和 faster-r-cnn 啥区别? 
- faster-r-cnn 对于不同的候选, 本质上是分别独自走一个小网络(为此, 要通过 ROI pooling 给这个小网络准备数据), 独自 fowrard, 计算量是要重复的.
  - 因为计算不共享, 所以需要优选出少量的候选, 减少数量, 然后继续下一步
- yolo: 不同的候选, 是统一一次完成的, 所以即使 fea_map_H * fea_map_W * K 很大, 也不怕计算量太大
  - 所有位置所有 Anchor 一次性并行出结果, fea_H × fea_W × K 个候选，一次forward全算完. 卷积天然并行，计算共享，不怕候选多
- 候选框是否需要独立计算, 才是两阶段 vs 单阶段的根本区别:
  - 两阶段：候选框需要独立计算 → 计算重 → 必须筛选 → 流程复杂
  - 单阶段：所有候选共享计算   → 天然并行 → 不需要筛选 → 简单快速

(3). yolo-v3: 多尺度 feature map

不是 3 路不同大小的 conv kernel, 而是一个网络从一串卷积中，抽取不通size 的feature-map, 分别做目标detection.
```
输入 416×416 
 -> conv-> 52×52 特征图 ───→ for 小目标检测
 -> conv-> 26×26 特征图 ───→ for 中目标检测
 -> conv-> 13×13 特征图 ───→ for 大目标检测
```

(4). history
```
- v1: 提出框架，格子预测，速度快但精度差
- v2: 引入 Anchor  ← 现代YOLO的基础
- v3: 多尺度 feature map  ← 多尺度检测成熟
  - v4: 系统整合所有Tricks         ← 工程优化集大成
  - v5: PyTorch重写，工程友好      ← 落地标准
- YOLOX: 去掉Anchor，解耦头        ← 设计理念革新
- v8: Anchor-Free + 统一框架      ← 新一代工程标准
- v10: 去掉NMS                    ← 向DETR思路靠拢
```

### SSD（2016）

它也用到了和 faster-r-cnn 一样的 anchor 机制. ssd 是用不通尺度的 feature-map 检测不同大小的物体, 于是不同尺度用不同大小的 Anchor.

```
抽取 VGG 的多个尺度的特征图：
  38×38 → 检测小物体（Anchor: 小尺度）
  19×19 → 检测中物体
  10×10
   5×5
   3×3
   1×1  → 检测大物体（Anchor: 大尺度）
每层特征图上都密铺各自的 Anchor，直接预测
```

和 yolo-v3, 同样思路. 只是 yolo-v3 有不同尺度的特征融合（加了FPN）.

### RetinaNet + Focal Loss（2017）—— 解决正负样本不平衡

RetinaNet 也是 Anchor-Based. 

单阶段精度差的真正原因：一张图产生 ~100,000 个候选框, 正样本：几十个, 负样本（背景）：几万个. 模型懒得学，直接全猜背景，Loss 就很低了

解法 Focal Loss：
- 普通 CE Loss: Loss = -log(p)
- Focal Loss: Loss = -(1-p)^γ · log(p)
  - 当预测很容易（背景概率高）→ (1-p)^γ 趋近0 → Loss自动降权
  - 当预测很难（正样本） → 权重保留 → 模型专注学难例

单阶段精度第一次超过两阶段, 配合 FPN（特征金字塔）使用，成为经典框架

### anchor-free

anchor based, 本质上是要检测多目标. 如果只是一个目标. 直接回归方法预测中心点与半径; 或左上右下坐标就行了:
- 方案A: (cx, cy, w, h)        ← 中心点 + 宽高
- 方案B: (x1, y1, x2, y2)      ← 左上角 + 右下角
- 方案C: (cx, cy, r)           ← 中心点 + 半径（圆形框）

anchor-free 要支持多目标检测, 仍然是需要位置遍历的:

(1). center net
```
三个独立的预测头：
  ┌─ Heatmap Head → (H/4, W/4, C)     C=类别数         这个位置上: 是否有目标
  ├─ Size Head    → (H/4, W/4, 2)     2=(w, h)        这个位置上: 如果有目标, bbox 多大
  └─ Offset Head  → (H/4, W/4, 2)     2=(Δx, Δy)      这个位置上: 如果有目标, bbox 大小的精调
```

(2). FCOS

遍历特征图每个位置, 问：这个点在某个物体内部吗？
- 特征图上每个点，如果落在某个GT框内部, 这个点就"负责"预测这个框, 因此需要预测该点到框四条边的距离 (l, t, r, b).
- FCOS 需要遍历每个位置, 预测每个点都是否属于目标, 以及预测到四边的距离

---

## 第三次革命：Transformer 时代（2020–至今）

### DETR（2020）—— 彻底扔掉 Anchor 和 NMS

**核心思想：把检测当成集合预测问题**

```
原图
 ↓
CNN Backbone → 特征图 → 展平为序列
 ↓
Transformer Encoder（建立全局依赖）
 ↓
Transformer Decoder: 不是自回归的, 而是并行 100 query tokens in, 100 predictions out
（100个可学习的 Object Query）
 ↓
匈牙利算法做二分图匹配（训练时）
 ↓
直接输出 N 个 (类别, 坐标)
```

- 无 Anchor、无 NMS，流程极简
  - 全局注意力，对遮挡/关系推理更强
- 问题：
  - 训练收敛极慢（需要 500 epoch vs Faster RCNN 的 12）
  - 小目标还是弱

### dino

Transformer 检测的 SOTA 基础.

```
给每个 Query 一个初始位置 (Reference Point)
      ↓
Cross-Attention 不再盲目全图搜索
而是以 Reference Point 为中心局部attend
      ↓
收敛从 500 epoch → 12 epoch
```

Reference Point 怎么来: 从 Encoder 输出中选
```
图片
  ↓
Transformer Encoder
  ↓
输出每个位置的特征 + 显著性得分 (加一个小的分类 Head（线性层）, 每个位置输出一个显著性得分（前景/背景二分类）)
  ↓
取 Top-K 个显著性最高的位置
  ↓
这些位置坐标 → 作为 Reference Point
初始化对应 Query 的位置先验
```

---

## 总体演进脉络

```
手工特征时代          CNN两阶段时代               单阶段时代          Transformer时代
    │                     │                       │                    │
Viola-Jones          R-CNN (2014)            YOLO v1 (2015)      DETR (2020)
 HOG+SVM             Fast R-CNN              SSD (2016)          Def-DETR(2021)
   DPM               Faster R-CNN ◄─────►    RetinaNet(2017)     DINO (2022)
                      (两阶段巅峰)             YOLOv3~v8           RT-DETR(2023)
                                              (工程落地王)
```
