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

### 参考
- https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview
- https://agentskills.io/home

