# 目标检测发展史

深度学习之后的发展历史. 

## R-CNN 系列

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

### (2). Fast R-CNN（2015）: 仍然依赖于 rule based selective search

一次 cnn 得到feature map; 同时在原图上做 selective search, 得到好多候选; 然后对每个候选: 
- 在 feature map 上映射, 得到这个候选 box 的feature sub-region, 经过 ROI Pooling, 就能获得固定大小的表示(无论候选多大), 然后就可以经过一定网络做分类/回归.
  - ROI Pooling：任意大小的候选框 → 固定大小特征
  - 可以端到端训练，Loss = 分类Loss + 回归Loss
- 瓶颈在 Selective Search

### (3). Faster R-CNN（2015）

候选框也用神经网络来生成

```
原图
 ↓
Backbone (VGG/ResNet) → 共享特征图
       ↙                    ↘
  RPN网络                 ROI Pooling
(生成候选框)           (用候选框截取特征)
       ↘                    ↙
         Detection Head
         (分类 + 回归)
```

#### RPN（Region Proposal Network）核心设计：
```
特征图上每个点 → 预设 k 个 Anchor（不同尺度/比例）
每个 Anchor 预测：
  - 是否有物体（2分类）
  - 坐标偏移量（4个值）
```

- 💡 创新：
  - **全程GPU**，候选框生成也是网络的一部分
  - Anchor 机制：**预设框 + 预测偏移**，大幅降低回归难度
  - 速度：**5 fps**，精度大幅提升
- ❌ 问题：
  - 两阶段，速度仍有瓶颈
  - Anchor 超参数多（尺度/比例要手调）
  - 小目标还是不好检

---

## 单阶段检测（2015–2018）

> **能不能去掉 Proposal 阶段，一步出结果？**

### 🔵 YOLO v1（2015）—— You Only Look Once

**核心思想：把检测当成回归问题，直接预测**

```
原图 → CNN → 7×7 网格
每个格子预测：
  - 2个框的坐标 (x,y,w,h,confidence) × 2
  - 20个类别概率
输出：7×7×30 的张量 → 直接解码出最终框
```

- 💡 创新：
  - **真正的端到端，一次前向传播出结果**
  - 速度 **45 fps**，实时！
- ❌ 问题：
  - 每个格子只能预测2个框，**密集小目标**检测差
  - 定位精度不如 Faster R-CNN
  - 对不常见比例的物体效果差

### 🟣 SSD（2016）—— 多尺度的单阶段

```
原图 → VGG主干
 ↓
抽取多个尺度的特征图：
  38×38 → 检测小物体（Anchor: 小尺度）
  19×19 → 检测中物体
  10×10
   5×5
   3×3
   1×1  → 检测大物体（Anchor: 大尺度）
每层特征图上都密铺 Anchor，直接预测
```

- 💡 创新：**多尺度特征图 + Anchor**，兼顾速度和精度
- ❌ 问题：浅层特征语义信息弱，小目标检测仍不理想

### 🔴 RetinaNet + Focal Loss（2017）—— 解决正负样本不平衡

**发现了单阶段精度差的真正原因：**
```
一张图产生 ~100,000 个候选框
正样本：几十个
负样本（背景）：几万个

模型懒得学，直接全猜背景，Loss 就很低了
```

**Focal Loss 解法：**
```
普通 CE Loss:    Loss = -log(p)
Focal Loss:      Loss = -(1-p)^γ · log(p)

当预测很容易（背景概率高）→ (1-p)^γ 趋近0 → Loss自动降权
当预测很难（正样本）      → 权重保留 → 模型专注学难例
```

- 💡 创新：**单阶段精度第一次超过两阶段**
- 配合 FPN（特征金字塔）使用，成为经典框架

### YOLO 进化线（2016–2020）

| 版本 | 年份 | 核心改进 |
|------|------|---------|
| YOLOv2 | 2016 | 引入 Anchor、BatchNorm、多尺度训练 |
| YOLOv3 | 2018 | 3个尺度预测、Darknet53、效果大幅提升 |
| YOLOv4 | 2020 | Mosaic增强、CSP结构、CIOU Loss，工程集大成 |
| YOLOv5 | 2020 | PyTorch实现、工程友好，成为业界标准 |

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
Transformer Decoder
（100个可学习的 Object Query）
 ↓
匈牙利算法做二分图匹配（训练时）
 ↓
直接输出 N 个 (类别, 坐标)
```

- 💡 创新：
  - **无 Anchor、无 NMS**，流程极简
  - 全局注意力，对遮挡/关系推理更强
- ❌ 问题：
  - 训练收敛极慢（需要 500 epoch vs Faster RCNN 的 12）
  - 小目标还是弱

---

### Deformable DETR / DAB-DETR / DN-DETR（2021–2022）

逐步解决 DETR 的收敛慢问题：
- **Deformable DETR**：注意力只看少数关键点，快 10 倍
- **DN-DETR**：训练时加噪声正样本，加速收敛
- **DINO**：目前 Transformer 检测的 SOTA 基础

---

## 🗂️ 总体演进脉络

```
手工特征时代          CNN两阶段时代            单阶段时代          Transformer时代
    │                     │                       │                    │
Viola-Jones          R-CNN (2014)            YOLO v1 (2015)      DETR (2020)
 HOG+SVM             Fast R-CNN              SSD (2016)          Def-DETR(2021)
   DPM               Faster R-CNN ◄─────►  RetinaNet(2017)      DINO (2022)
                      (两阶段巅峰)            YOLOv3~v8          RT-DETR(2023)
                                             (工程落地王)
```

---

## 💡 每一代解决的核心问题

| 时代 | 核心痛点 | 解决方案 |
|------|---------|---------|
| R-CNN | 特征弱 | 用CNN提特征 |
| Fast R-CNN | 重复计算 | ROI Pooling共享特征图 |
| Faster R-CNN | Proposal慢 | RPN网络生成候选框 |
| YOLO | 两阶段慢 | 直接回归，单次前向 |
| RetinaNet | 正负样本失衡 | Focal Loss |
| FPN | 多尺度弱 | 特征金字塔 |
| DETR | Anchor/NMS繁琐 | Transformer + 集合预测 |

---

> 🎯 **一句话总结整个历史：**
> 每一代研究者都在问同一个问题——
> **"上一代方法最慢/最差的那个环节，能不能用神经网络替换掉？"**
> 替换完了，新的瓶颈出现，下一代继续替换，就这样滚动到了今天。
