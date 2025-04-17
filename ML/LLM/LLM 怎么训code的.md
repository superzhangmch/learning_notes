现在的大模型 LLM 的写代码能力都很强。这样的能力在pretrain阶段是怎么打造出来的。当然，这是通过把大量的代码放入 pretrain 数据集训练出来的。

但是，我们知道，普通的代码，不会有那么多的注释，写的也不规范，结构也没那么好，但是现在的 LLM 写的代码，注释非常完善，非常规范。大量的人写的代码，直接放进去 pretrain，总感觉LLM学出来的代码风格也会是注释很少，比较杂乱，不规范。

大量的代码，是怎么放进去 pretrain的？是稍为清洗（去除不靠谱的代码）就可以吗？还是说需要设法弄出大量的规范代码才行？

# 主流大模型编程能力训练方法调研

author: chatgpt deepresearch

## 预训练阶段的代码数据收集与清洗

在预训练阶段，主流大型语言模型通常会使用大规模的公开可用代码语料。例如，OpenAI 的 Codex 模型（GPT-3 的代码专用微调版）就是从 GitHub 获取了海量代码数据进行训练 ([[2107.03374] Evaluating Large Language Models Trained on Code](https://ar5iv.org/abs/2107.03374#:~:text=Our%20training%20dataset%20was%20collected,final%20dataset%20totaled%20159%20GB))。具体而言，OpenAI 在 2020 年收集了约 5400 万个公开的 GitHub 代码库，其中提取出所有小于 1MB 的 Python 源文件，共得到约 179GB 的**独立代码文件**（去除了精确重复） ([[2107.03374] Evaluating Large Language Models Trained on Code](https://ar5iv.org/abs/2107.03374#:~:text=Our%20training%20dataset%20was%20collected,final%20dataset%20totaled%20159%20GB))。然后，他们通过一系列规则过滤掉低质量或无意义的文件，例如**自动生成的代码**、平均行长超过100的代码（可能是压缩/混淆代码）、最长行超过1000字符的文件，以及字母数字字符占比极低的文件 ([[2107.03374] Evaluating Large Language Models Trained on Code](https://ar5iv.org/abs/2107.03374#:~:text=Our%20training%20dataset%20was%20collected,final%20dataset%20totaled%20159%20GB)) ([[2107.03374] Evaluating Large Language Models Trained on Code](https://ar5iv.org/abs/2107.03374#:~:text=MB,final%20dataset%20totaled%20159%20GB))。经过这些清洗步骤后，最终用于训练的代码数据集大小约为159GB ([[2107.03374] Evaluating Large Language Models Trained on Code](https://ar5iv.org/abs/2107.03374#:~:text=MB,final%20dataset%20totaled%20159%20GB))。由此可见，在数据收集上，GitHub 等开源平台是主要来源，而清洗过程注重去重和过滤异常情况（如机器生成代码、极端格式等），以确保模型看到的是**多样且有意义**的代码。

除了代码仓库，本阶段也会收集**与代码相关的自然语言文本**，例如编程问答论坛的内容。Meta 的 Code Llama 模型就明确提到，其5000亿标记的训练语料中有约8%的样本来自“与代码相关的自然语言数据集”，包含了许多关于代码的讨论和问答片段 ([Code Llama: Open Foundation Models for Code](https://arxiv.org/html/2308.12950v3#:~:text=We%20train%20Code%C2%A0Llama%207B%2C%2013B,BPE))。这意味着类似于 Stack Overflow 的问答数据也被纳入，用于提供代码上下文的解释说明。这样做有助于模型既学习纯代码，又学习人们在讨论代码时的语言表达。这类数据往往包含**问题描述、代码片段和回答**，可以让模型理解编程问题的语境。总体而言，预训练阶段的主流做法是在尽可能大的代码语料上训练，同时通过**去重**（如哈希去重、近重复检测 ([Code Llama: Open Foundation Models for Code](https://arxiv.org/html/2308.12950v3#:~:text=We%20train%20Code%C2%A0Llama%207B%2C%2013B,BPE))）和简单启发式规则**过滤低质量内容**，保证数据覆盖广泛且不至于灌入明显无用的代码。

值得注意的是，有些项目还会考虑**开源许可**等因素来过滤数据。例如 BigCode 项目发布的 “The Stack” 数据集就仅包含许可友好的公开代码。但像 OpenAI 和 Meta 等用于内部模型训练时，具体如何处理代码许可证未完全公开。不过，“公共可用代码”通常指从互联网抓取的开源代码，可能包括各种许可证。在学术和开源界，常采用许可证过滤确保合规，而工业模型是否过滤取决于各自政策。总体来说，**数据源**主要来自 GitHub及类似平台的大规模爬取，辅以 StackOverflow 等编程社区内容；**数据清洗**侧重于去重和过滤噪音，确保模型不会被大量重复或无效代码干扰 ([[2107.03374] Evaluating Large Language Models Trained on Code](https://ar5iv.org/abs/2107.03374#:~:text=Our%20training%20dataset%20was%20collected,final%20dataset%20totaled%20159%20GB)) ([[2107.03374] Evaluating Large Language Models Trained on Code](https://ar5iv.org/abs/2107.03374#:~:text=MB,final%20dataset%20totaled%20159%20GB))。

## 训练数据中代码质量与注释的选择

在预训练语料的选择上，当前主流做法更看重数据规模和覆盖面，而非严格挑选“高质量、有良好注释”的代码子集。换句话说，**以量取胜**是常见策略，质量控制通常通过简单的规则过滤来实现，而不会人工精选大量风格规范、注释丰富的代码。在 OpenAI 的案例中，Codex 所用的 159GB GitHub 代码数据基本上是自动抓取后略加清理的结果，其中包含各式各样的代码 ([[2107.03374] Evaluating Large Language Models Trained on Code](https://ar5iv.org/abs/2107.03374#:~:text=Our%20training%20dataset%20was%20collected,final%20dataset%20totaled%20159%20GB))。并没有证据表明他们只挑选了那些注释完备或编码风格良好的仓库；相反，绝大部分公开仓库的代码——无论风格好坏——都可能出现在训练集中。过滤过程主要淘汰**明显无用或有问题**的内容（如机器生成代码、极端长行等），而**并未针对代码注释多少进行筛选** ([[2107.03374] Evaluating Large Language Models Trained on Code](https://ar5iv.org/abs/2107.03374#:~:text=Our%20training%20dataset%20was%20collected,final%20dataset%20totaled%20159%20GB))。

例如，Codex 使用的GitHub数据集只是在基本清理后就用于训练，并没有进一步按注释丰富度或编码规范度来打分筛选 ([[2107.03374] Evaluating Large Language Models Trained on Code](https://ar5iv.org/abs/2107.03374#:~:text=Our%20training%20dataset%20was%20collected,final%20dataset%20totaled%20159%20GB))。再比如，Google 在 PaLM 等模型的预训练中据报道也加入了大量源代码（涵盖多种语言），目的是提升模型的编程能力，但公开信息并未提到偏好有注释的代码，只提到扩大代码语料比例以提高多样性和质量。这说明业界普遍认为，让模型接触**足够大量**的代码，比限定风格更重要，因为模型可以从海量数据中自行学习什么是高质量代码。**简单的质量过滤**（如去掉语法不合法或明显无意义的片段）通常有，但**不会严格限定**代码一定要有注释或符合某种风格。

另外，一些模型在预训练后会进行**专门的代码微调**。这些微调数据有时是人为设计的问题-解答对，可能比随机GitHub代码更规范。例如 OpenAI 在训练 Codex 时，除了GitHub语料，还构建了一小部分**编程练习题数据集**进行二次微调，以更贴近代码生成评测任务 ([
     
        
        OpenAI Codex: Why the revolution is still missing | dida blog
    
](https://dida.do/blog/codex#:~:text=Fine))。这些题目和答案往往比较简洁规范，但那是为了提高模型解题能力，而非专门为了教模型写更多注释。总体来看，主流做法是**广泛收集**公开代码（包括有无注释的各种风格)，在此基础上通过规模效应提升模型编程能力，而不是牺牲数据量去严格挑选“注释丰富”的代码子集。

## 模型代码规范、注释丰富风格的来源

令人印象深刻的是，诸如 GPT-4、Claude 等模型往往能生成**风格规范、带有丰富注释的代码**。这种能力的来源可以归结为两个方面：**预训练的模式学习**和**后续对齐微调（如指令微调和RLHF）的影响**。

首先，在预训练过程中，模型从大规模代码语料中**学习到了代码注释和文档的模式**。许多开源项目的代码（尤其是大型库或知名项目）本身就包含规范的编码风格和文档说明，例如文件头的版权声明、函数的 docstring、关键步骤的行内注释等。模型阅读了大量这样的示例，自然就掌握了在代码中加入文档和注释的写作习惯。当模型在生成代码时，如果上下文暗示需要说明，它会调用这种“记忆”，自动补充适当的注释。例如，有研究通过让模型练习**代码填空**（Infilling）的方式，专门训练模型生成代码中的缺失部分，包括自动添加函数注释。Meta 的 Code Llama 就采用了**代码补全/填空训练**来增强文档生成能力：在训练时随机遮盖掉代码中的一部分（如函数docstring或代码段），让模型预测填充，从而学会生成类似docstring这样的**代码内文档** ([Code Llama: Open Foundation Models for Code](https://arxiv.org/html/2308.12950v3#:~:text=Code%20infilling%20is%20the%20task,code%20documentation%20%28e.g.%2C%20docstrings))。这种训练方式可以明显提升模型在正常生成时编写注释和文档的倾向 ([Code Llama: Open Foundation Models for Code](https://arxiv.org/html/2308.12950v3#:~:text=Code%20infilling%20is%20the%20task,code%20documentation%20%28e.g.%2C%20docstrings))。

其次，更重要的是**后续的指令微调和人类反馈强化学习（RLHF）对模型风格的塑造**。OpenAI 在 GPT-4 技术报告中指出，基座模型经过预训练后，仍需要通过后续微调来“对齐”用户期望——预训练主要决定了模型的能力上限，而微调/RLHF决定了模型回答的形式和风格 ([GPT-4 | OpenAI](https://openai.com/index/gpt-4-research/#:~:text=of%20ways%20that%20might%20be,RLHF%20%E2%81%A0))。换言之，模型能否主动给出详尽注释，很多时候取决于微调阶段教给模型的**回答风格偏好**。以 ChatGPT/GPT-4 为例，在使用RLHF打造成为对话助手的过程中，人类标注者往往倾向于选择**解释更清楚、注释更充分**的代码答案作为最佳答案。这种偏好会反映在奖励模型中，进而引导最终模型更频繁地输出带有解释性注释的代码。OpenAI提到，RLHF 主要用于**引导模型的行为**朝向人类期望 ([GPT-4 | OpenAI](https://openai.com/index/gpt-4-research/#:~:text=of%20ways%20that%20might%20be,RLHF%20%E2%81%A0))（例如更详细地解释步骤），而模型的核心编程**能力**仍然来自于预训练的大量代码学习 ([GPT-4 | OpenAI](https://openai.com/index/gpt-4-research/#:~:text=learning%20with%20human%20feedback%20,%E2%81%A0))。因此，像 GPT-4 这样的模型之所以表现出乐于给代码加注释、解释意图的风格，很大程度上是因为在对话微调时被教导成了一个“乐于解释的助手”。

Anthropic 的 Claude 模型类似地通过**宪法式AI (Constitutional AI)**和人类反馈来训练模型在对话中表现得更加乐于助人、详细说明。这意味着当用户让 Claude 编写代码时，Claude 往往会给出详尽的解释或内嵌注释，以确保易懂和有帮助。这不是因为训练中只见过有注释的代码，而是因为**对话训练阶段**强调了“帮助用户理解”的原则，模型因此倾向于主动把代码意图说清楚。总而言之，**模型的代码注释风格是训练得来的**：预训练提供了范例（模型知道代码可以怎样写注释），而指令微调/RLHF阶段确定了输出风格（模型选择是否以及如何在答案中加入注释来满足用户）。这两方面共同作用，使得当前的大模型能输出规范且注释丰富的代码。

## 模型代码风格与人类习惯的对齐与改进

关于模型是否会学到人类“懒得写注释”的习惯，以及模型风格如何与原始数据风格对齐或改进，这是一个有趣的问题。一般来说，**预训练模型会倾向模仿训练语料的统计特征**。如果大量训练代码缺乏注释，模型的基础倾向可能也是生成较少注释的代码。这意味着**模型确实能反映人类代码中常见的疏于写注释的现象**。例如，如果让一个未经过指令微调的基础模型直接完成代码补全，它很可能只给出完成功能所需的代码，而不会额外加上长篇注释，因为很多训练样本就是这样的风格。然而，现代大模型通过后续对齐训练，往往**在风格上进行了人为引导的调整**，有意改善了这种“人类懒惰习惯”。

从实践来看，经过指令微调的对话式模型（如 ChatGPT、Claude）往往**比原始代码语料更加健谈和注释丰富**。这是一种有意的偏离原始数据分布的行为，目的是提升对用户的友好度和可解释性。训练者希望模型给出“理想化”的答案风格——比如即便很多程序员实际不写注释，模型回答用户时依然会加注释以帮助理解。因此，我们看到模型的代码风格相对于平均的人类代码风格而言，其实是经过**优化和改进**的。例如，ChatGPT 往往会在给出代码前先用自然语言解释思路，或者在代码中插入注释说明关键步骤，这种做法在普通的开源项目代码中并不总是这么频繁。有研究指出，如果不加干预，大模型会严格按训练统计来（那样可能就复现人类代码中注释稀少的情况）；但通过人类反馈微调，可以**鼓励模型比训练数据更积极地添加注释**，以提高可读性和用户满意度 ([GPT-4 | OpenAI](https://openai.com/index/gpt-4-research/#:~:text=learning%20with%20human%20feedback%20,%E2%81%A0))。OpenAI 也承认，在不特别优化的情况下，RLHF可能导致模型在专业任务上的性能略有下降 ([GPT-4 | OpenAI](https://openai.com/index/gpt-4-research/#:~:text=learning%20with%20human%20feedback%20,%E2%81%A0))（因为模型开始更加注重符合人类偏好，可能牺牲一点点原始精准性），这正是风格调整带来的权衡。不过他们和其它研究者都会通过混入一定比例的原始任务数据来防止能力退化。例如，Meta 在训练 Code Llama 的指令-following版本时，特意保留了一部分原始代码语料（6%）和普通自然语言语料（2%）一同训练，以防止模型在对齐对话风格时**遗忘原本编程技能或偏离代码本身的准确性** ([Code Llama: Open Foundation Models for Code](https://arxiv.org/html/2308.12950v3#:~:text=)) ([Code Llama: Open Foundation Models for Code](https://arxiv.org/html/2308.12950v3#:~:text=In%20order%20to%20prevent%20the,2))。

至于模型是否“学会”人类懒得写注释的坏习惯，可以说**既会模仿也会超越**。模型会模仿人类代码中的模式：如果很多函数通常只有一个docstring而没有行内注释，模型默认也会这么做。但模型也不会无缘无故添加并不存在于训练分布的冗余注释。此外，通过后期的对齐，模型被引导在与人交互时提供比平均训练样本更多的解释。因此，相比原始数据，模型的输出风格往往是**对其进行了优化的版本**：在不影响功能前提下提供更多有用信息。这种风格对齐在很多实验中是显著的——例如未微调的代码模型可能返回冷冰冰的代码片段，而经过对话微调的模型会返回代码并配以说明。这表明模型的风格可以在训练中被人为**调节**，而不只是被动地反映训练语料。

当然，模型的行为还是可以**根据用户要求进行调整**。如果用户明确表示不需要解释或注释，模型也能生成简洁的、没有多余评论的代码。这种灵活性说明模型并非固定输出冗长注释，而是学会了在人类偏好之间取得平衡：既能复现简洁风格，也能提供详尽说明。总的来说，主流大模型通过预训练掌握了人类代码的真实风格分布（其中包括“懒得写注释”的倾向），但又通过指令微调和RLHF进行了**风格重塑**，使其在交互场景中倾向于更加规范、注释丰富的风格，以提升代码的可读性和对用户的友善度。这种风格既可以看作是对原始数据中良好编程实践的提炼，也可以视为模型在对齐人类理想输出方面的一种**改进**。模型最终呈现的代码风格，正是原始数据学习和后期人为引导共同作用的结果：在必要时对齐人类习惯（简洁）、在可能时超越人类习惯（提供更详尽的注释和说明）。 ([Code Llama: Open Foundation Models for Code](https://arxiv.org/html/2308.12950v3#:~:text=)) ([GPT-4 | OpenAI](https://openai.com/index/gpt-4-research/#:~:text=learning%20with%20human%20feedback%20,%E2%81%A0))

**参考文献：**

- OpenAI Codex 官方论文 (Chen et al. 2021)，关于代码数据集的描述 ([[2107.03374] Evaluating Large Language Models Trained on Code](https://ar5iv.org/abs/2107.03374#:~:text=Our%20training%20dataset%20was%20collected,final%20dataset%20totaled%20159%20GB)) ([[2107.03374] Evaluating Large Language Models Trained on Code](https://ar5iv.org/abs/2107.03374#:~:text=MB,final%20dataset%20totaled%20159%20GB))  
- Meta AI 发布的 Code Llama 技术报告 (Rozière et al. 2023)，关于代码语料构成和训练策略的说明 ([Code Llama: Open Foundation Models for Code](https://arxiv.org/html/2308.12950v3#:~:text=We%20train%20Code%C2%A0Llama%207B%2C%2013B,BPE)) ([Code Llama: Open Foundation Models for Code](https://arxiv.org/html/2308.12950v3#:~:text=Code%20infilling%20is%20the%20task,code%20documentation%20%28e.g.%2C%20docstrings))  
- OpenAI GPT-4 技术报告 (OpenAI 2023)，关于预训练与对齐过程作用的讨论 ([GPT-4 | OpenAI](https://openai.com/index/gpt-4-research/#:~:text=of%20ways%20that%20might%20be,RLHF%20%E2%81%A0)) ([GPT-4 | OpenAI](https://openai.com/index/gpt-4-research/#:~:text=learning%20with%20human%20feedback%20,%E2%81%A0))  
- Code Llama 指令微调部分的数据混合法，防止能力退化的措施 ([Code Llama: Open Foundation Models for Code](https://arxiv.org/html/2308.12950v3#:~:text=)) ([Code Llama: Open Foundation Models for Code](https://arxiv.org/html/2308.12950v3#:~:text=In%20order%20to%20prevent%20the,2))  
- Dida Blog 对 OpenAI Codex 的解读 (2022)，提及Codex微调数据集及HumanEval评测 ([
     
        
        OpenAI Codex: Why the revolution is still missing | dida blog
    
](https://dida.do/blog/codex#:~:text=Fine)) (辅助理解模型训练流程)
