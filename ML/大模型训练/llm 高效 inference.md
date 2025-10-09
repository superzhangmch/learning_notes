假设一个 LLM server，有源源不断的请求到来。那么怎么高效推理呢？

- batch：请求会组织成 batch 进行，而不是每个请求独立做生成
- continuous batching：即使 batch 化，也不是说这一批执行完后，才开始下一个 batch——batch 内有的生成结果短，有的长，这样会计算资源浪费。而是 batch 内算完的马上退出，从而把新的添加进来。
  - vLLM、Hugging Face 的 Text Generation Inference（TGI），都支持它。

