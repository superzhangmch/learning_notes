LLM 多轮交互中，新一轮需要把过去几轮的交互也发给llm，那么llm server 端怎么处理的？会有某种 cache 吗？按说也可以有的。

根据 https://api-docs.deepseek.com/zh-cn/guides/kv_cache 的 “上下文硬盘缓存”：

![image](https://github.com/user-attachments/assets/2f0a5895-06c1-4ef9-bd8e-af6e7e7593f7)

上图这样的，会中他的上下文硬盘缓存，这其实不就正是这里所说的多轮的前几轮的cache。且据他说，它这时全球第一家这样做的。这得益于它家的 MLA：

![image](https://github.com/user-attachments/assets/736a7c05-a3ac-434b-9917-96ab86c7382c)

那么也就可以推测，LLM 多轮，前几轮交互在新一轮对话中，各家目前一般是不做什么 cache的。

========
另外：下面是 chatgpt deepResearch 的结果：


ChatGPT、Claude、Gemini 这类在线对话模型（官方 Web 或 App 版本）在多轮对话中是如何处理上下文的，特别是他们是否保留 KV Cache 以避免重复进行 prefill？ 

author: chatgpt
date：2024.03

# 主流对话大模型的多轮对话上下文处理策略

多轮对话场景下，大型语言模型需要处理每一轮的新输入，同时参考之前的对话内容。**ChatGPT（OpenAI）**、**Claude（Anthropic）** 和 **Gemini（Google）** 等主流在线对话模型在官方网页或应用中通常有两种策略：要么在第 N 轮对话时**重复提供所有前 N-1 轮的对话作为输入**（即完整地将历史对话拼接进提示，称为 *prefill*），要么**利用模型的 KV 缓存保留前文的内部表示**，使模型能从上一次结束的状态继续推理。下面分别介绍各家在多轮对话中的上下文处理及优化措施，并引用公开资料加以说明。

## ChatGPT（OpenAI）

**默认方式：完整历史作为提示输入。**  ChatGPT 等基于Transformer的模型本身并没有跨对话轮次的长期记忆，模型每次生成回复只考虑它接收到的上下文。因此，在没有特殊优化时，每轮对话都会将**系统提示语和之前所有用户+助手消息串联**后再输入模型，让模型生成新回复 ([Multi-turn conversation best practice - API - OpenAI Developer Community](https://community.openai.com/t/multi-turn-conversation-best-practice/282349#:~:text=const%20messages%20%3D%20%5B%20,)) ([KV Cache with the OAI API - when does it kick in? - API - OpenAI Developer Community](https://community.openai.com/t/kv-cache-with-the-oai-api-when-does-it-kick-in/719616#:~:text=Each%20API%20call%20is%20its,tool%20calls%20without%20external%20interaction))。这种做法确保模型“记住”之前对话内容，但代价是随着对话轮次增加，**提示长度越来越长**，每次推理都要重复计算大量相同的内容，首个输出 token 的延迟不断增加 ([大模型推理优化实践：KV cache 复用与投机采样_kvcache-CSDN博客](https://blog.csdn.net/AlibabaTech1024/article/details/135551973#:~:text=%E5%9C%A8%20%E6%B7%98%E5%AE%9D%E9%97%AE%E9%97%AE%20%E4%B8%AD%EF%BC%8C%E6%9C%89%E4%B8%A4%E7%B1%BB%E5%A4%9A%E8%BD%AE%E5%AF%B9%E8%AF%9D%E7%9A%84%E5%9C%BA%E6%99%AF%EF%BC%9A%E4%B8%80%E6%98%AF%E9%97%AE%E7%AD%94%E7%B1%BB%E7%9A%84%E5%9C%BA%E6%99%AF%EF%BC%8C%E5%AE%83%E6%AF%8F%E6%AC%A1%E8%AF%B7%E6%B1%82%E6%A8%A1%E5%9E%8B%E6%97%B6%E4%BC%9A%E6%8B%BC%E6%8E%A5%E4%B9%8B%E5%89%8D%E7%9A%84%E9%97%AE%E7%AD%94%EF%BC%9B%E4%BA%8C%E6%98%AF%20LangChain%20%E5%BA%94%E7%94%A8%EF%BC%8C%E5%AE%83%E5%9C%A8%E6%A8%A1%E5%9E%8B%E7%94%9F%E6%88%90%E7%BB%93%E6%9D%9F%E5%90%8E%E4%BC%9A%E8%B0%83%E7%94%A8%E5%A4%96%E9%83%A8%E6%8F%92%E4%BB%B6%EF%BC%8C%E6%8B%BC%E6%8E%A5%E6%8F%92%E4%BB%B6%E8%BF%94%E5%9B%9E%E7%9A%84%E7%BB%93%E6%9E%9C%E5%86%8D%E6%AC%A1%E8%AF%B7%E6%B1%82%E6%A8%A1%E5%9E%8B%E3%80%82%E8%BF%99%E4%B8%A4%E7%B1%BB%E5%9C%BA%E6%99%AF%E5%85%B1%E5%90%8C%E7%9A%84%E9%97%AE%E9%A2%98%E6%98%AF%EF%BC%9A%E9%9A%8F%E7%9D%80%E5%AF%B9%E8%AF%9D%E8%BD%AE%E6%95%B0%E7%9A%84%E5%A2%9E%E5%8A%A0%EF%BC%8C%E8%AF%B7%E6%B1%82%E9%95%BF%E5%BA%A6%E5%8F%98%E9%95%BF%EF%BC%8C%E5%AF%BC%E8%87%B4%E6%A8%A1%E5%9E%8B%E7%9A%84,First%20Token%20Time%EF%BC%88%E4%B8%8B%E7%A7%B0%20FTT%EF%BC%89%E4%B8%8D%E6%96%AD%E5%8F%98%E9%95%BF%E3%80%82))。

**KV 缓存与前缀复用优化。** 为了减少重复计算，OpenAI 对ChatGPT的后台推理进行了优化，引入**Prompt Caching（提示缓存）**机制，实现多轮对话中**前缀的KV缓存复用** ([Prompt Caching in the API | OpenAI](https://openai.com/index/api-prompt-caching/#:~:text=API%20calls%20to%20supported%20models,changes%20to%20your%20API%20integration))。简单来说，如果新一轮对话的提示开头部分与之前某次请求的前缀相同，系统会重用已缓存的键值对（KV）而不重新计算它们。这意味着在第 N 轮对话时，**模型无需重新计算前 N-1 轮不变的上下文表示**，而只处理新增的用户提问和生成新的回答，从而加快推理速度并降低计算成本 ([Prompt Caching with OpenAI, Anthropic, and Google Models](https://www.prompthub.us/blog/prompt-caching-with-openai-anthropic-and-google-models#:~:text=,to%20increase%20cache%20hit%20rates)) ([Prompt Caching in the API | OpenAI](https://openai.com/index/api-prompt-caching/#:~:text=API%20calls%20to%20supported%20models,changes%20to%20your%20API%20integration))。OpenAI 官方指出，当提示长度超过约1024个 token 时会自动触发提示缓存，对重复的前缀部分不再重复计费 ([Prompt Caching in the API | OpenAI](https://openai.com/index/api-prompt-caching/#:~:text=API%20calls%20to%20supported%20models,changes%20to%20your%20API%20integration))。社区实测表明，使用缓存后**延迟可降低约80%**，相关部分的输入token费用约减少一半 ([Prompt Caching with OpenAI, Anthropic, and Google Models](https://www.prompthub.us/blog/prompt-caching-with-openai-anthropic-and-google-models#:~:text=,to%20increase%20cache%20hit%20rates))。

 ([Scaling ChatGPT: Five Real-World Engineering Challenges](https://newsletter.pragmaticengineer.com/p/scaling-chatgpt#:~:text=match%20at%20L351%20system%20tries,to%20work%20quadratically%2C%20not%20linearly))这种前缀KV缓存的维护需要占用GPU显存，但极大提高了多轮对话的效率。如果缓存未命中（即需要重新计算已有前缀），GPU计算量会随着序列长度二次增长，延迟明显上升 ([Scaling ChatGPT: Five Real-World Engineering Challenges](https://newsletter.pragmaticengineer.com/p/scaling-chatgpt#:~:text=match%20at%20L351%20system%20tries,to%20work%20quadratically%2C%20not%20linearly))。因此，ChatGPT后台会尽量将每个对话会话固定在同一服务器上，在**短时间间隔（通常几分钟）内重用缓存** ([Prompt Caching in the API | OpenAI](https://openai.com/index/api-prompt-caching/#:~:text=Caches%20are%20typically%20cleared%20after,are%20not%20shared%20between%20organizations))。官方信息显示，OpenAI的缓存一般在**5~10分钟不活动后**失效，最长不超过1小时 ([Prompt Caching in the API | OpenAI](https://openai.com/index/api-prompt-caching/#:~:text=Caches%20are%20typically%20cleared%20after,are%20not%20shared%20between%20organizations))。综上，ChatGPT 的官方服务并非每轮都完全重新计算所有历史，而是通过**维护上文的KV缓存**实现了多轮对话状态的复用和加速。

## Claude（Anthropic）

**长对话与大窗口支持。** Anthropic 的 Claude 模型以支持超长上下文（如100k tokens）著称。在Claude的官方聊天中，如果每轮都传入完整历史，将产生巨大的计算开销。为此，Anthropic 也采用了**提示缓存（Prompt Caching）**策略，以在多轮对话中重用不变的上下文部分。Anthropic在2024年8月官方博客中宣布了Claude的提示缓存功能，允许在多次API调用之间缓存经常重复的提示内容 ([Prompt caching with Claude \ Anthropic](https://www.anthropic.com/news/prompt-caching#:~:text=Prompt%20caching%2C%20which%20enables%20developers,Opus%2C%20and%20Claude%203%20Haiku))。这表明Claude能够**保留先前对话内容对应的内部表示（KV）**，在后续轮次中避免重复处理，从而**将长对话的成本降低最多90%，首 token 延迟降低最高85%** ([Prompt caching with Claude \ Anthropic](https://www.anthropic.com/news/prompt-caching#:~:text=Prompt%20caching%2C%20which%20enables%20developers,Opus%2C%20and%20Claude%203%20Haiku))。

**实现方式与优化效果。** 与OpenAI不同，Claude的提示缓存需要开发者在API请求中明确启用并指定缓存范围（例如用特殊header和参数标记哪些部分可缓存） ([Prompt Caching with OpenAI, Anthropic, and Google Models](https://www.prompthub.us/blog/prompt-caching-with-openai-anthropic-and-google-models#:~:text=)) ([Prompt Caching with OpenAI, Anthropic, and Google Models](https://www.prompthub.us/blog/prompt-caching-with-openai-anthropic-and-google-models#:~:text=,0))。Anthropic支持将提示划分为多达四段进行分别缓存（如工具调用结果、系统提示、消息等），缓存的生命周期默认仅**5分钟（每次使用会刷新时间）** ([Prompt Caching with OpenAI, Anthropic, and Google Models](https://www.prompthub.us/blog/prompt-caching-with-openai-anthropic-and-google-models#:~:text=,0))。尽管需要手动配置，这一机制在长对话中效果显著——官方提供的用例显示，**对话代理在有长指令或长资料的多轮对话中，通过缓存可显著减少每轮提示处理的开销** ([Prompt caching with Claude \ Anthropic](https://www.anthropic.com/news/prompt-caching#:~:text=Prompt%20caching%20can%20be%20effective,repeatedly%20in%20subsequent%20requests%2C%20including))。例如，将一本书全文嵌入首轮提示并对其提问，多轮对话开启缓存后**首token等待从约10秒降至2.5秒** ([Prompt caching with Claude \ Anthropic](https://www.anthropic.com/news/prompt-caching#:~:text=Use%20case%20Latency%20w%2Fo%20caching,53))。因此在Claude的官方服务中，可以推断其内部也应用了类似的KV缓存复用：上一轮对话生成后，模型的KV缓存并不立即丢弃，而是在会话存续期内保留，用于加速后续回答。这样，第 N 轮对话时Claude实际上**继续利用了前N-1轮的上下文状态**进行推理，而非每次都从零开始计算完整历史。

## Gemini（Google）

**“上下文缓存”机制。** Google 的新一代对话模型（Gemini，在Bard及开发者接口中提供）同样面临长对话的效率问题。Google采用的策略称为**Context Caching（上下文缓存）** ([Prompt Caching with OpenAI, Anthropic, and Google Models](https://www.prompthub.us/blog/prompt-caching-with-openai-anthropic-and-google-models#:~:text=%2A%20Uses%20the%20term%20,not%20available%20for%20beta%20versions))。在其云服务Vertex AI的文档中，Google说明开发者可以创建一个上下文缓存，将大量内容一次性缓存，然后在对同一个 Gemini 模型的多次请求中反复引用 ([Create a context cache  |  Generative AI  |  Google Cloud](https://cloud.google.com/vertex-ai/generative-ai/docs/context-cache/context-cache-create#:~:text=You%20must%20create%20a%20context,request%20to%20create%20the%20cache))。缓存的内容可以是文本、音频、视频等（Gemini是多模态模型），创建后默认**保存60分钟**，超时失效（支持自定义有效期） ([Create a context cache  |  Generative AI  |  Google Cloud](https://cloud.google.com/vertex-ai/generative-ai/docs/context-cache/context-cache-create#:~:text=Cached%20content%20has%20a%20finite,see%20Update%20the%20expiration%20time))。这一机制等价于**让模型保留了指定内容的KV表示**：后续请求只需提供一个缓存标识，模型就能在生成时直接利用已存的上下文，而无需每次都输入并处理那段内容 ([Create a context cache  |  Generative AI  |  Google Cloud](https://cloud.google.com/vertex-ai/generative-ai/docs/context-cache/context-cache-create#:~:text=You%20must%20create%20a%20context,request%20to%20create%20the%20cache))。

**多轮对话应用与特性。** 有了上下文缓存，应用可以在对话开始时先缓存长资料或长系统提示，之后用户每提一个新问题，只附上缓存引用和当前问题即可，大幅减少传输和处理开销。这对**多轮对话特别是长上下文对话**很有利。例如，在Bard这样与用户持续交互的场景，Gemini模型很可能在后台对用户会话维护一个缓存，使得每轮回答时无需重新处理之前已经提供给模型的大段背景。 ([Prompt Caching with OpenAI, Anthropic, and Google Models](https://www.prompthub.us/blog/prompt-caching-with-openai-anthropic-and-google-models#:~:text=%2A%20Uses%20the%20term%20,not%20available%20for%20beta%20versions))据第三方总结，Google的上下文缓存需要由开发者显式使用，默认1小时期限，可自定义更长；缓存命中时按较低代价计费 ([Prompt Caching with OpenAI, Anthropic, and Google Models](https://www.prompthub.us/blog/prompt-caching-with-openai-anthropic-and-google-models#:~:text=%2A%20Uses%20the%20term%20,not%20available%20for%20beta%20versions))。虽然Google官方未直接对外详述Bard后台是否持续维护KV缓存，但从其提供的API特性推测，**Gemini在官方对话服务中应具备多轮状态复用能力**，以支持更长对话和提升响应速度。

## 总结与对比

综上，三大在线对话模型的官方实现都**不会简单地在每轮对话从头处理完整历史**，而是引入了**KV缓存复用**或**上下文缓存**等优化来维护多轮对话的上下文状态：

- **ChatGPT（OpenAI）**：每轮对话仍以完整历史作为输入，但服务器端自动**维护前缀的KV缓存**，使模型可跳过重复计算 ([Prompt Caching in the API | OpenAI](https://openai.com/index/api-prompt-caching/#:~:text=API%20calls%20to%20supported%20models,changes%20to%20your%20API%20integration))。在短暂会话间隔内重用缓存，可大幅降低延迟和计算（缓存命中部分输入token成本降低约50% ([Prompt Caching with OpenAI, Anthropic, and Google Models](https://www.prompthub.us/blog/prompt-caching-with-openai-anthropic-and-google-models#:~:text=,to%20increase%20cache%20hit%20rates))）。若会话闲置超过几分钟，缓存可能失效，需要重新预填充历史。 ([Prompt Caching in the API | OpenAI](https://openai.com/index/api-prompt-caching/#:~:text=Caches%20are%20typically%20cleared%20after,are%20not%20shared%20between%20organizations))

- **Claude（Anthropic）**：允许显式指定哪些提示内容缓存。**复用先前对话的内部表示**来加速后续轮次，官方数据显示长对话场景下首词延迟降低最多 **75%** ([Prompt caching with Claude \ Anthropic](https://www.anthropic.com/news/prompt-caching#:~:text=Use%20case%20Latency%20w%2Fo%20caching,53))、相关token成本降低过半 ([Prompt caching with Claude \ Anthropic](https://www.anthropic.com/news/prompt-caching#:~:text=Prompt%20caching%2C%20which%20enables%20developers,Opus%2C%20and%20Claude%203%20Haiku))。默认缓存寿命较短（约5分钟） ([Prompt Caching with OpenAI, Anthropic, and Google Models](https://www.prompthub.us/blog/prompt-caching-with-openai-anthropic-and-google-models#:~:text=,0))，强调及时刷新。其官方聊天应用推测也利用了这些技术，使Claude能高效处理超长上下文对话。

- **Gemini（Google）**：通过“上下文缓存”让模型**在多次请求间共享上下文** ([Create a context cache  |  Generative AI  |  Google Cloud](https://cloud.google.com/vertex-ai/generative-ai/docs/context-cache/context-cache-create#:~:text=You%20must%20create%20a%20context,request%20to%20create%20the%20cache))。开发者可将长资料一次缓存，后续对话反复引用，缓存默认有效期 **60 分钟** ([Create a context cache  |  Generative AI  |  Google Cloud](https://cloud.google.com/vertex-ai/generative-ai/docs/context-cache/context-cache-create#:~:text=Cached%20content%20has%20a%20finite,see%20Update%20the%20expiration%20time))。这意味着在官方聊天如Bard中，Gemini能够保持一定的对话状态而无需每轮重发所有背景。与Anthropic类似，Google要求预先创建缓存，但一旦建立，**多轮对话只需增量处理新输入**，未变部分直接复用 ([Prompt Caching with OpenAI, Anthropic, and Google Models](https://www.prompthub.us/blog/prompt-caching-with-openai-anthropic-and-google-models#:~:text=%2A%20Uses%20the%20term%20,not%20available%20for%20beta%20versions))。

总的来看，这些优化策略在**长上下文或频繁交互**时尤其关键。通过维护KV缓存并复用不变的前缀，各家模型有效降低了多轮对话的计算冗余和延迟，提高了响应效率 ([Prompt caching with Claude \ Anthropic](https://www.anthropic.com/news/prompt-caching#:~:text=Prompt%20caching%20can%20be%20effective,repeatedly%20in%20subsequent%20requests%2C%20including)) ([Prompt Caching with OpenAI, Anthropic, and Google Models](https://www.prompthub.us/blog/prompt-caching-with-openai-anthropic-and-google-models#:~:text=,to%20increase%20cache%20hit%20rates))。公开的博客和文档已经披露了这些机制，表明主流厂商在其官方服务中都采用了**多轮对话状态复用**技术来提升用户体验和降低成本。今后，随着对话长度需求的增加，关于缓存管理、上下文截断与压缩等方面可能还会有进一步的优化研究。  

 ([Prompt Caching in the API | OpenAI](https://openai.com/index/api-prompt-caching/#:~:text=API%20calls%20to%20supported%20models,changes%20to%20your%20API%20integration)) ([Prompt caching with Claude \ Anthropic](https://www.anthropic.com/news/prompt-caching#:~:text=Prompt%20caching%20can%20be%20effective,repeatedly%20in%20subsequent%20requests%2C%20including)) ([Create a context cache  |  Generative AI  |  Google Cloud](https://cloud.google.com/vertex-ai/generative-ai/docs/context-cache/context-cache-create#:~:text=You%20must%20create%20a%20context,request%20to%20create%20the%20cache)) ([Scaling ChatGPT: Five Real-World Engineering Challenges](https://newsletter.pragmaticengineer.com/p/scaling-chatgpt#:~:text=match%20at%20L351%20system%20tries,to%20work%20quadratically%2C%20not%20linearly))

### other
> **一般所说的 KV Cache，默认是指 “生成一个回答过程中，用来避免重复 attention 的 token-by-token 缓存”。**
>
> 多轮对话中缓存上下文（前 N 轮）的 KV 表示，也属于一种缓存，但通常会特别说明为：
> - prefix cache
> - prompt cache
> - 或 context cache
> 来与“标准的 KV cache”区分。
 
