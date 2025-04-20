### system prompt 怎么和chat 记录拼一起, 形成最终的塞给 LLM 的 prompt 的？

虽然可以猜测怎么做，还是问问 LLM。

chatgpt 说： 
```
System Prompt: "You are a helpful assistant."
Chat History:
User: "What is the capital of France?"
Assistant: "The capital of France is Paris."
User: "And the population?"
Current Question: "What is the population of Paris?"

The combined input is sent to the LLM as a single prompt.
```

chatgpt 4o 说:
```
[System Prompt]
User: [First User Input]
Assistant: [First Model Response]
User: [Second User Input]
Assistant: [Second Model Response]
...
User: [Current User Input]
```

如果聊天过长，怎么截断？AI 说多种截断法，总之会保证 system prompt 不被截走。

### 实际应用中怎么组织 prompt
人设、要求、输出格式等，放入 system prompt 是很自然想法。但按照上面拼接法，如果会话历史过长，sys_prompt 距离最后的用户query，以及最近的会话历史就会过远，于是 sys_prompt 的遵从就会变差。这时候可以这样组织 prompt：
```
【System Prompt BEGIN
...
System Prompt end】

User: [First User Input]
Assistant: [First Model Response]

User: [Second User Input]
Assistant: [Second Model Response]
...
User: 【 [use prompt begin
...
...
ueer prompt end]
user_query: 请问。。。
】
```
也就是把prompt 拆分成两份。实际中，有时会很有效。

----

### 追加：

另外后来了解到： chatML 格式，就是干这个的。最后就是转成了该格式。

比如：

```
[
  {"role": "system", "content": "You are a helpful assistant."},
  {"role": "user", "content": "Who won the world cup in 2018?"},
  {"role": "assistant", "content": "France won the 2018 FIFA World Cup."}
]
```

转化成了
```
<|im_start|>system
You are a helpful assistant.
<|im_end|>
<|im_start|>user
Who won the world cup in 2018?
<|im_end|>
<|im_start|>assistant
France won the 2018 FIFA World Cup.
<|im_end|>
```

transformers 库里的 text = processor.apply_chat_template(messages, add_generation_prompt=True, return_tensors="pt") 就是作这样的转化的。
