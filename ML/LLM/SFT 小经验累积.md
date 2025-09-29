# SFT 小经验累积

### 需要多少数据

一般有一两百条数据，两三个 epoch 就可以很好的 SFT 了。

### 混合通用语料

SFT 时混合通用语料很重要。如果不混合，可能需要更多的 epoch 才能收敛到SFT数据集，且这时候收敛后其实已经在过拟合了————影响其他任务的通用表现了。一两百条数据，混入5倍通用数据是个不错的选择。具体多少可以尝试，总之 sft过程对于混合比例还是很敏感的。

### RL

如果同时还有 KTO 等，如果不能有通用预料，应该先做KTO等，后做 SFT。

如果直接令生成 json 格式输出，有说效果不好的，有说其实没问题的。说明不总是很好。

DPO 最少数据量，一般是1000：
- https://www.reddit.com/r/LocalLLaMA/comments/1d3zvyo/whatre_your_typical_hyperparameters_for_fine/
  > Dataset for DPO/ORPO should be at least 1000 samples and for SFT I would say over 5000 samples. Watch out for any biases in DPO/ORPO dataset ...
- https://www.sitepoint.com/fine-tuning-llm-with-direct-preference-optimization-dpo/#h-creating-a-dpo-dataset
  > You’ll generally need between 500 and 1,000 pairs of data at a minimum to have effective training without overfitting. The biggest DPO datasets contain up to 15,000–20,000 pairs.
  
### 多轮训练，需要 mask 哪些

```
user = A
assistant = B
user = C
assistant = D
user = E
assistant = F
user = G
assistant = H
```

多轮如上. 常见的三种 masking 策略

（1）、 **全 assistant 策略（最常见）**

* **mask**：system + 所有 user 的内容
* **保留**：所有 assistant 的内容（B、D、F、H）

损失在 **每一轮 assistant 回复**上都会算。
**优点**：利用了更多监督信号，训练效率高。
**缺点**：模型学到的是“每轮都要立刻答复”，有时在长对话预测里泛化不如只训最后一轮稳定。

（2）、 **只最后一轮 assistant 策略**

* **mask**：system + 所有 user 的内容 + 前面所有 assistant 回复（B、D、F）
* **保留**：最后一轮 assistant 回复（H）

损失只在最后一个 assistant 回复上算。
**优点**：训练目标和推理场景一致（给定完整上下文，只预测最后一轮回答）。
**缺点**：有效监督少，收敛更慢，需要更多数据。

（3）、 **混合策略（部分项目用）**

* 在同一批数据里，一部分样本训练全 assistant，另一部分只训练最后一轮。
* 或者在 curriculum learning（课程学习）里，先训全 assistant，再训只最后一轮。

平衡数据利用率和推理一致性。

业界实践对比

* **ChatGPT / LLaMA / Alpaca 类开源 SFT**：通常采用 **全 assistant 策略**。
* **面向真实部署（对话机器人、客服助手）**：更偏向 **只最后一轮策略**，因为推理时就是“给定上下文 → 预测最新回复”。
* **大规模商用产品**（如 Claude、GPT 系列）：一般会混合使用，还会加上额外的 **system prompt** 保持 persona。
