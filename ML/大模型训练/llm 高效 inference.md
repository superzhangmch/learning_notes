假设一个 LLM server，有源源不断的请求到来。那么怎么高效推理呢？

### pagedAttention
----
vllm 的做法。大概说，GPU 没有真正的“分页（paging）机制”，所以它在软件层面“模拟”出一种分页式内存管理，用来高效管理 kv-cache。它的核心要义是：kv-cache 可以物理上不连续存储，而是通过指针指向他。这样就给 kv-cache 共享复用留了余地（单 prompt 多采样、beam search 之类都能受益）。

**page 大小：**
一个 page 一般 1MB。对于61层，每个压缩后的 kv-cache 512维，并按 fp16 算，则 1MB/(61 x 512 x 2) = 16, 即一个 page 存 16 个 token。如果不是 MLA，那么就需要 GQA/MQA, kv-heads-num 就需要很小。这样一个 1MB 的 page 才能维持稍微大点的 kv 数。从这也说明为啥 page 要这么大（而非 cpu-mem 的 4K 那么小）。

### continuous batching
----

**batch化**

首先不会是每个请求独立处理，而是会组织成 batch 进行。一般的 deep-learning model，在线推理如果要 batch 化处理请求，可以等够（带超时的等）一个固定 batch，并固定时间完成推理。LLM 生成用时不一，没法这样做：等够 N 个请求后，统一做 prefill，然后统一生成。这样资源利用率低，延迟大。

假如就要这么做（这叫做 dynamic batching），鉴于 prompts 长度不一，需要 padding，需要注意 padding 的方向：
- LLM 训练的时候，一般是右 padding。而 inference 的时候，应该是左 padding。
  - 只有 batch 操作才需要 padding。所以如果一次 inference 一个，没必要 padding。
  - 如果右 padding，每个序列的待生成的 tokens 位置不能对齐，没法做 batch 化的生成（或者说硬要做，很麻烦，还并行度不高）。
  - 训练时右 padding，infer 时左 padding，不一致不会有问题吗？答案是不会，因为 attention mask 会把 padding mask 掉（但是统一施加的位置编码，还是会带来一些差异）。

**continuous batching**

LLM 要高效推理，应该用 continuous batching。该方法出于 《Orca: A Distributed Serving System for Transformer-Based Generative Models》 https://www.usenix.org/system/files/osdi22-yu.pdf ，里面叫它 iteration-level scheduling， vllm 中叫它 continuous batching。

它的思想是：
- 可以把多序列构成的 batch 直接 flatten 成一个长长的新序列，然后在这个新的 batch_size=1 的序列上进行 inference。
  - 为什么可行：
    - 只有 attn $\sigma(QK')V$ 这一步依赖于序列。对这一步，每个序列独立进行。
    - 其他的（input=> QKV_proj 与 attn_output => final_output）：都是在单个token粒度上进行的，flatten操作对他们没任何影响。
    - <img width="556" height="346" alt="image" src="https://github.com/user-attachments/assets/cb82a5a9-2ceb-4bee-ab25-083dbcdf9cd8" />
- 每推进一 step，把生成完成的 seq 剔除，同时可以添加新的序列（prompt）。
- prefill 与 decode 可以混在一起进行

《Orca》还提到了 selective batching：它是 continuous batching 的进一步，讲怎样做选择 batching。

### "连续" 怎么做的

这里 https://www.aleksagordic.com/blog/vllm 讲 continuous batching 是怎么个连续，讲得很清楚（但是它只是关注 flatten 成一行）：

（1）、把不同序列都 flatten 成一行：

<img width="858" height="696" alt="image" src="https://github.com/user-attachments/assets/ca061784-b457-4422-b8d2-21a073a20d41" />

（2）、做 prefill 后（实际中，prefill 和 decode 可以混杂一起做）：

<img width="900" height="402" alt="image" src="https://github.com/user-attachments/assets/38f60e05-bc9e-4c1d-9d7c-7c1390526a81" />

（3）、decode 一步：

<img width="850" height="253" alt="image" src="https://github.com/user-attachments/assets/1ecd56e8-b09a-43ad-86c2-1aa5a88d1026" />

### batch 内序列变长（prompt与生成都是不等长的），以及位置编码，怎么处理的

**变长batching问题：**

鉴于只有 $\sigma(qK')V$ 才是不能 token 并行的，连续batching的不等长序列拼接，影响到的也只有 attn 部分。它是通过每个序列独立计算规避这问题的；既然 attn 不能batch计算，就独立算。当然也可以当成拼接后的长序列用巧妙设置的 attn mask 来解决。具体实际细节没看。

注意 $\sigma(qK')V$ 没有参数，且对于单个序列，也有多个 heads，计算量也是不小的，独立计算它并不会有啥问题。

**位置编码:**

从上面图可以看到，不同序列拼后，每个序列内部是有独立的位置编码的。摘录如下：

```
input_ids = [1,2,3,4,5, 1,6,5,7,8,9,10, 1,12,13]
positions = [0,1,2,3,4, 0,1,2,3,4,5,6,   0,1,2]
```

也就是计算 $\sigma(qK')V$ 时，可以独立施加正确的位置编码。从而不会有问题。

### vllm 中一些优化：

https://www.aleksagordic.com/blog/vllm 中提到了 vllm 的一些优化：

- Chunked prefill：把长序列的 prefill 切成 chunks，分多次 prefill(从而减小粒度）。否则就把推理流水线给 hang 住了。
  > (v0.4.2) vLLM supports an experimental feature chunked prefill. Chunked prefill allows to chunk large prefills into smaller chunks and batch them together with decode requests.
- prefill-decoding 分离（PD分离）： continuous batching 可以混合 perfill 与 decode，但是二者差异还是有的，所以可以把两种计算在不同的计算节点完成。

