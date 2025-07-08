大体说，每次请求LLM的时候，要把自己有的 tool 信息（tool 叫什么，干什么的，有什么参数：什么名字，什么类型，什么含义）以 json 格式传给 LLM，LLM 自主判断。

如果发现需要调用 tool，则下一步直接返回要调用哪个 tool，同时会把参数填充，这样客户端把这个信息提取出来后就可以直接调用自己的工具了。调用结束后，把结果给到 LLM， LLM 就可以返回有 tool 帮助下的结果了。

也就是分这么几步（两次 LLM 交互）：
- 用户发起带 tool 描述的请求
- LLM 返回 tool 掉用的 json
- 用户调用 tool，并再次向 LLM 发起带 tool_result 的请求
- LLM 返回最终结果

---

非常详细的实现，也就是 chatML，发现一个 qianwen 2.5 的

### qianwen-2.5 的 chatML

https://huggingface.co/peakji/qwen2.5-72b-instruct-trim/blob/main/tokenizer_config.json

```
{%- if tools %}
    {{- '<|im_start|>system
' }}
    {%- if messages[0]['role'] == 'system' %}
        {{- messages[0]['content'] }}
    {%- else %}
        {{- 'You are a helpful assistant.' }}
    {%- endif %}
    {{- "

# Tools

You may call one or more functions to assist with the user query.

You are provided with function signatures within <tools></tools> XML tags:
<tools>" }}
    {%- for tool in tools %}
        {{- "
" }}
        {{- tool | tojson }}
    {%- endfor %}
    {{- "
</tools>

For each function call, return a json object with function name and arguments within <tool_call></tool_call> XML tags:
<tool_call>
{\"name\": <function-name>, \"arguments\": <args-json-object>}
</tool_call><|im_end|>
" }}
{%- else %}
    {%- if messages[0]['role'] == 'system' %}
        {{- '<|im_start|>system
' + messages[0]['content'] + '<|im_end|>
' }}
    {%- else %}
        {{- '<|im_start|>system
You are a helpful assistant.<|im_end|>
' }}
    {%- endif %}
{%- endif %}
{%- for message in messages %}
    {%- if (message.role == "user") or (message.role == "system" and not loop.first) or (message.role == "assistant" and not message.tool_calls) %}
        {{- '<|im_start|>' + message.role + '
' + message.content + '<|im_end|>' + '
' }}
    {%- elif message.role == "assistant" %}
        {{- '<|im_start|>' + message.role }}
        {%- if message.content %}
            {{- '
' + message.content }}
        {%- endif %}
        {%- for tool_call in message.tool_calls %}
            {%- if tool_call.function is defined %}
                {%- set tool_call = tool_call.function %}
            {%- endif %}
            {{- '
<tool_call>
{"name": "' }}
            {{- tool_call.name }}
            {{- '", "arguments": ' }}
            {{- tool_call.arguments | tojson }}
            {{- '}
</tool_call>' }}
        {%- endfor %}
        {{- '<|im_end|>
' }}
    {%- elif message.role == "tool" %}
        {%- if (loop.index0 == 0) or (messages[loop.index0 - 1].role != "tool") %}
            {{- '<|im_start|>user' }}
        {%- endif %}
        {{- '
<tool_response>
' }}
        {{- message.content }}
        {{- '
</tool_response>' }}
        {%- if loop.last or (messages[loop.index0 + 1].role != "tool") %}
            {{- '<|im_end|>
' }}
        {%- endif %}
    {%- endif %}
{%- endfor %}
{%- if add_generation_prompt %}
    {{- '<|im_start|>assistant
' }}
{%- endif %}
```

一个具体实例：
```
<|im_start|>system
You are a helpful assistant.

# Tools
You may call one or more functions to assist with the user query.
You are provided with function signatures within <tools></tools> XML tags:
<tools>
{"name": "get_weather", "description": "Get current weather for a city", "parameters": {"type": "object", "properties": {"city": {"type": "string"}, "date": {"type": "string"}}}}
</tools>
For each function call, return a json object with function name and arguments within <tool_call></tool_call> XML tags:
<tool_call>
{"name": ..., "arguments": {...}}
</tool_call>
<|im_end|>
```

-----

其他实例：

### **GPT-4：**

### **当 LLM 判断应该调用某个 tool，它会直接输出符合指定格式的 JSON 调用结构体**。

以 OpenAI 的 GPT-4 tool call 实现为例，当它觉得需要调用某个工具时，会直接输出类似这样的结构：

```json
{
  "tool_calls": [
    {
      "id": "call_abc123",
      "function": {
        "name": "get_weather",
        "arguments": "{ \"location\": \"Beijing\" }"
      },
      "type": "function"
    }
  ]
}
```

这个结构并不会由开发者手动写，而是模型自动生成的。
 
### 🔄 **调用流程简要描述：**

1. **定义工具（functions/tools）**
   在调用前，开发者需要预先向 LLM 提供一组 tools 的定义，包括名称、参数、参数类型（通常是 JSON Schema），以及简要描述。像这样：

   ```json
   {
     "name": "get_weather",
     "description": "Get the current weather of a city",
     "parameters": {
       "type": "object",
       "properties": {
         "location": {
           "type": "string",
           "description": "City name"
         }
       },
       "required": ["location"]
     }
   }
   ```

2. **模型输出调用结构**
   一旦模型在上下文中判断应该调用某工具，它会直接输出上述 JSON 调用结构，而不是普通的文本回答。

3. **由调用器执行工具**
   收到调用结构后，外部程序（比如 API 客户端）会解析这个 JSON，去执行对应的函数或 API。

4. **再把结果传回模型**
   工具执行完成后，将返回的结果（也通常是 JSON）重新传给 LLM，由它生成最终的自然语言回答。
 

### 举例说明

**用户输入：**

> What's the weather like in Tokyo today?

**模型输出（tool call）：**

```json
{
  "tool_calls": [
    {
      "id": "call_001",
      "function": {
        "name": "get_weather",
        "arguments": "{ \"location\": \"Tokyo\" }"
      },
      "type": "function"
    }
  ]
}
```

**外部调用 tool 并获取结果，返回模型：**

这一步给到 LLM 的时候，一般会令 role = tool：

```json
{
  "tool_responses": [
    {
      "tool_call_id": "call_001",
      "output": {
        "location": "Tokyo",
        "temperature": "30°C",
        "condition": "Sunny"
      }
    }
  ]
}
```

**模型再输出自然语言：**

> The weather in Tokyo today is sunny with a temperature of 30°C.

----

### **claude：**

https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/overview#single-tool-example

可以看到对于 claude 来说：第3步没按 role=tool 处理，而是 仍然是 role=user

![image](https://github.com/user-attachments/assets/f86bec6c-fcc3-4800-8ef4-5dd234f0f1ee)

----

### 

再看这里： https://medium.com/@developer.yasir.pk/tool-calling-for-llms-a-detailed-tutorial-a2b4d78633e2

![image](https://github.com/user-attachments/assets/c3cbcb9f-09e2-4e95-b075-2a06e6fa5b16)

--- 
