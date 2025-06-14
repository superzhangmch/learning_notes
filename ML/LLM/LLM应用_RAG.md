# Perplexity.ai 怎么工作的？主流 RAG 怎么做的？

下面 by chatgpt deepresearch。

---

明白了。我将研究 Perplexity.ai 和 ChatGPT 搜索插件底层是如何进行大规模信息检索的，包括它们使用的是倒排索引、向量数据库，还是混合方式。同时，我也会分析目前主流实用型的 RAG（检索增强生成）系统是如何实现检索的，比如它们使用 Lucene、向量数据库（如 FAISS、Pinecone、Weaviate）还是其他方案。

我会整理清晰的结构化信息，并用表格对比不同方法。完成后会第一时间告诉你。


# Perplexity.ai 和 ChatGPT 搜索插件的大规模检索技术研究

## Perplexity.ai 的底层检索技术

**索引构建：** Perplexity.ai 自称为“解答引擎”（Answer Engine）而非传统搜索引擎。早期（2022 年）其答案来自 Bing 搜索，但随着发展，团队开始建立自有的网页抓取和索引系统。Perplexity 开发了自有爬虫（PerplexityBot）来抓取网页，并构建定制的索引库和排名算法。这意味着 Perplexity.ai **确实建立了自己的索引库**，而且索引规模比 Google 更小、更精炼，侧重高质量、高可信度的网站内容。他们聚焦于主流查询涉及的权威内容，以紧凑索引提供快速准确响应。

**检索方式：** Perplexity.ai **主要采用传统倒排索引技术**进行关键词匹配检索，并使用改进的 TF-IDF 算法 BM25 来评分文档相关度。Perplexity 非常强调 BM25 等经典稀疏检索算法的价值。其 CEO 提到，在许多检索基准上，BM25 的表现仍**优于**某些语义向量模型，完全依赖嵌入向量无法解决搜索问题。因此 Perplexity **没有将全部网页内容转成单一“大型向量数据库”来检索**；相反，它采用**关键词匹配为主、语义为辅的混合策略**。例如利用 **BM25 算法**处理用户查询的词项匹配，同时结合 **n-gram** 分词匹配，处理拼写错误、短语匹配等情况。Perplexity 团队认为仅靠向量表示难以完美涵盖网页知识的各层语义，而且向量维度特征难以解缠，使得纯向量方案难以判断检索相关性。因此，他们业界实践是**传统检索算法与现代语义技术并用**，而非依赖单一嵌入模型。

**底层框架：** 虽然 Perplexity 官方未明确公开其索引架构细节，但从访谈信息推测，其索引和检索**可能基于经典搜索引擎框架（如 Lucene/Elasticsearch）**进行改造优化。Perplexity 强调了 **BM25** 算法和 **PageRank** 等网页权威度信号的重要性。这暗示他们利用了类似 Lucene 的倒排索引来实现 BM25评分，并参考网页链接分析（PageRank式）提升高信誉站点的排名。此外，PerplexityBot 爬虫遵循 robots.txt 抓取网页，说明其索引流程与传统搜索引擎类似。可以认为，Perplexity.ai 建立了**自研的爬虫 + 索引 + 排序管线**，融合了传统信息检索领域多年的工程实践（例如爬虫基础设施和倒排索引技术）。

**检索结果融合 LLM：** 在检索完候选文档后，Perplexity.ai 会**提取网页中的相关段落**提供给其语言模型，用于答案生成。为了找到文档中最相关的片段，Perplexity 使用 **LLM 和嵌入技术**对抓取的网页文本进行细粒度相关性分析。也就是说，Perplexity 不仅索引网页全文，还**解析网页内容**，将其中与查询最相关的句段挑选出来输入给 LLM。这一过程相当于对初步检索结果进行**语义精筛**。最终，LLM 基于选出的片段生成回答，并**严格限制答案来源于检索到的内容**。Perplexity 明确规定其回答**不添加检索源之外的任何信息**，不足则宁可答“没有足够信息”。这种策略比一般 RAG 更严格地保持事实依托，最大程度减少幻觉。回答中每句话附上来源引用，实现结果的可查证和可信赖。

**策略与特点：** 总体而言，Perplexity.ai 的检索部分体现了**混合检索**理念：以经典稀疏检索（倒排索引 + BM25）打基础，同时结合必要的语义技术增强。Perplexity 团队认为对**非结构化全网数据**，必须结合关键词匹配才能覆盖精确信息，例如人名、数字等精确匹配需求。他们在排名阶段融合了传统信息检索信号（如 n-gram 匹配、站点权威度）和现代方法（如 LLM 判断段落相关性）。**索引库**方面，Perplexity 并未索引整个长尾网页，而是精选高质量内容构建较小但精炼的索引，以提升质量和准确性。这是一种**以质取胜**的索引策略，针对大多数用户常问的主题确保有权威答案，对于特别冷门的长尾查询暂未全面覆盖。总体来看，Perplexity.ai 的底层技术路径是**自建爬虫+倒排索引（BM25）+混合检索+LLM 生成**，属于RAG系统在全网搜索场景的一种实现。

## ChatGPT 搜索插件的底层检索技术

**Bing 搜索集成：** ChatGPT 的“浏览/搜索”插件并未自行建立网页索引，而是直接**集成微软 Bing 的搜索引擎**来实现网络信息检索。用户在 ChatGPT 中启用联网搜索（点击地球图标）后，ChatGPT会将用户查询提交给 **Bing Search API**。因此，ChatGPT 实时搜索能力完全建立在 Bing 已有的**大规模网页索引**之上。这意味着**若某网页未被 Bing 收录编入索引，ChatGPT 搜索将无法检索到该网页**。OpenAI 方面也推出了新的爬虫 OAI-SearchBot 配合 Bing 索引，以确保更多网页内容可供 ChatGPT 检索，但本质上 ChatGPT 搜索依赖的是 **Bing 的全球网页数据库和索引体系**。

**检索方式：** 由于底层使用 Bing，引擎层面采用的是 **传统搜索引擎的倒排索引技术**，结合现代搜索引擎的多种增强。在检索第一步，Bing 会利用其倒排索引执行 **关键词匹配和 BM25 算法**的基础排序，找出包含查询相关关键词的网页。接下来，Bing 还应用**机器学习语义模型对结果进行重排序**。据微软透露，Bing 使用一种**语义Ranker**模型（如 BERT 类模型）对初步结果与原始查询逐一对比打分（相关性0-4分），再据此调整排序。这相当于 Bing 内部执行了\*\*“BM25 + 语义重排”**的检索流程。此外，Bing 可能还结合**向量相似度**等新技术来增强召回；微软的 Azure Cognitive Search 已提供将**向量搜索与BM25结合的混合检索\*\*能力（Bing 很可能在自家搜索中也部分采用类似策略）。总的来说，ChatGPT 搜索继承了 **Bing 搜索的混合检索**特点：既利用倒排索引保证高召回和精确匹配，又借助深度学习模型理解查询意图、语义匹配，从而提高排名质量。

**基础架构：** ChatGPT 搜索插件本身不维护索引数据库，也不直接使用向量数据库存储网页文本\*\*。它通过**API调用**即时获取 Bing 搜索结果。这意味着**底层框架**完全是微软 Bing 的基础架构，包括其全球爬虫、索引、排名管线等。对 OpenAI/ChatGPT 而言，Bing 搜索相当于一个封装好的检索工具（Plugin），ChatGPT 只需提供查询并将 Bing返回的网页内容用于后续的回答生成。这种模式下，OpenAI **继承了微软多年来在大规模搜索引擎上的积累**，包括对网页可靠性的评估、垃圾信息过滤，以及**安全模式**筛除不良内容。OpenAI 表示，通过 Bing API，他们沿用了微软在信息可靠性和安全过滤方面的大量工作成果。

**结果处理与引用：** ChatGPT 获取 Bing 搜索结果后，会**爬取前若干网页的内容**并交由GPT-4模型总结答案。回答生成时，ChatGPT 会引用信息来源链接，确保用户可以点击核实。在 ChatGPT 界面中，模型回答的同时在侧栏列出相关链接，提供更多上下文。与 Perplexity 类似，ChatGPT 搜索插件也注重**给出来源引用**，提升回答的可追溯性和可信度。不过，其引用链直接来自 Bing 提供的结果链接，并不一定逐段标注。ChatGPT 还允许用户就检索结果继续对话追问，使搜索过程更具对话交互性。

**小结：** ChatGPT 搜索插件实际上是 **LLM + Bing 搜索引擎**的结合。它**不使用独立的倒排索引或向量数据库**，而完全依赖商用搜索引擎（Bing）的基础设施。因此在“是否建立索引库”、“索引类型”等问题上，ChatGPT 搜索插件本身答案是：**不自行建立索引**，而使用 **Bing 的倒排索引**（并辅以 Bing 内部的向量语义模型）。这一模式证明了现有搜索引擎可以与大型语言模型互补结合：搜索引擎负责大规模信息检索，LLM 负责语言理解和回答生成。ChatGPT 则专注于如何将检索结果整合为连贯回答。因此，ChatGPT 搜索插件体现的是一种\*\*“检索即服务”\*\*的思想，通过 API 使用传统搜索引擎完成检索任务。

## 主流 RAG 系统检索部分的实现

在 Retrieval-Augmented Generation (RAG，检索增强生成) 系统中，检索模块是关键组件。当前主流且实用的 RAG 系统在检索部分主要体现出以下趋势：

### 检索方式：倒排索引 vs 向量检索 vs 混合检索

* **稀疏倒排索引检索：** 传统关键词匹配（如 TF-IDF/BM25）仍然在 RAG 中扮演重要角色。倒排索引能够精确匹配查询中的关键术语、专有名词、数字等，对于**精确字符串匹配**的场景非常有效。此外，倒排方法不需要训练数据，对领域和语言没有偏置，适用于任何文本集合。实践中发现，在**域外查询**（out-of-domain）或高度技术化的内容上，预训练的通用向量模型未必理解专业词汇，这时简单的关键词匹配反而表现更好。因此许多系统仍内置BM25检索，确保对**精确匹配**需求的良好支持。

* **密集向量检索：** 随着深度学习发展，**向量语义检索**（dense retrieval）成为 RAG 主流方案之一。将文档和查询编码为**嵌入向量**，通过向量空间的距离（如余弦相似度）来衡量相关性，可捕捉语义上的匹配。向量检索的优势在于**语义理解**：用户可以用自然语言提问，不需要刻意使用文档中的精确词汇，也能找到语义相关内容。例如，对于同义表达、上下文相关的问题，embedding 检索往往比纯关键词匹配更有效。然而其劣势在于对罕见实体、数字等精确信息可能召回不足，而且如果向量模型训练语料与实际应用领域差异大，效果会明显下降。尽管如此，在海量非结构化文档场景下，**向量数据库**（如 FAISS、Pinecone 等）已成为构建 RAG 系统的常用基础设施，用于高效存储和查询嵌入向量。许多应用通过向量检索获取 top-k 相似文档，再交由 LLM 阅读，这种\*\*“语义匹配+生成”\*\*流程极大拓展了可用信息范围。

* **混合检索：** 为了兼顾上述两种方法的优点，当前**最优实践是混合检索（Hybrid Search）**。混合检索指同时执行稀疏关键词检索和密集向量检索，然后融合两者结果。这样既能找到语义相关但词不同的内容，又不漏掉包含查询关键词的精确文本。微软的研究表明：**仅向量检索不足以完成高质量RAG**，应结合全文检索以捕获精确匹配信息。Azure Cognitive Search 已默认实现**向量+BM25+融合+重排**的完整流程，其实验证明“BM25+向量+语义Ranker”的组合获得了最佳效果。Haystack 等开源框架同样推荐采用两个检索器（Sparse+Dense）并将结果合并，然后用Ranker排序。融合方式常用**倒数等级融合（RRF）**等算法，将同时出现在两边的结果提升排名。混合检索能显著提高检索的**召回率和精准率**：在需要精确匹配的场景下，关键词检索贡献结果；在语义扩展场景下，向量检索提供补充。因此，大型RAG系统越来越多地**默认采用混合检索**策略，以最大程度覆盖用户查询意图。

### 检索增强策略：重排序、Query 重写、多跳检索

为了进一步提升检索模块提供给 LLM 上下文的质量，主流 RAG 系统通常在基本检索之上增加一些**增强策略**：

* **结果重排序（Re-ranking）：** 通过初步检索得到一批候选文档后，往往引入**二次排序模型**对这些结果按相关性重新打分排序。常见做法是利用预训练的 **Cross-Encoder** 模型（例如微软的 MS MARCO-MiniLM, 或 CoCa 类模型）对“查询-文档”对做深入语义匹配评分。与单纯的向量相似度不同，Cross-Encoder 能结合查询和文档上下文进行精细判断，因此能更准确地区分哪几篇文档最相关。这一过程类似于 Bing 等搜索引擎中用BERT模型对Top结果**语义重排**。学界和工业实践表明，两阶段检索（检索+重排）可明显提升最终Top-1精确率。例如，Azure的实验发现，在混合检索结果上再用语义Ranker重排，能够将答案正确引用率提升到 \~92%。在 RAG 系统中，引入重排序能确保LLM看到的几段文本是真正相关、高质量的，从而提高回答准确性。不过重排序也增加了计算成本（需对每个候选文本过一次模型），所以通常Top-50结果中选Top-5重排即可权衡性能。

* **查询改写与扩展：** 为了弥补用户原始问题表达可能的不足，RAG 系统常加入**Query 重写（Query Rewriting）**或**扩展**策略。借助 LLM 将用户查询**改写为更有利于检索的形式**，例如提取出核心关键词、替换同义词，或者**生成若干个语义等价的查询变体**。这种思路有时被称为 *RAG-Fusion*：对同一问题产生多个措辞不同的查询，将各自检索到的结果合并并去重，从而扩大全面召回。例如问题“为什么海水是蓝的？”，系统可以生成“海洋的蓝色原因是什么？”等改写来检索更多相关资料。检索到多批结果后，再通过RRF等融合排名，选出最相关的文档。另一方面，在多轮对话场景，Query 改写也用于**将对话上下文融入当前查询**，形成自包含查询发给检索器（LangChain 提供了类似 ConversationalRetrievalChain，会用LLM将对话中的用户问题改写为独立查询）。总体而言，**查询改写**可以提高检索召回的全面性，减少因措辞差异导致的遗漏。一些 RAG 管道也利用查询扩展技术，在查询中增加额外限定词或同义词，以获得更精确结果。

* **多跳检索（Multi-hop Retrieval）：** 对于需要综合多条信息才能回答的问题，RAG 系统可能采用**多跳检索策略**。多跳检索指模型**迭代地进行多次检索**，每次利用前一步获取的信息来引导下一步检索。例如，问：“肠道微生物如何影响帕金森治疗？”这个复杂问题涉及两个子问题：先检索“肠道微生物与帕金森的关系”，再检索“帕金森的治疗方式”，最后整合两方面信息。实现多跳的方法有：基于**流程控制的管线**（如 Haystack 提供的 *iterative retrieval pipeline*，先后运行两个Retriever，用第一次结果中的实体构造第二次查询）；或者使用**Agent智能体**，由 LLM 自主决定需要检索的子问题并调用检索工具多次。OpenAI 的 WebGPT、Google的 Multi-hop QA 等研究均探索了链式检索+推理的方法。在实际系统中，多跳检索可以通过**链式Prompt**或**工具调度**实现。当一个查询答案不在单一文档时，模型通过阅读第一批文档产生新疑问，再检索，从而**逐步搜集线索**。尽管多跳增加了复杂度，但对复杂问答显著提升正确率，是 RAG 系统迈向更复杂推理任务的重要方向。

### 常用开源工具和框架

构建 RAG 检索模块的开发者生态也相当丰富，主要有以下常用工具：

* **Haystack：** deepset 开源的 Haystack 框架专注于问答和搜索应用，提供了**模块化的检索-阅读管线**。在检索方面，Haystack 支持 **Sparse 和 Dense Retriever** 两大类。稀疏检索器如 **BM25Retriever** 可以对接 Elasticsearch、OpenSearch 等后端，实现传统倒排检索；密集检索器如 **EmbeddingRetriever** 则可使用 SentenceTransformers、OpenAI 等模型，将文档向量化并使用 FAISS、Milvus 等向量库搜索。Haystack 甚至提供了 **EnsembleRetriever（混合检索）**，可以同时配置 BM25 和向量两种 Retriever，在管线中并行检索并合并结果。框架内建 **JoinDocuments** 节点支持多结果列表的融合（包括简单拼接、RRF 等方式）。此外，Haystack 还实现了 **TransformersReader/Ranker** 用于重排序和抽取答案，以及 **Agent** 机制可以与搜索引擎等工具交互，实现多跳或工具增强的 RAG。总的来说，Haystack 提供从文档导入、索引、检索、到最终QA的全套组件，**开箱即用支持混合检索和重排序**，非常适合构建生产级问答系统。

* **LangChain：** LangChain 是另一流行的 LLM 编排库，它提供**统一的 Retriever 接口**并能集成各种后端。LangChain 本身不提供搜索引擎，但封装了对 Pinecone、Weaviate、FAISS、Elasticsearch 等后端的连接，使开发者可以方便地使用这些向量数据库或全文检索引擎作为检索器。LangChain 的 RetrievalQA链允许指定任意 Retriever，然后将检索文档交给 LLM 生成答案。对于**混合检索**，LangChain 目前没有完全统一的调用方式，但如果底层存储支持（如 Elastic、Azure Search），开发者可以通过传入特定参数启用同时向量+关键词搜索。LangChain 还提供一些**实用工具**提升检索效果，例如 **ConversationalRetrievalChain** 会使用一个 LLM将对话查询改写融合上下文后再检索，**MultiVectorRetriever**可以对接多个embedding模型检索以增加多样性，还有\*\*MMR (Maximal Marginal Relevance)\*\*选项来减少检索结果冗余等。总之，LangChain 在 RAG 检索部分给予开发者高度灵活性，利用其接口可以快捷组合出定制的检索+生成流程，并辅以缓存、并行等优化提高性能。

* **LlamaIndex（旧称 GPT Index）：** LlamaIndex 专注于**数据索引与查询**，提供了丰富的索引结构来更高效地让 LLM 利用文档。它支持构建**向量索引**（基于向量数据库）、**List索引**（简单拼接全文）、**树索引**（分层聚合文档）以及**关键词Table索引**等多种形式，开发者可根据场景选择。对于检索，LlamaIndex 既支持 **DenseRetriever**（向量语义搜索），也内置了 **BM25Retriever** 以进行关键词匹配。值得注意的是，LlamaIndex 可以将 **BM25 作为稀疏向量嵌入**存入 Milvus 等向量库，通过向量空间计算实现全文搜索——Milvus 2.5 提供了 Sparse-BM25 的内置支持，使开发者无需额外部署Lucene即可在向量引擎中进行关键词检索。此外，LlamaIndex 的灵活之处在于**组合检索器**：例如可以配置一个查询先用BM25Retriever检索，再用EmbeddingRetriever检索，将结果合并后返回；或者先关键词召回大量文档再对这些进行向量过滤等。总之，LlamaIndex 致力于简化**RAG索引构建**，使开发者能以插件化方式尝试不同检索策略（包括混合检索）以提升系统性能。

* **向量数据库与其他：** 除了上述框架，本身提供检索API的**向量数据库**在RAG中扮演底层存储角色。常见的如 **FAISS**（Facebook开发的本地向量近邻检索库，支持百万级向量的高效相似检索），**Pinecone**（商用云向量数据库，即插即用扩展性强），**Weaviate**（开源向量搜索引擎，支持schema和Hybrid问答），**Qdrant**、**Milvus** 等都被广泛采用。许多 RAG 案例是：先用开源工具将文档向量化存入这些向量库，然后通过库的相似度查询获得结果，再交由LLM。对于需要**混合检索**的场景，Elasticsearch/OpenSearch 现在也支持向量字段，可以同时进行语义和关键词查询；Azure Cognitive Search 则提供一站式的Hybrid索引。当构建企业或私有RAG时，经常会将**现有全文检索基础设施（SharePoint搜索、数据库全文索引等）与新引入的向量检索结合**，形成一套混合方案。这种方式利用了既有数据索引，加上向量召回语义扩展，实现比单一方案更好的效果。

综上，当前实用RAG系统的检索实现倾向于：**灵活运用多种检索策略**（稀疏+稠密），并**结合增强技巧**（重排序、改写、多跳）以尽可能获取正确且完整的知识依据。开发者可以借助成熟的框架（LangChain、Haystack、LlamaIndex 等）和后端引擎（Lucene/Elasticsearch、FAISS/Pinecone 等）快速搭建这样的检索模块。在实际应用中，根据数据规模和需求不同，可以选择**纯向量**方案（方便语义查询）、**混合检索**方案（提高综合效果），并辅以**rerank模型**进一步优化。下面的表格总结了 Perplexity、ChatGPT 搜索插件，以及典型 RAG 检索方式在索引和检索技术方面的对比：

| 系统/方法                            | 索引类型及规模                                                                                                                 | 检索技术特点                                                                                                                                                                    | 使用的框架/引擎                                                                                                                                                                                                  | 增强策略与特色                                                                                                                                                                        |
| -------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Perplexity.ai**                | 自建网页索引库（自有爬虫抓取，全网精选子集）。采用经典倒排索引存储网页文本；索引规模较搜索巨头更小但内容质量高。                                                                | 以 **BM25** 为核心的关键词匹配检索。注重词频-逆文档频率相关度计算，支持 n-gram 模糊匹配提升召回。**不依赖纯向量语义搜索**，认为压缩所有知识到单一向量效果不佳。整体为**传统稀疏检索为主，语义方法为辅**的混合策略。                                                   | **自研搜索架构**（可能基于 Lucene/Elastic 打造）。包括自有 **PerplexityBot** 爬虫与定制索引器、Ranker。利用现有搜索引擎原理（倒排索引+PageRank 等）构建，针对问答优化排序算法。                                                                                       | 结合**网页权威度信号**（类似 PageRank，对高质量域名赋予更高权重）；抓取页面时进行**精细化内容解析**，将网页拆成段落并存储，方便检索后LLM引用。使用 LLM 对候选结果段落做相关性判断和**摘要引用**，回答只基于检索内容以确保事实准确。                                               |
| **ChatGPT 搜索插件** <br>*(Bing 集成)* | 不自行构建索引，**直接利用 Bing 的全网索引**。Bing 索引覆盖数十亿网页，使用倒排表存储词->文档映射，并拓展支持向量嵌入等新特性。                                                | **关键词检索 + 神经网络重排**。首先通过 Bing 的倒排索引执行 **BM25** 文本检索，然后应用 Bing 的**语义Ranker**模型对结果重排序。效果上相当于**混合检索**（同时考虑了文本相关性和语义相关性）。也可能利用**稀疏向量**（如 SPLADE）或**Dense 向量**辅助召回，微软云搜索已支持此功能。 | **微软 Bing 搜索引擎**框架。ChatGPT 通过 **Bing Search API** 获取结果。底层由 Bing 的爬虫、索引、排名基础设施支撑。OpenAI 未使用自身数据库，完全调用外部搜索服务。                                                                                               | **实时最新数据**：依托 Bing 实时更新的索引获取最新资讯（如新闻、天气）；**安全过滤**：继承 Bing SafeSearch，对不良内容的检索结果自动过滤；**来源引用**：ChatGPT 将 Bing 返回的网页内容汇总作答，列出来源链接方便验证。                                            |
| **RAG – 向量检索**                   | 自定义**向量数据库**索引。将内部知识库文档通过嵌入模型转换向量，并存入向量索引结构（如 FAISS 平面索引或 HNSW 图）。索引规模可弹性扩展到百万级向量，支持基于向量相似度的快速近邻查询。                     | **Dense 向量相似度搜索**：用户查询经同一嵌入模型编码为向量，在向量空间用距离度量相关性。返回余弦相似度最高的 top-k 文档。此方式擅长语义匹配，自然语言提问可找到语义相关内容，即使措辞不同。缺点是对**精确匹配**如数字、符号略有不足，通常需结合其他策略补足。                                 | 常用 **向量索引/数据库**：开源库如 **FAISS**（本地相似检索）、**Annoy**，向量云服务如 **Pinecone**、**Weaviate**、**Qdrant** 等。开发框架通过接口调用它们实现存储与检索，例如 LangChain 的 VectorStore API 封装了 Pinecone/PGVector 等，LlamaIndex 提供 FAISS、Milvus 集成等。 | **Metadata 过滤**：向量检索常结合元数据条件（如文档类别、时间）筛选结果，提高准确率；**结果重排**：为弥补纯向量可能排序不理想，常对初始结果用 Cross-Encoder **二次排序**，精调排名。若需要支持关键词精确匹配，可在查询前后增设**布尔过滤或多路检索**作为补充。总体注重提高语义召回，同时尽可能保证结果涵盖关键细节。 |
| **RAG – 混合检索**                   | \*\*双索引并行：\*\*同时维护稀疏倒排索引和稠密向量索引两套数据结构。倒排索引用于关键词匹配（通常存储在 ElasticSearch/OpenSearch），向量索引用于语义匹配（存储在向量数据库或Elastic的dense字段）。 | **关键词 + 向量融合检索**：对每个查询同时执行 BM25 检索和向量相似检索，然后将两者结果合并去重。采用如 **Reciprocal Rank Fusion (RRF)** 等算法融合排名，既保证包含查询词的结果不会遗漏，也引入纯语义相关的结果。融合结果再提交下游使用。此方案需要对两路结果评分标准进行归一或加权平衡。       | **支持混合检索的引擎：** *Elasticsearch* 7.17+ 支持稀疏+稠密联合查询，*Azure Cognitive Search* 原生提供 Hybrid 搜索管线（矢量+BM25+RRF）。开源工具如 **Haystack** 封装了同时调用两个retriever并 Join 的管线。另外像 **Weaviate** 也允许在向量查询中附加关键词过滤，实现类似效果。         | **语义重排**：混合检索通常在融合后的候选集上再用强力的语义模型重排序，以充分利用两种检索信号。微软实验证明“混合+重排”可大幅提升答案的正确率和引用覆盖率。此外，系统需要根据应用调整两种检索的相对权重，例如数值精确答案场景可提高BM25权重。从效果看，混合检索显著提升了**检索的鲁棒性**，在各种查询下都能兼顾语义相关性和精确匹配。      |

**参考资料：**

1. Srinivas, Aravind. *Lex Fridman Podcast #434 - “Future of AI, Search & the Internet” (Perplexity CEO)*. (2024) – *Perplexity CEO 强调传统检索(BM25)依然有效，纯向量不足，需结合使用*。
2. Lazuk, Ethan. “**How Does Perplexity Work?** A Summary from an SEO’s Perspective” *(2024)* – *介绍 Perplexity 检索从依赖 Bing 到自建爬虫索引的发展，并总结其 BM25 优势观点*。
3. Lazuk, Ethan. *同上*. – *引用 Perplexity 团队访谈，描述其利用 BM25 算法、n-gram 匹配和 PageRank 信号提升检索质量，并用 LLM 提取网页段落*。
4. Fox, Pamela (Microsoft). “**Doing RAG? Vector search is not enough**.” *Microsoft Tech Community Blog* (2024) – *强调 RAG 检索需“全量混合”：向量语义+BM25+融合+语义重排的多步骤管线，Azure Cognitive Search 即提供该默认配置*。
5. Milvus & LlamaIndex Docs. “**Using Full-Text Search with LlamaIndex and Milvus**” (2023) – *介绍 Milvus 2.5+ 支持稀疏 BM25 向量，实现向量库中的全文检索，并展示如何在 LlamaIndex 中构建混合索引*。
6. Haystack Official. “**Hybrid Document Retrieval**.” *Haystack Blog* (2023) – *阐述稀疏(BM25)与稠密(Transformer embeddings)各自优缺点，以及如何在 Haystack 管线中组合两个检索器并融合结果（包括RRF算法）*。
7. OpenAI. “**ChatGPT plugins**” – *插件文档，介绍官方开源的检索插件和浏览插件。指出浏览插件使用 Bing Search API 进行网页检索*。另强调检索插件基于向量数据库，实现私有知识库查询\*。
8. Yoast. “**What is ChatGPT Search (and how does it use Bing data)?**” (2023) – *SEO 文章，解释 ChatGPT Search 与 Bing 的集成关系，确认ChatGPT搜索利用了Bing的索引和实时数据，网站需被Bing收录才会出现在ChatGPT结果中*。
9. Shiftasia. “**Retrieval-Augmented Generation (RAG): A Comprehensive Guide**” (2023) – *全面指南，涵盖 RAG 系统构建各环节。特别对比了检索排名技术（余弦相似度、交叉编码重排、BM25+向量混合）；并介绍了高级检索策略如 RAG-Fusion 查询改写、Multi-hop 迭代检索 等*。
