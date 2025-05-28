# fastspeech2 《FASTSPEECH 2: FAST AND HIGH-QUALITY END-TOEND TEXT TO SPEECH》 https://arxiv.org/pdf/2006.04558

### 原理
首先对于原始 text 序列，要经过 text-frontend 转化为 Phoneme（音素） tokens 序列，然后才开始展开工作。

![image](https://github.com/user-attachments/assets/6c56557b-b6fb-4d84-9c3b-8942013b4ca5)

它用到了 transformer，但是并不是**自回归方式**生成 mel-谱的帧的。而 Phoneme token 的发音长度不一，这就有问题是：怎么决定最终 result audio 的时长，以及每个 Phoneme token 的时长问题。

它所用的方法是（继承自 fastspeech_v1)，预测出每个 Phoneme token 时长，然后根据这个时长，把序列展开。展开结束后，序列长度就和 result mel-谱 seq_len 一样了。见下图：LR 负责音素与mel帧：

![image](https://github.com/user-attachments/assets/018b02f7-22ea-43e2-a71b-4ed122ad9591)

它用到了 Energy、pitch、duration 等特征，这些都是要用专门工具抽取出来的，并且会有监督 MSE loss 来学习它们。最终是多 loss 学习。

### FastSpeech 2s

它还可以跳过 mel-谱 阶段，直接生成 audio wave。

![image](https://github.com/user-attachments/assets/2b522d53-2b30-4f77-a6de-817cf8783f6f)

该方式效果还可以（比 tacotron2 还要好些）：

![image](https://github.com/user-attachments/assets/8fe7a18c-f84a-48ba-abf5-804efbe6ca27)
