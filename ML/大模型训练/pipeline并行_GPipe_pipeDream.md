# pipeline 并行

### 相关 paper 

- gPipe（谷歌）：《GPipe: Efficient Training of Giant Neural Networks using Pipeline Parallelism》 https://arxiv.org/abs/1811.06965
- pipedream(微软）：《PipeDream: Fast and Efficient Pipeline Parallel DNN Training》 https://arxiv.org/pdf/1806.03377
- pipeDream-2BW、pipeDream-flush（微软）：《Memory-Efficient Pipeline-Parallel DNN Training》 https://arxiv.org/pdf/2006.09503

---

### 为啥用 pipeline 并行

如果 model 太大，单张 gpu 训不起来，这时候就需要想办法——比如用 deepspeed ZeRO 技术。但是如果 model 太大以至于，一个 gpu 连参数都放不下（比如当前 LLM），这时候就需要把 model 拆分了，即需要 model 并行。

假设model 是从下往上一层层的。那么拆分方式有两种：
- 纵向切分，也就是每一层都切开到不同 gpu，这就是张量并行。
- 横向切分，也就是每个 gpu 放置 model 的不同层。这就是 pipeline 并行。

除了 model 太大，《PipeDream》paper 更关注的是数据并行的一些弊端，从而想用 pipeline 并行来解决它：
- 数据并行的通信瓶颈：数据并行在每个小批量后需要同步整个模型的参数，通信量和模型大小成正比。随着模型变大（如 VGG16）、GPU 计算速度提高，通信时间可能占到总训练时间的 70%–85%，扩展性大幅下降。Pipeline 并行只需在不同阶段之间传递激活值和梯度，通信量极大降低。
- 结合模型并行和数据并行的优点：不同类型的层（例如卷积层、全连接层）在模型并行和数据并行下的表现差异很大。Pipeline 并行允许在一些阶段用模型并行、另一些阶段用数据并行，实现计算负载均衡和通信量最小化。
- 适应更大模型和慢网络环境：在网络带宽有限（如公有云 10Gbps）的环境中，大模型的纯数据并行训练速度可能比单机还慢。Pipeline 并行可以在这种情况下依然保持较高吞吐量（论文实验中可比数据并行快 3–5 倍）。

---

### pipeline 并行怎么做

<img width="810" height="554" alt="image" src="https://github.com/user-attachments/assets/1e4cee4a-1130-415c-b158-c1f7d9449c08" />

如图，按层把 model 切分成多个组，每个组用一个 gpu。单个gpu内训练指定的这些 layers，和上下游的 gpu 联动，传递梯度或激活值。至于怎样切分更好，见《pipeDream》、《GPipe》二文。

如下，pipeline 并行，可以和数据并行联合使用：

<img width="790" height="544" alt="image" src="https://github.com/user-attachments/assets/adbce50f-9910-4505-8f11-f2a04d0faf79" />

pipeline 并行时，如果作 activation checkpointing，切分点很自然地选用 pipeline 切分点就行：每个 gpu 把 input 激活存下来用于重计算即可。另外 pipeline 没法精确还原 batch Norm，具体见《GPipe》。

**（1）朴素做法**

然后具体怎么操作呢？看下图：最直接的就是图中 (b) 那样。但是过程中只有一个 gpu 在忙，资源浪费严重。

<img width="1224" height="574" alt="image" src="https://github.com/user-attachments/assets/2b9b3b39-8bba-4203-8837-427aed67e59f" />

**（2）微批化**

于是可以 micro-batch 的方式(上图中 (c), 即 GPipe 方法；或下图)，把大的 batch_size 拆小，这样 gpu 利用率会变大，但是仍然有 idle bubble 在（假设 P 路并行， 微批数是 M，则 bubble 占比是 $\frac {P-1}{M+P-1}$)。

<img width="1540" height="444" alt="image" src="https://github.com/user-attachments/assets/c662cef2-a330-4bc0-996d-c0b0f9f9096e" />

如上，按一个 backward 是 forward 的 2 倍时间算。一个 forward 算作一格时间，则一个完整周期共有 33 格时间，共36 格 idle。数得 bubble 率为 36/(4*33)=0.273， 或带入 $\frac {P-1}{M+P-1}$ 也可得。

**（3）1F1B=（1 forward 1 backward）**

《pipeDream》发现，可以令 forward 与 backward 按微批做交错。这时候的 bubble 率一样，但是对显存有好处。如下图，和上图一样的任务。可以看到一个一个数出的一个周期时间（33格），以及 idle（36格） 和 上面 GPipe 方案一样。

<img width="1578" height="372" alt="image" src="https://github.com/user-attachments/assets/8b16efe2-506b-4ed6-af55-1e6899f73afc" />

startup stage：怎么确定 warm-up phase 长度？

**（4）interleaved 1F1B**

<img width="1614" height="620" alt="image" src="https://github.com/user-attachments/assets/e0927137-d598-4dfb-9443-ffa92961fd21" />

