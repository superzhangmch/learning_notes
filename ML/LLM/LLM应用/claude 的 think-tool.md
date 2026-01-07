### claude 的 think-tool

claude 的 agent 框架有一个 tool, 名叫 think. 它和 LLM 本身的 thinking 功能不同. 关于这个 tool, 见:  https://www.anthropic.com/engineering/claude-think-tool

```
{
  "name": "think",
  "description": "Use the tool to think about something. It will not obtain new information or change the database,"
                 "but just append the thought to the log." # log 指的是 chat 的 messages
                 "Use it when complex reasoning or some cache memory is needed.", # cache memory 并不是外部的物理cache存储. 而是向 LLM 说, 如果你觉得应该把某些东西暂存下(cache下), 就在 think tool里发挥好了. 只是给 LLM 一个"借口"和"格式",让它把想记住的东西显式地写出来
  "input_schema": {
    "type": "object",
    "properties": {
      "thought": {
        "type": "string",
        "description": "A thought to think about."
      }
    },
    "required": ["thought"]
  }
}
```

关于这个tool, 是主 LLM 把 think 的具体内容作为参数传给 tool, 而 tool 本身反而啥也不干
