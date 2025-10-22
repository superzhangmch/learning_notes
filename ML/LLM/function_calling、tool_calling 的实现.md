大体说，每次请求LLM的时候，要把自己有的 tool 信息（tool 叫什么，干什么的，有什么参数：什么名字，什么类型，什么含义）以 json 格式传给 LLM，LLM 自主判断。

如果发现需要调用 tool，则下一步直接返回要调用哪个 tool，同时会把参数填充，这样客户端把这个信息提取出来后就可以直接调用自己的工具了。调用结束后，把结果给到 LLM， LLM 就可以返回有 tool 帮助下的结果了。

也就是分这么几步（两次 LLM 交互）：
- 用户发起带 tool 描述的请求
- LLM 返回 tool 掉用的 json
- 用户调用 tool，并再次向 LLM 发起带 tool_result 的请求
- LLM 返回最终结果

豆包的 coze.cn 上，好多操作就是直接用的 tool call / function call 来实现的额。

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

============

# 示例
```
import os
import json
import datetime
import requests 

API_KEY = "sk-XXX"
BASE_URL = "https://xxxx.com/v1/chat/completions"


# 定义函数 schema
functions = [
    {
        "name": "calculate",
        "description": "执行一个数学表达式，返回结果",
        "parameters": {
            "type": "object",
            "properties": {
                "expr": {
                    "type": "string",
                    "description": "数学表达式，例如 '3+4*2'"
                }
            },
            "required": ["expr"]
        }
    },
    {
        "name": "get_current_date_time",
        "description": "获取当前系统日期与时间（2022-02-22 01:22:33格式）。",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }
]

def calculate(expr: str):
    """执行字符串表达式，返回结果"""
    local_vars = {}
    exec(f"a = {expr}", {}, local_vars)
    print ("LLLexpr", expr, "ans", local_vars["a"])
    return local_vars["a"]

def get_current_time():
    """返回当前系统时间字符串"""
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")

def call_llm(messages):
    """发起 POST 请求"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }
    payload = {
        "model": "gpt-4.1",  # 改成你的模型名称
        "messages": messages,
        "functions": functions,
        "function_call": "auto",
    }

    resp = requests.post(BASE_URL, headers=headers, data=json.dumps(payload))
    if resp.status_code != 200:
        print("请求失败:", resp.status_code, resp.text)
        return None
    return resp.json()

def run_chat():
    messages = [{"role": "system", "content": "你是一个能计算数学表达式的助手"}]

    while True:
        user_input = input("你：").strip()
        if user_input.lower() in ("退出", "exit", "quit"):
            print("系统：再见！")
            break

        messages.append({"role": "user", "content": user_input})
        resp = call_llm(messages)
        print ("  call_llm")
        if not resp:
            continue

        message = resp["choices"][0]["message"]
        print ('  first_call_result', message)

        # 检查是否触发 function call
        if "function_call" in message:
            func_name = message["function_call"]["name"]
            args = json.loads(message["function_call"]["arguments"])
            if func_name == "calculate":
                result = calculate(args["expr"])
            elif func_name == "get_current_date_time":
                result = get_current_time()
            else:
                result = f"未知函数: {func_name}"

            messages.append({
                "role": "function",
                "name": "calculate",
                "content": str(result)
            })

            # 再发一次，把函数结果返回给模型生成自然语言回答
            final = call_llm(messages)
            print ('  call_LLM_again', final)
            if final:
                reply = final["choices"][0]["message"]["content"]
                print("助手：", reply)
        else:
            print("助手：", message.get("content"))


if __name__ == "__main__":
    run_chat()
```

执行：

``` 
你：小王去买菜，一斤白菜一块九毛二，买了二斤八两，一共多少钱
  <<  下面是 functional calling 的两次过程
  call_llm 
  first_call_result {'role': 'assistant', 'content': None, 'function_call': {'name': 'calculate', 'arguments': '{"expr":"1.92 * (2 + 8/16)"}'}, 'refusal': None, 'annotations': []}
LLLexpr 1.92 * (2 + 8/16) ans 4.8
  call_LLM_again {'id': 'chatcmpl-CTJvGFfYOxyBOkATUJhSbpaI45mbs', 'object': 'chat.completion', 'created': 1761104130, 'model': 'gpt-4.1-2025-04-14', 'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': '一斤白菜1.92元，买了二斤八两（2.8斤），总价计算如下：\n\n1.92 × 2.8 = 5.376元\n\n所以一共需要5.38元（四舍五入到分）。', 'refusal': None, 'annotations': []}, 'logprobs': None, 'finish_reason': 'stop'}], 'usage': {'prompt_tokens': 132, 'completion_tokens': 58, 'total_tokens': 190, 'prompt_tokens_details': {'cached_tokens': 0, 'audio_tokens': 0}, 'completion_tokens_details': {'reasoning_tokens': 0, 'audio_tokens': 0, 'accepted_prediction_tokens': 0, 'rejected_prediction_tokens': 0}}, 'system_fingerprint': 'fp_f99638a8d7'}
  >>
助手： 一斤白菜1.92元，买了二斤八两（2.8斤），总价计算如下：

1.92 × 2.8 = 5.376元

所以一共需要5.38元（四舍五入到分）。
```
