# pipeline 并行

### 相关 paper 

- gPipe（谷歌）：《GPipe: Efficient Training of Giant Neural Networks using Pipeline Parallelism》 https://arxiv.org/abs/1811.06965
- pipedream(微软）：《PipeDream: Fast and Efficient Pipeline Parallel DNN Training》，简记为《PipeDream》 https://arxiv.org/pdf/1806.03377
- pipeDream-2BW、pipeDream-flush（微软）：《Memory-Efficient Pipeline-Parallel DNN Training》，简记为《PipeDream-2BW》 https://arxiv.org/pdf/2006.09503
- megatron-LM：《megatron-LM：Efficient Large-Scale Language Model Training on GPU Clusters Using Megatron-LM》，简记为《megatron-LM》 https://arxiv.org/pdf/2104.04473

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

如图，按层把 model 切分成多个组，每个组用一个 gpu。单个gpu内训练指定的这些 layers，和上下游的 gpu 联动，传递梯度或激活值。至于怎样切分更好，见《pipeDream》、《GPipe》二文，AI总结道：GPipe：每层可以提供可选的计算成本估算函数，基于计算成本作切分，目标是最小化各partition间计算时间的方差。。pipeDream：自动剖析：先在单机上运行模型，测量每层的计算时间和输出大小；然后动态规划优化：用算法自动决定如何将连续的层分组成"阶段"，并分配给不同机器，目标是让各阶段工作量均衡、通信量最小。GPipe 看计算，pipeDream 看计算+通信】

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

《pipeDream》发现，可以令一个个微批的 forward 与 backward 交错。bubble 率和不这样一样，但是对显存有好处（）。如下图，和上图一样的任务。可以看到一个一个数出的一个周期时间（33格），以及 idle（36格） 和 上面 GPipe 方案一样。

<img width="1578" height="372" alt="image" src="https://github.com/user-attachments/assets/8b16efe2-506b-4ed6-af55-1e6899f73afc" />

warmup 阶段最佳微批数：据《pipeDream》，NUM_OPT_ACTIVE_MINIBATCHES= NOAM = ⌈(总机器数) / (输入阶段的机器数)⌉。目标:是让所有机器在稳态时都保持忙碌，而输入阶段是流水线的"瓶颈" - 它控制着新 minibatch 的注入速度。如果每个stage 平均切分，机器数也一样，则 NOAM=并行数。

当 1F1B 交错时，如图是假设时间上精确地 2个F = 1个B。而实际只是近似如此，会不会导致上图F与B格子对不齐，从而影响效率？实际上GPU之间并不要求非得对齐。每个 GPU 上，只要 1F-1B-1F-1B 这样交错着执行就行，只要任务来就执行；没任务等等，如果任务堆积，连续不停歇执行。

**（4）interleaved 1F1B**

《megatron-LM：Efficient Large-Scale Language Model Training on GPU Clusters Using Megatron-LM》中提到了 interleaved 1F1B 的方式。里面对于 model layers 的切分，不是直接每个设备认领一段，而是认领不相邻的两段（所以 interleaved 并不指的 1F-1B-1F-1B 的交错；而是 layers 的交错），如图：

<img width="1116" height="514" alt="image" src="https://github.com/user-attachments/assets/cb303e9f-cda2-4940-a3bc-36c5c9f749b6" />

设备数不变，微批大小与数量都不变时，如下图这样执行。通过数格子，可以看到它的总执行时间更短（28.5 < 33)，且 bubble 率更小：

<img width="1614" height="620" alt="image" src="https://github.com/user-attachments/assets/e0927137-d598-4dfb-9443-ffa92961fd21" />

**（5）zero-bubble**

《ZERO BUBBLE PIPELINE PARALLELISM》 https://arxiv.org/pdf/2401.10241

<img width="1300" height="482" alt="image" src="https://github.com/user-attachments/assets/aab71194-17e6-456c-b281-9f67535c4c1d" />

backward 时间为 forward 的 2 倍。这是基于 DNN 中大部分操作是 $W \cdot f(x)$ 矩阵乘法的缘故, 反向传播时要关于 W 求梯度，也要关于 input f(x) 求。时间各占一半。所以作者把 backward 分成了这两者，分别用 W 与 B 表示。从而 F，B，W 数量一样。然后基于此分解，精心设计了 zero-bubble 的调度法。另外paper中也有关于怎样做自动化编排。

**（6）seq-1F1B**

https://arxiv.org/pdf/2406.03488v1 据 ai，在普通 1F1B（包括 interleaved）里，最小调度单位是一个 micro-batch。对于单条样本的长序列，会作为一个整体，forward 完了才能 backward。在 Seq1F1B 里，这个长序列组成的 micro-batch 会沿着 token 维度切成多个 segment。最终也是要flush的。它还可以和 zero-bubble 技术结合。

具体得看 paper。

----

## 不停歇的 pipeline-并行

以上方式，都是要让效果完全等同于不走 pipeline。还有方式是，让流水线完全不停歇，一直流下去，不过会导致并等同于非流水线训练（而只是近似）。《PipeDream》、《PipeDream-2BW》中的方法，就是如此。

当前的 LLM 训练一般不用这样方式。

该方式下，起始的 startup 阶段后，进入稳定态。稳定态下，每个 gpu 实例上都是一直不停执行 1F-1B-1F-1B：《PipeDream》是 1F1B 中的每个 backward，都会当场更新参数，而《PipeDream-2BW》则稍等下再更新，但仍然没有上面那样的统一划线的参数更新的 flush。

<img width="1094" height="442" alt="image" src="https://github.com/user-attachments/assets/4b7674ed-9203-4e2a-a9c4-4e4f329003fc" />

如上图：稳定态后，不再有 bubble 存在，从而最大程度利用 gpu。

<img width="1244" height="722" alt="image" src="https://github.com/user-attachments/assets/898bda98-2df0-40c1-b339-c5e2d8c694c4" />

如上图：从 input stage => output stage, 每个微批的 B 与 F 之间的距离（等待时间，从最远线性变为 0。对 output stage（流水线最后一个 gpu）来说：当前微批才做完 forward，马上做它的 backward。

关于不停流 pipeline 并行的参数更新方式，有这么几种：

**（1）每个 backward都更新参数：需参数版本管理**

如果参数不作版本管理，那么除了output stage GPU 外，其他 gpu 上 同一个 microbatch 的 F 与 B 之间有其他微批做参数更新，导致 Backward 时的用到的参数值和 forward 时的参数值不一样，算出的梯度也有问题。所以需要参数版本化管理，核心就是保证：F 与 B 时用到了同样取值的参数。

版本化方式有两种（《pipeDream》）：Weight Stashing 或 Vertical Sync。

**Weight Stashing** 是记录下一个 microbatch 作 forward 时的参数镜像，到了作 backward 时仍然用这一份。不同 stage gpu 上需要同时存的参数数量不等（每个微批都需要存，但是需要存的生命周期不同。导致gpu 存的版本数不同）：从 input stage => output stage 线性递减到 0。这样做没解决的问题是：同一个 microbatch，在不同的 stage，仍然用了不同版本的参数。而 **Vertical Sync** 就是要解决这个问题。它的方法是，记录下每个微批在 input stage 入口处的参数版本，在其他所有 stage 在forward 阶段也应该用同样的"历史"版本，这样它存的版本就更多了(output stage 也要存同样多的版本）。

weight stashing 示意图如下（对当前微批，用最新参数做 forward，顺便存下此参数；backward 的时候要用存下的参数；做完backward，马上更新参数）：

<img width="1266" height="866" alt="image" src="https://github.com/user-attachments/assets/1dc6c2b0-cf8c-4017-babc-df31ca6361bd" />

有全局 flush 时参数更新是 $w^{(t+1)} = w^{(t)} - \nu \cdot \nabla f(w_1^{(t)}, w_2^{(t)}, \ldots, w_n^{(t)})$, 而 weeight stashing 的参数更新等价于说(可以看到不同stage所基于的参数版本不同)：

$$w^{(t+1)} = w^{(t)} - \nu \cdot \nabla f(w_1^{(t-n+1)}, w_2^{(t-n+2)}, \ldots, w_n^{(t-2)}, w_n^{(t-1)} w_n^{(t)})$$

Vertical Sync 示意图如下（对当前微批在各个stage作 F 与 B时的参数版本，都是 input stage 时的最新参数的那个版本，这个版本号随着pipeline 传到所有stage）：

<img width="1240" height="586" alt="image" src="https://github.com/user-attachments/assets/0e178c06-806f-4adf-b66c-6ff0da957009" />

它的参数更新等价于说（虽然同一个微批在不同 stage 所基于的参数版本一样，但是延后n步。每次都是用历史上某次参数的梯度，更新最新参数）：

$$w^{(t+1)} = w^{(t)} - \nu \cdot \nabla f(w_1^{(t-n+1)}, w_2^{(t-n+1)}, \ldots, w_n^{(t-n+1)})$$

上面这样的多数据版本导致的问题是，本来为了省显存采用 pipeline 并行，这下把省了的又弄回来了。不过其实还是省了，因为多版本存储的时候，每个节点这时候也只是参数部分占用的多了。而其它梯度、优化器状态、激活值等，都是非流水线并行的 1/N。而多版本参数，最多不过相当于存了全部参数（这是假设 model 终究还是不是那么那么大吧）。

**（2）不是每个 backward 都更新参数，对参数双 buffer 方式，汇聚一批更新一批**

如下图。每跑一定数量（足够多的）微批，梯度累积后做一次参数更新。从此起，所有forward 都要用新参数，直到下一次参数更新。而对于 backward，都用 forward时的参数版本（要么是最新，要么是次新。总之两个版本足以。）

<img width="1376" height="574" alt="image" src="https://github.com/user-attachments/assets/720b1927-c2fd-40d8-a5ed-7ccde541e0b7" />

如上图如果梯度累积的步数刚刚好，则差不多所有微批都是横跨参数更新“斜线”的。这表现为它的参数更新，正好落后一步：总是用上上次参数的梯度更新上次参数，然后得到最新参数。

如果梯度累积的步数很大（远超刚刚好；既上图两斜线距离很大），那么大部分微批用了最新版本参数做的backward。这时候就差不多就是一般train时的没有时延了。

原始paper中图：

<img width="1158" height="456" alt="image" src="https://github.com/user-attachments/assets/6008eb81-450c-4af5-945b-5eb4e876e87f" />
