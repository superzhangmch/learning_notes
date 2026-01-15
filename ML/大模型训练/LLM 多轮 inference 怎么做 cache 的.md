各家 LLM 供应商, 怎么实现多轮历史 messages 的 prompt cache 的?

有两种可能的架构： 

**方案 A：GPU 本地 + Sticky Routing** - Cache 存储在 GPU 的 VRAM 中 - 通过负载均衡器的 sticky routing，将同一会话的后续请求路由到同一台 GPU 
  - 这样会不会: 导致 gpu 的计算利用率不足

**方案 B：分布式 Cache Server** - Cache 存储在独立的分布式存储集群（如 Redis/Memcached 或自定义系统） - 任意 GPU 都可以通过网络读取 cache 

一般是哪种?

----

## vLLM 怎么做

chatgpt 回答:

在 **vLLM（一个高吞吐量、面向生产的 LLM 推理/服务引擎）中处理多轮对话历史缓存（prompt cache / KV-cache）时**，目前的实现和设计 **主要是针对单机 GPU 级别的 cache 重用机制**，本身并没有内置一个全局、分布式的 cache 服务去跨节点共享历史 messages。核心机制叫 **Automatic Prefix Caching（自动前缀缓存）**，它缓存 *已经计算好的 KV cache blocks* 并复用到后续请求。([vLLM][1])

**它的主要是方案 A：GPU 本地 + 会话/前缀亲和路由（sticky routing / prefix-aware routing）**

* vLLM 内部把 **KV cache 以块（blocks）形式存储在 GPU 内存里**（paged attention 设计），这些块可以在同一会话或后续请求之间复用。([vLLM][1])
* vLLM 的 *Automatic Prefix Caching* 会：

  * 识别相同或相似的 prompt 前缀（shared prefix）
  * 从之前的计算结果直接读取对应的 KV cache blocks
  * 避免重新 compute 前面的 token（减少首 token 时延 / 重复计算）([知乎专栏][2])
* 这种 cache 是 **“本地在某个 vLLM 引擎 / GPU 显存里”**。要让请求 hit 到这些缓存，一般需要：

  * LB/路由层实现 **前缀 cache 感知调度（prefix-aware routing）**
  * 将同样前缀的请求尽可能路由到有相关缓存的 GPU 上（sticky 或基于 cache metadata 的调度）([阿里云帮助中心][3])

所以如果你的多个推理节点部署了 vLLM，每个节点都有自己的 prefix cache，那么 **在没有外部 cache 服务的情况下**，要重用历史 messages，通常靠的是：

✔️ **负载均衡 / 调度层把带相同前缀的请求路由到同一个 vLLM 节点**
→ 相当于 “GPU 本地 + sticky routing / prefix-aware routing”（方案 A）。

