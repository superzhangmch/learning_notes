## 《Mask-Predict: Parallel Decoding of Conditional Masked Language Models》 2019.04 https://arxiv.org/pdf/1904.09324

paper 中是在做翻译。用的 encoder-decoder 架构。decoder的时候，没用自回归的方式，而是通过多次迭代用非自回归实现解码。

**怎么解码：**

```
预测出解码长度 N：encoder 加一个 LENGTH token，指示解码长度

input = [MASK] * N

for i in range(K): 
  output = forward(intput)
  把 input 中低置信的预测 token，换成 MASK。每次要减少 mask 数量（线性递减）
  input = output
```

这样逐步迭代，就实现了解码。每一次迭代，是一次预测 N 个 token，但是迭代 k 次。

**怎么训练：**

随机 mask 掉序列中一部分，预测全序列。

----

## 《Mask CTC: Non-Autoregressive End-to-End ASR with CTC and Mask Predict》 2020.05 https://arxiv.org/pdf/2005.

它用到了 《Mask-Predict》方法，做的是 asr：

<img width="812" height="684" alt="image" src="https://github.com/user-attachments/assets/442f0cd5-618a-42eb-90e4-89838ffd845a" />
