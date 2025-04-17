LLaMa3：8k的训练窗口，短文本拼成8k。提到训练时用 attn mask 把他们隔离开。见 https://ai.meta.com/blog/meta-llama-3/。说明之前好多LLM并没attn mask作区隔

《Fewer Truncations Improve Language Modeling》：提到LLaMa2，PaLM也是 concatenate-then-split, 为了充分利用训练context，导致完整的序列被truncation。按作者给的图可以看到，传统方法等价于把原始的训练大语料用 <|endoftext|> 拼接成单个序列，然后按train context length粒度切成片。该文觉得应该尽量少的把完整文本切开（通过某种方式密排而少truncation）。

《IN-CONTEXT PRETRAINING: LANGUAGE MODELING BEYOND DOCUMENT BOUNDARIES》：本文讲，构建pretrain数据序列时，应该把内容上相关的原始sequence聚合起来令挨着。从文中图2可以看到，单个原始序列，是有可能在train context length处被中间切开，导致下一样本序列的start部分是该被切开数据的后半段。

pretrain的时候，确实惯常做法是concatenate-then-split。但是在fine tune的时候，看到的各种做法，都不会把数据切开（可以拼，但是不切而是padding）

----

# 下面是直接问 LLM：
> LLM pretrain 的时候，要把不同的数据打包，用特殊符号隔开。假设 ABC三条数据打包后，还剩下一些空间，把D放进来容纳不下，余下把D截取。也就是用了 A-B-C-part_of_D, 那么多余D余下的部分，怎么处理？是本次直接丢弃？还是填充下一个 window的时候，remainder_of_D-E-F?

author: chatgpt 4.5

一般在LLM的pretrain过程中，数据打包（packing）时遇到单条数据无法完整放入window的情况，业界的主流处理方式是：

### **不丢弃，直接顺延到下一个 window：**

- 如果当前window装入数据时，数据D只放进了一部分（part_of_D），则剩下的部分（remainder_of_D）一般会保留并放到下一个window的开头，形成新的窗口：
  
  ```
  当前window： A - B - C - (part_of_D)
  下个window： (remainder_of_D) - E - F ...
  ```

- 这种方法称为 **跨窗口延续（跨window）**，是一种标准且合理的做法，广泛用于实际的大规模预训练中（例如GPT系列的训练）。
 
### 为什么不直接丢弃？

如果将数据截断后的余下部分直接丢弃，会造成：

1. 数据的浪费
   - 大规模预训练模型（GPT-3、GPT-4、LLaMA等）通常依赖于非常大的数据量，随意丢弃数据降低训练数据的使用效率。

2. 文本上下文的中断
   - 一些长上下文语义、篇章逻辑的信息被截断后，可能导致模型在此类任务上表现欠佳。

因此，跨窗口延续数据是普遍推荐的做法。
 

### 具体的实现方式举例（典型pipeline）：

- 假设模型上下文大小（window size）是 `1024 tokens`。
- 数据A, B, C, D, E... 不同长度，需要放入window时，按顺序打包。
- 打包后，如：
  ```
  Window 1: | <sep> A <sep> B <sep> C <sep> part_of_D |
  Window 2: | remainder_of_D <sep> E <sep> F <sep> part_of_G |
  Window 3: | remainder_of_G <sep> H <sep> I |
  ```
- 其中 `<sep>` 表示特殊分隔符token，用于模型学习不同样本间的边界。
 

### fine-tuning时的情况：

- Pretrain阶段强调数据利用效率，一般都采用跨window延续的方式。
- 而Fine-tuning阶段，有时候为了更明确的数据边界、语义完整性，会倾向于 **整句/完整句子为单位截断**，更注重数据的完整性，不太会跨window延续。

  例如fine-tuning时：
  ```
  如果数据D放不下，可能直接放到下一个window，保证每个样本语义完整、清晰。
  ```

- 但实际操作中，由于Fine-tuning数据通常更短、更规范（例如指令任务的prompt+answer），跨window延续的场景本来就很少出现。
 

### 业界常规总结：

| 阶段       | 主流方法                   | 优点                              | 缺点                         |
|------------|----------------------------|-----------------------------------|------------------------------|
| pretrain   | 跨窗口延续（继续下一window） | 提升数据利用率，减少浪费           | 部分语义被截断在两个窗口之间 |
| fine-tune  | 尽量完整、独立窗口          | 保证语义清晰，避免跨样本污染       | 数据利用效率可能稍低         |

综合来看：

- **预训练** 一般是 **跨窗口延续**；
- **Fine-tuning** 一般是 **避免跨窗口延续，尽量语义完整**。

这是业界比较广泛认可且实践的方法。

========

### author: gemini 2.5 pro

在LLM预训练的数据准备阶段，处理这种数据打包和截断的情况，通常有两种主要方法，但其中一种更为常见和高效：

1.  **携带剩余部分到下一个窗口 (Carry-over Remainder - 最常见方法)**：
    * **描述**：这是目前主流LLM预训练（如GPT系列、LLaMA等）中最常用的方法。当一个数据样本 `D` 在当前窗口 `A<sep>B<sep>C` 之后无法完全放入时，只将 `D` 的一部分（`part_of_D`）放入当前窗口，使其填满。然后，`D` 剩下的部分（`remainder_of_D`）会被保留下来，并作为**下一个**数据窗口的**起始内容**。
    * **下一个窗口的构造**：下一个窗口会以 `remainder_of_D` 开头，然后继续添加后续的完整数据样本 `E`, `F` 等，直到这个窗口也被填满。例如：`remainder_of_D<sep>E<sep>F<sep>part_of_G`。
    * **优点**：
        * **数据效率高**：不会丢失任何训练数据，所有文本都被模型看到。
        * **计算效率高**：最大化利用了每个训练批次中的token，减少了padding或浪费。
    * **分隔符处理**：通常，分隔符（如 `<|endoftext|>` 或 `</s>`）是加在每个完整样本 *之后* 的。所以在 `A<sep>B<sep>C<sep>part_of_D` 这个窗口里，`part_of_D` 后面通常 *不会* 再加分隔符，因为它不是一个完整的样本。下一个窗口 `remainder_of_D<sep>E<sep>F...` 中，`remainder_of_D` 后面也 *不会* 加分隔符，直到遇到下一个完整样本 `E` 的末尾，才会加上分隔符。有些实现也可能在样本 *之前* 加分隔符。关键是保持逻辑一致性，让模型能理解样本的边界。

2.  **丢弃剩余部分 (Discard Remainder - 较少使用)**：
    * **描述**：将 `part_of_D` 放入当前窗口后，直接丢弃 `D` 的剩余部分 `remainder_of_D`。下一个窗口直接从下一个完整的数据样本 `E` 开始构建 (`E<sep>F<sep>G...`)。
    * **优点**：实现相对简单。
    * **缺点**：
        * **数据丢失**：丢弃了部分数据，降低了数据的利用率，尤其是在处理长文档时，可能会丢失大量信息。
        * **效率较低**：相当于浪费了一部分本来可以用于训练的文本。
    * **使用场景**：这种方法不太常见于需要最大化数据利用率的大规模预训练，但可能在一些特定的、简化处理流程的研究或应用中被采用。

**总结：**

在标准的LLM预训练流程中，为了最大化数据利用效率，普遍采用**第一种方法**：将当前窗口放不下的数据样本的剩余部分（`remainder_of_D`）**携带到下一个训练窗口的开头**继续使用。这样可以确保所有的训练数据都被模型学习到，避免浪费。


----

# 下面是 chatgpt deepresearch 的报告（2025.04.17）：

（总结下，即 concatenate-then-split。 这样可能导致：被截断的长文本，后半部分被训练的时候，有可能一句话都被切成两半了，于是model看到的就是一片文章是以一个残破的句子开头的。）

author: chatgpt deepresearch

明白了，我会调研当前主流大模型（如 GPT、LLaMA、Mistral 等）在训练阶段（包括 pretraining 和 finetuning）处理输入序列长度不一致时的策略。
重点关注：
- 对于填充训练窗口时一条数据超过 context window 时是否截断，截断后是否丢弃或重新放入下一窗口
- 数据 packing 策略，包括如何最大化利用 context-size

我会尽快给你汇总详细结果和方法，包括业界公开论文或实际工程实现中的说明。

# 预训练阶段

**短文本的 Packing：** 在大模型预训练时，**会将多个短的文本样本拼接(pack)成一个长序列**，以充分利用固定的上下文长度。例如 OpenAI 的 GPT-3 模型在训练时**始终使用完整的 2048 个 token 的上下文窗口**，如果单个文档不足 2048 token，就会紧接着拼接下一个文档，并在文档之间插入一个特殊的“文本结束”标记（如 `<|endoftext|>`），以划分不同样本 ([[2005.14165] Language Models are Few-Shot Learners](https://ar5iv.org/abs/2005.14165#:~:text=During%20training%20we%20always%20train,specific%20masking))。这样做可以避免对每个短样本单独填充大量空白。**RoBERTa、GPT-3、T5 等主流模型的论文都提到采用类似的“packing”技巧**（例如“将完整句子连续采样拼接，直至总长度达到上限”） ([Packing Data for efficient Training and Inference](https://lweitkamp.github.io/posts/packing/index.html#:~:text=RoBERTa2%20%E2%80%9CEach%20input%20is%20packed,%E2%80%9D))。通过packing，训练序列中的空白填充(padding)大幅减少——有研究指出，如果不做packing，NLP语料长度差异会导致多达 **50%** 的训练tokens只是用于填充 ([[2107.02027] Efficient Sequence Packing without Cross-contamination: Accelerating Large Language Models without Impacting Performance](https://ar5iv.org/abs/2107.02027#:~:text=batches%20and%20long%20sequences%20for,lost%2C%20or%20by%20customized%20kernel))。采用packing后，模型上下文几乎全被实际数据占据，提高了计算效率 ([llm-foundry/llmfoundry/data/packing.py at main · mosaicml/llm-foundry · GitHub](https://github.com/mosaicml/llm-foundry/blob/main/llmfoundry/data/packing.py#:~:text=,minimizes%20padding%20with%20zero%20waste))。

**长文本的截断与续接：** 当单条训练样本（如一篇长文档）的长度**超过**模型的最大上下文长度时，业界通常会**在达到上限处截断**然后继续训练剩余部分，而不是完全跳过超长内容。也就是说，**将长文本切分成若干个连续的窗口片段**。例如，对于GPT-3，训练时就是按顺序将语料流切分成一个个2048-token的片段 ([[2107.02027] Efficient Sequence Packing without Cross-contamination: Accelerating Large Language Models without Impacting Performance](https://ar5iv.org/abs/2107.02027#:~:text=match%20at%20L959%20GPT,problem%20trivial%20and%20avoiding%20any))。如果一个文档在某个片段末尾未完结，并未特别添加终止标记（表示并非真正文档结束），模型在下一个训练序列会接着该文档的剩余部分继续训练。这样**长文档的剩余部分并不会被丢弃**，而是作为后续序列的一部分被模型学习，只是模型无法跨越超过上下文窗口的距离看到更早部分。GPT-3 的实现方式是**在每个2048长度序列装满时直接切断超出部分**，使每个序列正好达到上下文长度上限，无需填充 ([[2107.02027] Efficient Sequence Packing without Cross-contamination: Accelerating Large Language Models without Impacting Performance](https://ar5iv.org/abs/2107.02027#:~:text=match%20at%20L959%20GPT,problem%20trivial%20and%20avoiding%20any))。被切断的内容将在下一个训练序列继续出现（如果前一序列因为上下文限制中断了一篇文档，下序列开头继续该文档的剩余内容）。通过这种 **“截断续接”**，几乎所有训练文本都会被模型看到；只有极少数情况（例如整个语料最后不足一窗的部分）可能被舍弃或填充。需要注意的是，不同文档之间仍以终止符区分以防混淆，模型可以据此判断序列中不同段落实际上无关联 ([[2005.14165] Language Models are Few-Shot Learners](https://ar5iv.org/abs/2005.14165#:~:text=During%20training%20we%20always%20train,specific%20masking))。主流模型（如GPT系列、LLaMA、BLOOM、Falcon等）在预训练数据处理中普遍采用上述策略：**短样本尽量拼接填满上下文，长样本超出部分切分到下一窗口**。

**效率与效果权衡：** 这种 **packing+截断** 策略大幅提高了GPU利用率，避免了绝大部分填充浪费 ([[2107.02027] Efficient Sequence Packing without Cross-contamination: Accelerating Large Language Models without Impacting Performance](https://ar5iv.org/abs/2107.02027#:~:text=batches%20and%20long%20sequences%20for,lost%2C%20or%20by%20customized%20kernel)) ([llm-foundry/llmfoundry/data/packing.py at main · mosaicml/llm-foundry · GitHub](https://github.com/mosaicml/llm-foundry/blob/main/llmfoundry/data/packing.py#:~:text=,minimizes%20padding%20with%20zero%20waste))。GPT-3团队提到他们**不对同一序列中不同来源的文本做特殊的遮蔽处理**（即不阻止跨文档的自注意力），而是仅靠终止符让模型自行识别上下文已重置 ([[2005.14165] Language Models are Few-Shot Learners](https://ar5iv.org/abs/2005.14165#:~:text=During%20training%20we%20always%20train,specific%20masking))。尽管理论上拼接不相干文本段可能引入轻微的“跨样本污染”，影响模型判断句子边界，Facebook 的研究曾发现**混合同一序列中的不同文章可能略微降低准确率**，但在大规模训练下这种影响很小，可以接受 ([Packing Data for efficient Training and Inference](https://lweitkamp.github.io/posts/packing/index.html#:~:text=Some%20approaches%20use%20the%20packing,of%20an%20impact%20at%20scale6))。因此业界默认的做法是**简单拼接并依赖特殊标记分隔**，不额外插入人工mask，从而保持训练过程的简洁和高效 ([[2005.14165] Language Models are Few-Shot Learners](https://ar5iv.org/abs/2005.14165#:~:text=During%20training%20we%20always%20train,specific%20masking))。此外，一些工程上会采用启发式策略进一步 **减少浪费**：（1）**动态规划/装箱算法**：如 Graphcore 提出的按序列长短进行优化的“高效序列装箱”可以避免不同样本混插时的注意力干扰，通过在自注意力中引入遮罩完全杜绝跨样本信息泄漏，并在BERT预训练中将速度提升2倍 ([[2107.02027] Efficient Sequence Packing without Cross-contamination: Accelerating Large Language Models without Impacting Performance](https://ar5iv.org/abs/2107.02027#:~:text=padding,between%20examples%20in%20a%20pack))（虽然这种严格隔离在常规GPT式训练中并不常用）。又如 MosaicML 的数据_collator_实现了自动调整 *packing_ratio* 的算法，在遍历一小部分数据进行profiling后选取既不浪费又不需要额外填充的最优拼接比例，使得**每批次的序列长度利用率接近100%** ([llm-foundry/llmfoundry/data/packing.py at main · mosaicml/llm-foundry · GitHub](https://github.com/mosaicml/llm-foundry/blob/main/llmfoundry/data/packing.py#:~:text=,minimizes%20padding%20with%20zero%20waste))。（2）**分阶段长度策略**：部分模型预训练采用 **“短到长”** 的课程式学习。例如BERT先用较短序列训练90%的步骤，再用长序列训练剩余10%，以降低前期计算成本和填充浪费。这些措施都属于工程上的优化，但**对于 GPT、LLaMA 这类自回归大模型，大多数开源实现还是采用固定最大长度直接拼接的方法**，以确保模型始终在最大上下文下学习。

# 微调阶段

**单样本序列及不跨样本拼接：** 在指令微调或对话微调阶段，每条训练数据通常是一段**独立的完整对话或问答**，模型需要根据该输入产生对应输出。与无监督预训练不同，此时**不会把多个互不相关的指令样本拼接在同一序列**中训练，因为不同对话/指令之间没有连贯性，而且微调往往需要针对每个样本单独计算loss（例如只让模型生成回答部分的内容）。为了简化处理，业界一般一条样本用一个序列，**不进行跨样本的packing**。这样做避免了需在同一序列内标记多个答案区域、处理不同样本交错带来的复杂性。**短的微调样本**（比如只有一两句话的指令）也直接作为一个序列训练；在构造批次时，会对该批次内最长样本对齐进行**动态填充**。例如 Hugging Face 提供的`DataCollatorWithPadding`默认将每个batch中序列padding到当批次最长序列的长度 ([Using data collators for training and error analysis](https://lewtun.github.io/blog/til/nlp/huggingface/transformers/2021/01/01/til-data-collator.html#:~:text=Using%20data%20collators%20for%20training,on%20the%20padded%20tokens))。这意味着如果微调样本普遍短于模型最大长度，则实际填充长度只是当批最长值，而不是总是填充到模型上下文上限，从而减少了不必要的计算开销 ([Using data collators for training and error analysis](https://lewtun.github.io/blog/til/nlp/huggingface/transformers/2021/01/01/til-data-collator.html#:~:text=Using%20data%20collators%20for%20training,on%20the%20padded%20tokens))。通过**按批动态padding**和按长度分桶排序等手段，微调阶段的padding浪费也能被控制在较低水平。

**超长样本的截断处理：** 如果某条微调数据本身长度**超过模型的上下文窗口**（例如包含非常长的多轮对话或篇幅过长的文章），通常会**直接截断到模型最大长度**，超出的部分不参与训练。业界工具一般默认如此：例如 MosaicML 的微调工具中提供了参数`context_length`用于设置最大序列长度，任何超过该长度的样本都会被**截断** ([Finetuning - Mosaic AI Training](https://docs.mosaicml.com/projects/mcli/en/latest/finetuning/finetuning.html#:~:text=multiplier%20of%200)) ([Finetuning - Mosaic AI Training](https://docs.mosaicml.com/projects/mcli/en/latest/finetuning/finetuning.html#:~:text=truncate%20any%20data%20that%20is,length%20beyond%20each%20model%E2%80%99s%20default))。**截断后的剩余内容通常被舍弃**，并不会像预训练那样自动衔接到下一个序列继续训练，因为在微调任务中每条数据都是独立语义，不易将一条超长对话拆成两部分分别训练（那样第二部分将缺少开头的上下文，语义不完整）。因此，为保证训练数据质量，开发者要么在预处理阶段就过滤掉过长的对话/指令，要么在加载时截断到上限。截断时一般会保留开头部分（例如用户提问和尽可能多的助手回答），**超出上下文窗口的尾部内容直接丢弃**。模型只对截断后的内容计算损失，这样虽然有部分标注数据未用到，但可以确保每次喂给模型的序列不超过可处理长度。以 OpenAI 为例，其指令微调和对话RLHF数据基本都限制在模型上下文长度（如GPT-3.5系列是2048 token）内，训练时如果对话超过这个长度也会被截断到上限；Facebook 在LLaMA-Chat等微调时同样遵循模型的固定最大长度，不额外扩展序列。总的来说，**微调阶段严格遵循模型的上下文窗口限制**：宁可舍弃过长部分，也不让单个训练序列超长。

**减少微调阶段浪费的其他措施：** 虽然微调不采用跨样本packing，但仍有一些工程技巧来提高效率、减少无效计算。例如上面提到的**动态padding**能确保批内padding最小化 ([Using data collators for training and error analysis](https://lewtun.github.io/blog/til/nlp/huggingface/transformers/2021/01/01/til-data-collator.html#:~:text=Using%20data%20collators%20for%20training,on%20the%20padded%20tokens))。此外，项目通常会**按长度划分批次或排序**微调数据，使得同一批次里的序列长度相近，避免极短序列和长序列混杂造成大量填充。对于极少数超长样本，开发者可能选择**丢弃这些异常样本**而不是频繁截断，毕竟在高质量指令数据中，超过模型上下文长度的情况非常少见而且模型也无法完整训练这部分内容。还有一些启发式处理，例如在多轮对话微调中，如果对话记录过长，可以只取最近若干轮对话作为模型输入，从而既保持问题语境又不超长。不过，总体来看**主流开源模型在微调时都是直接遵循模型原有的最大长度限制来截断输入** ([Finetuning - Mosaic AI Training](https://docs.mosaicml.com/projects/mcli/en/latest/finetuning/finetuning.html#:~:text=truncate%20any%20data%20that%20is,length%20beyond%20each%20model%E2%80%99s%20default))；通过合理整理数据顺序和动态填充，训练过程中因长度不一致导致的计算浪费也被降到最低。各大模型（如GPT-3.5系列、LLaMA-2-Chat、Mistral-Instruct等）在公开的微调实现中，无一不是采用上述策略：**每条指令单独处理，超长截断丢弃，靠数据整理来减少padding开销**。这种简单而稳健的做法保证了微调阶段训练的高效和数据的有效利用。 

**参考文献：**

- 【15】Brown et al. *“Language Models are Few-Shot Learners”*, 2020 ([[2005.14165] Language Models are Few-Shot Learners](https://ar5iv.org/abs/2005.14165#:~:text=During%20training%20we%20always%20train,specific%20masking))  
- 【24】Krell et al. *“Efficient Sequence Packing without Cross-contamination”*, 2021 ([[2107.02027] Efficient Sequence Packing without Cross-contamination: Accelerating Large Language Models without Impacting Performance](https://ar5iv.org/abs/2107.02027#:~:text=match%20at%20L959%20GPT,problem%20trivial%20and%20avoiding%20any)) ([[2107.02027] Efficient Sequence Packing without Cross-contamination: Accelerating Large Language Models without Impacting Performance](https://ar5iv.org/abs/2107.02027#:~:text=padding,between%20examples%20in%20a%20pack))  
- 【10】L. Weitkamp, *“Packing Data for Efficient Training and Inference”*, 2023 ([Packing Data for efficient Training and Inference](https://lweitkamp.github.io/posts/packing/index.html#:~:text=RoBERTa2%20%E2%80%9CEach%20input%20is%20packed,%E2%80%9D)) ([Packing Data for efficient Training and Inference](https://lweitkamp.github.io/posts/packing/index.html#:~:text=Some%20approaches%20use%20the%20packing,of%20an%20impact%20at%20scale6))  
- 【23】Krell et al., *同上*, 引言部分 ([[2107.02027] Efficient Sequence Packing without Cross-contamination: Accelerating Large Language Models without Impacting Performance](https://ar5iv.org/abs/2107.02027#:~:text=batches%20and%20long%20sequences%20for,lost%2C%20or%20by%20customized%20kernel))  
- 【31】MosaicML LLM Foundry 源码, *`packing.py`*, 2024 ([llm-foundry/llmfoundry/data/packing.py at main · mosaicml/llm-foundry · GitHub](https://github.com/mosaicml/llm-foundry/blob/main/llmfoundry/data/packing.py#:~:text=,minimizes%20padding%20with%20zero%20waste))  
- 【32】MosaicML 平台文档, *Finetuning*, 2023 ([Finetuning - Mosaic AI Training](https://docs.mosaicml.com/projects/mcli/en/latest/finetuning/finetuning.html#:~:text=truncate%20any%20data%20that%20is,length%20beyond%20each%20model%E2%80%99s%20default))  
- 【33】Hugging Face 文档, *Using Data Collators*, 2022
