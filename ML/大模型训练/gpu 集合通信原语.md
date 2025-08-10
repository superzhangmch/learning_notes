# gpu 集合通信原语：

总结起来看，这些功能基本都通过 tree 或 ring 完成的。

---

by chatgpt

## Broadcast（广播）

**功能**：一个 GPU 的数据 → 所有 GPU。

**工作原理**：

* **Tree 算法**常用：

  1. 源 GPU（root）先把数据发给一半 GPU。
  2. 收到数据的 GPU 再发给其他 GPU，形成二叉树扩散。
  3. 最多 **log₂(N)** 轮广播就能覆盖所有 GPU。
* **Ring 算法**也能做广播：

  1. 数据分成 N 片。
  2. 每个 GPU 按环路顺序接力传递，直到所有 GPU 拿到完整数据。
  3. 适合大数据量，带宽利用率高。

📌 **特点**：Tree 延迟低，Ring 吞吐高。
 
## Reduce（归约）

**功能**：所有 GPU 的数据 → 聚合到一个 GPU（root），例如做求和、最大值等。

**工作原理**：

* **Tree Reduce**：

  1. 所有 GPU 分成两半，后一半发给前一半并做归约运算（sum/max/...）。
  2. 递归进行，直到数据集中到 root。
  3. 每轮传输距离减半，延迟 \~log₂(N)。
* **Ring Reduce**：

  1. 数据分成 N 片。
  2. 沿环路传递时，每个 GPU 把收到的数据和自己本地的对应分片做归约。
  3. 最终 root GPU 拥有完整归约结果。
  4. 带宽利用率高，但延迟较高。
 
## All-Reduce（全归约）

**功能**：所有 GPU 数据聚合 → 每个 GPU 都有聚合结果（常用于分布式训练的梯度同步）。

**工作原理**（NCCL 默认用 **Ring All-Reduce**）：

1. **阶段 1：Reduce-Scatter**

   * 数据分成 N 片。
   * 沿环路传递，每个 GPU 只保留一片聚合结果。
2. **阶段 2：All-Gather**

   * 把每个 GPU 聚合好的那片数据再沿环路广播回去。
3. 完成后，所有 GPU 都有全量聚合结果。

**优化**：

* 对小数据用 **Tree All-Reduce**（延迟低）。
* 对大数据用 **Ring All-Reduce**（带宽利用率接近 100%）。
* 大规模集群用 **分层 All-Reduce**：节点内（NVLink）+ 节点间（InfiniBand）。
 
## Gather（收集）

**功能**：所有 GPU 数据 → 一个 GPU 上的完整集合。

**工作原理**：

* **Tree Gather**：

  1. 所有 GPU 数据逐层向 root 汇聚（类似 Tree Reduce，但不做计算，只是搬运）。
  2. 延迟 \~log₂(N)。
* **Ring Gather**：

  1. 分片沿环路送到 root。
  2. 适合大数据量传输，但实现较少用 ring，因为单 root 会成为瓶颈。
 

## All-Gather（全收集）

**功能**：所有 GPU 收集到所有 GPU 的数据。

**工作原理**（Ring All-Gather）：

1. 数据分成 N 片（每个 GPU 初始只有 1 片）。
2. 每一轮将自己已有的片发给下一个 GPU，并接收来自上一个 GPU 的片。
3. N-1 轮后，所有 GPU 都有全量数据。

📌 **特点**：All-Gather = Gather + Broadcast 的组合。
 
## Scatter（分发）

**功能**：一个 GPU 的数据分片 → 不同 GPU（每 GPU 得到一部分）。

**工作原理**：

* **Tree Scatter**：

  1. Root GPU 先发一半数据给另一 GPU。
  2. 每个收到数据的 GPU 再将其中一部分发给别人，直到完成分发。
* 对称于 Gather，延迟 \~log₂(N)。
 
## Reduce-Scatter（归约分发）

**功能**：所有 GPU 数据先归约，然后将结果分片发给不同 GPU。

**工作原理**（Ring Reduce-Scatter）：

1. 数据分成 N 片。
2. 沿环路传递时，每个 GPU 对收到的对应分片做归约。
3. 最终每个 GPU 只保留一片聚合好的数据（分布在不同 GPU 上）。

📌 **用途**：All-Reduce 的第一阶段就是 Reduce-Scatter，可节省内存和带宽。
 

## 🔍 总结性能比较

| 原语             | 常用算法 | 延迟优势 | 吞吐优势 | 常用场景    |
| -------------- | ---- | ---- | ---- | ------- |
| Broadcast      | Tree | ✔    | -    | 模型参数分发  |
| Reduce         | Tree | ✔    | -    | 结果汇总    |
| All-Reduce     | Ring | -    | ✔    | 梯度同步    |
| Gather         | Tree | ✔    | -    | 数据合并    |
| All-Gather     | Ring | -    | ✔    | 推理数据全量化 |
| Scatter        | Tree | ✔    | -    | 数据分片    |
| Reduce-Scatter | Ring | -    | ✔    | 内存优化同步  |
