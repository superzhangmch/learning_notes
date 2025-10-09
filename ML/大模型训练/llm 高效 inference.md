假设一个 LLM server，有源源不断的请求到来。那么怎么高效推理呢？

### pagedAttention
vllm 的做法。大概说，GPU 没有真正的“分页（paging）机制”，所以它在软件层面“模拟”出一种分页式内存管理，用来高效管理 kv-cache。它的核心要义是：kv-cache 可以物理上不连续存储，而是通过指针指向他。这样就给 kv-cache 共享复用留了余地（单 prompt 多采样、beam search 之类都能受益）。

**page 大小：**
一个 page 一般 1MB。对于61层，每个压缩后的 kv-cache 512维，并按 fp16 算，则 1MB/(61 x 512 x 2) = 16, 即一个 page 存 16 个 token。如果不是 MLA，那么就需要 GQA/MQA, kv-heads-num 就需要很小。这样一个 1MB 的 page 才能维持稍微大点的 kv 数。从这也说明为啥 page 要这么大（而非 cpu-mem 的 4K 那么小）。

### batch 与 动态连续batch
- batch：请求会组织成 batch 进行，而不是每个请求独立做生成
- continuous batching：即使 batch 化，也不是说这一批执行完后，才开始下一个 batch——batch 内有的生成结果短，有的长，这样会计算资源浪费。而是 batch 内算完的马上退出，从而把新的添加进来。
  - vLLM、Hugging Face 的 Text Generation Inference（TGI），都支持它。

### 不同长度怎么 batch

