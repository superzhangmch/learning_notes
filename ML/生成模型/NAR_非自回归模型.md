NAR，Non-autoregressive，一般是单步或多步生成。

# iterative NAR

### 《Mask-Predict: Parallel Decoding of Conditional Masked Language Models》 2019.04 https://arxiv.org/pdf/1904.09324

这算是该方法第一篇吗？没深究。paper 中是在做翻译。用的 encoder-decoder 架构。decoder的时候，没用自回归的方式，而是通过多次迭代用非自回归实现解码。

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

扩散语言模型 LlaDa 和它感觉好像（ https://github.com/superzhangmch/learning_notes/blob/main/ML/LLM/%E7%89%B9%E5%88%AB%E7%BB%93%E6%9E%84/202502_LLaDa_%E6%89%A9%E6%95%A3.md ）

### 《Listen and Fill in the Missing Letters: Non-Autoregressive Transformer for Speech Recognition》 2019.11 https://arxiv.org/pdf/1911.04908

它用到了 《Mask-Predict》方法，做的是 asr。它不需要预测 Length token，而是 decoder 预测 EOS token的方式（提前分配足够长的长度）。

<img width="952" height="274" alt="image" src="https://github.com/user-attachments/assets/c65fc44a-a775-44b5-83f5-9fecc2666522" />

NAR 生成&mask 迭代得到结果。

### 《Mask CTC: Non-Autoregressive End-to-End ASR with CTC and Mask Predict》 2020.05 https://arxiv.org/pdf/2005.

它用到了 《Mask-Predict》方法，做的是 asr：

<img width="812" height="684" alt="image" src="https://github.com/user-attachments/assets/442f0cd5-618a-42eb-90e4-89838ffd845a" />

----

## single step NAR

比如 https://arxiv.org/pdf/2206.08317 《Paraformer》。已有笔记在 [here](https://github.com/superzhangmch/learning_notes/blob/main/ML/%E8%AF%AD%E9%9F%B3%E8%AF%86%E5%88%AB/%E9%9D%9E%E8%87%AA%E5%9B%9E%E5%BD%92%E5%B9%B6%E8%A1%8C%E8%A7%A3%E7%A0%81%E7%94%9F%E6%88%90%EF%BC%9Aparaformer%20%E4%B8%8E%20funAsr.md)
