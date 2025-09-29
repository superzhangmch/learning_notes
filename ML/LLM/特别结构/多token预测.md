### deepseek-v3 的做法

如下，它的多 token 预测，是因果串联式的，而之前别人的做法，是直接接多个独立的 output heads。

别人：如下图独立处理：

<img width="950" height="674" alt="image" src="https://github.com/user-attachments/assets/9c5fc375-bcac-434d-b88a-24e748ee9182" />

deepseek-v3：如下图因果串联式：

<img width="1762" height="876" alt="image" src="https://github.com/user-attachments/assets/016ba7af-4834-4965-92af-ec0f668ff989" />

如上图：
- 最左是当前pos=i 位置的 token预测，也就是一般 LLM 所做的。后面的是额外的多 token 预测。
- 额外的多 token 预测：是 **串联式** 进行的。每个 pos=i+k 的 MTP input 包括 pos=i+k-1 的 MTP 的 output state，以及 pos=i+k 的 input token emb：对这两个 input concat 之后，经过一个 transformer block 的处理后，预测下一个 token。
- MTP 之间共享的是 emb 与 output_llm_head，其他不共享。
- 图中各部分的 loss 之和，为最终 loss

对于 单个 MTP，特别看下：

<img width="842" height="860" alt="image" src="https://github.com/user-attachments/assets/0df634a5-55fd-409c-a74c-d328b441570b" />

