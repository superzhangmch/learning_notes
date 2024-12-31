# system prompt 怎么和chat 记录拼一起, 形成最终的塞给 LLM 的 prompt 的？

虽然可以猜测怎么做，还是问问 LLM。

chatgpt: 
```
System Prompt: "You are a helpful assistant."
Chat History:
User: "What is the capital of France?"
Assistant: "The capital of France is Paris."
User: "And the population?"
Current Question: "What is the population of Paris?"

The combined input is sent to the LLM as a single prompt.
```

chatgpt 4o:
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
