有两篇 paper 是关于基于 small model 的 speculative decoding 的。都是google 家的（其中一篇是 deepmind的）。 

- 2022.11 《Fast Inference from Transformers via Speculative Decoding》  https://arxiv.org/pdf/2211.17192
- 2023.02 《Accelerating Large Language Model Decoding with Speculative Sampling》 https://arxiv.org/pdf/2302.01318
  > Coincidentally, the work in this manuscript was undertaken **concurrently and independently** of the work on speculative decoding from Leviathan et al. (2022).
  >
  > We focus more heavily the distributed serving setting for large models and offer some incremental optimisations, but otherwise the core underlying idea is the same. (背后做法一样。但本篇更侧重分布式 serving 与一些优化）

----

