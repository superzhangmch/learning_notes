简单说, 它是关于做一个具体的事, 应该怎么做的. 同样是做事, MCP 是说有什么资源可以利用. 而 skills 则是告诉你怎么做事.

具体的一些实际实现: 
- claude 官方实现: https://github.com/anthropics/skills/tree/main/skills

从里面的 pdf skill 看( https://github.com/anthropics/skills/blob/main/skills/pdf/SKILL.md ): 
- Merge PDFs
- Split PDF
- Extract Metadata/Rotate Pages/pdfplumber - Text and Table Extraction
- etc

等操作, 如果任务中真的涉及, 那么按此来做就是了. LLM 固然也能想出一种方式完美做到, 终究不可控, 或者不是你想要的. 而用了 skill, 就不用每次啰嗦叮嘱了.

### 原理

(1). SKILL.md

skills 根目录下, 放一堆子目录. 每个代表一个 skill. 每个子目录内有一个 SKILL.md: 头部以固定格式存有 skill name 与 skill description 信息, 然后是关于该 skill 的其他描述. 如果涉及到别的, 在 skill.md 中指明, 同时把相关文件放到 skill 目录下即可: 

<img width="553" height="171" alt="image" src="https://github.com/user-attachments/assets/55070314-642e-48c8-b8cd-85dcd392efc0" />

SKILL.md 例子: 
```
---
name: pdf-processing
description: Extract text and tables from PDF files, fill forms, merge documents.
---

# PDF Processing

## When to use this skill
Use this skill when the user needs to work with PDF files...

## How to extract text
1. Use pdfplumber for text extraction...

## How to fill forms
...
```

(2). LLM 怎么用它

LLM 把 skills 的 name/description 放到 system prompt, 这样它就知道有哪些 skill 可以用. 如果处理用户请求时, 如果它判断需要用到某个 skill, 它通过 function call 读取 SKILL.md 就知道该怎么按指南做事了.

整个过程中, LLM 自己决定是否应该用某个 skill, 从而 lazy load SKILL.md 到 context. 它读了 SKILL.md 后, 如果发现有必要, 它会自动使用 SKILL.md 提到的 skill 目录下的其他内容(仍然是通过工具调用: 如果是代码, 则直接执行, 而不必读取源代码).

```
from https://agentskills.io/what-are-skills:

How skills work: Skills use progressive disclosure to manage context efficiently

- Discovery: At startup, agents load only the name and description of each available skill, just enough to know when it might be relevant.
- Activation: When a task matches a skill’s description, the agent reads the full SKILL.md instructions into context.
- Execution: The agent follows the instructions, optionally loading referenced files or executing bundled code as needed.
```

### 参考
- https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview
- https://agentskills.io/home

