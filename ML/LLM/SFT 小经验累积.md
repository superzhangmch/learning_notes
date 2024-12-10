# SFT 小经验累积

1. 一般有一两百条数据，两三个 epoch 就可以很好的 SFT 了。
2. SFT 时混合通用语料很重要。如果不混合，可能需要更多的 epoch 才能收敛到SFT数据集，且这时候收敛后其实已经在过拟合了————影响其他任务的通用表现了。一两百条数据，混入5倍通用数据是个不错的选择。具体多少可以尝试，总之 sft过程对于混合比例还是很敏感的。

如果直接令生成 json 格式输出，有说效果不好的，有说其实没问题的。说明不总是很好。

DPO 最少数据量，一般是1000：
- https://www.reddit.com/r/LocalLLaMA/comments/1d3zvyo/whatre_your_typical_hyperparameters_for_fine/
  > Dataset for DPO/ORPO should be at least 1000 samples and for SFT I would say over 5000 samples. Watch out for any biases in DPO/ORPO dataset ...
- https://www.sitepoint.com/fine-tuning-llm-with-direct-preference-optimization-dpo/#h-creating-a-dpo-dataset
  > You’ll generally need between 500 and 1,000 pairs of data at a minimum to have effective training without overfitting. The biggest DPO datasets contain up to 15,000–20,000 pairs.
  
