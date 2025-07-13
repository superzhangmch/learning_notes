一说到 MCP，就会说它有 host、client、server 三部分。其实它只是定义了 client 与 server 之间的交互协议，这部分是死的。其他部分并没严格规定，具体怎么实现无一定之规。

----

# mcp-server

## mcp server 和 LLM 的关系

MCP Server 内部通常不包含 LLM 的使用。server 是一个轻量级的接口层（对接文件系统、数据库等），而不是智能处理层。

## mcp server 的 prompts 接口

对于上游来说，server 就是具体的 tools。既然是工具，就有工具怎么更好使用的问题。所以 prompt 接口返回的 LLM prompt，是用来指示 LLM 怎么用好 server 提供的工具的。

LLM 使用工具时，需要经过多个工具中选择最优这一步。server.prompts 并不是作为额外的 prompt 用来指导某一环节的工具选择。而是针对一个具体的任务，它提供给了 LLM 解决这个任务的最佳执行指南与执行路径，LLM根据这个指示来拆解任务，决定怎么使用server 提供的工具集。

### （1）、数据交互

**client 询问 server 有哪些 prompt 可使用：**
- client 请求： client发起 method=`prompts/list` 的请求。
- server 返回：
```
prompts_arr = [
      {
        "name": "code_review",
        "title": "Request Code Review",
        "description": "Asks the LLM to analyze code quality and suggest improvements",
        "arguments": [
          {
            "name": "code", # client 发起 "method=prompts/get, name=code_review" 的请求时，需要填充的参数
            "description": "The code to review",
            "required": true
          },
          {...}, ...其他 prompt 参数 (若有）..., {...}
        ]
      },
      {...}, ... 其他 prompts ..., {...},
]
```
**针对具体任务，请求获得具体的 LLM prompt：**
- client 请求： client发起 method=`prompts/get` 的请求。承上例子，要提供 `name=code_review`， 并提供参数: `param.code=具体的一段代码`。提供的参数用于让 server 拼出恰当的 prompt。
  - 为啥 client 知道在这个场景下正好该请求 prompt_get 获得某个name=xx 的具体 prompt，而非其他？这个属于决策选择问题，下面讲。
- server 返回：可以供 LLM 用 role=user 使用的一段 prompt: `Please review this Python code:\n{{code}}"`， code=请求时提供的代码
  - 根据 https://modelcontextprotocol.io/specification/2025-06-18/server/prompts ， https://modelcontextprotocol.io/docs/concepts/prompts ，可以 role=assistant，且content 可以不只是 text，甚至可以是 既有 user又有assistant(即一个聊天的片段)：
    ```
    [
      {
        role: "user",
        content: {
          type: "text",
          text: `Here's an error I'm seeing: ${error}`,
        },
      },
      {
        role: "assistant",
        content: {
          type: "text",
          text: "I'll help analyze this error. What have you tried so far?",
        },
      },
      {
        role: "user",
        content: {
          type: "text",
          text: "I've tried restarting the service, but the error persists.",
        },
      },
    ];
    ```

<img width="2698" height="1496" alt="image" src="https://github.com/user-attachments/assets/cfe409f0-55e5-42ae-96af-03237ba90687" />

（上面例见 https://modelcontextprotocol.io/specification/2025-06-18/server/prompts ）

### （2）、具体任务的 prompt 选择问题

server 的 prompts 使用的流程为：
- Discovery 阶段：Client 通过 prompts/list 获取所有可用的 prompts
- Selection 阶段：根据用户需求或程序逻辑选择合适的 prompt
- Execution 阶段：调用选定的 prompt 并传入必要参数
- Response 处理：处理 LLM 返回的结果

那么在 selection 阶段，为啥 client 知道在这个场景下该调用 prompt_get 获得某个 name=xx 的具体 prompt，而不是获取另一个 name=yy 的，甚至为什么不是去调用某个 tool？

可以有两种方式来决定：
- 提前静态绑定
  - 比如用户界面上有相应的按钮或者选项，已经提前绑定死了就是 code_review。用户一旦点旋它，必然打向 `method=prompts/get with name=code_review`
  - 或者比如根据一定上下文智能选择，这时候跟踪了任务状态，知道这时候是在 code_review 场景，当然只能打向它。
- 动态选定：让 LLM 根据用户需求动态选择合适的 prompt。
  - 比如用户说“帮我分析这段代码的质量”， 就像工具的动态选择一样，由 LLM 自动选择 prompt.name = code_review.

不多当前多用静态绑定的方法。

----

# client-server 网络连接方式

<img width="1174" height="408" alt="image" src="https://github.com/user-attachments/assets/44970ba2-5ed0-4a4e-8f6e-a8f9c54896a7" />

如上，stdio 是 client 与 server 同机部署的进程间通信，其他方式才是远程调用。而 SSE=Server-Sent Events，该方法要被淘汰。

### **1. stdio：**

官方例子 https://github.com/modelcontextprotocol/python-sdk/blob/main/examples/clients/simple-chatbot/mcp_simple_chatbot/main.py 中，就用了 stdio 方式。所以它里面才会提到启动 server 的 命令行参数：

<img width="1404" height="492" alt="image" src="https://github.com/user-attachments/assets/64cd7dde-7ee9-46ca-a625-d78c530ffe55" />

### **2. SSE:**

就是异步请求模式，client 向 server 发送请求后，不能同步拿到结果。（要同步，只能弄成伪同步）

```
// 1. 通过 HTTP POST 发送请求
const response = await fetch('/mcp/request', {
  method: 'POST',
  body: JSON.stringify({
    jsonrpc: "2.0",
    method: "tools/call",
    params: { name: "search" },
    id: 123  // 关键：请求ID
  })
});

// 1. 建立 SSE 连接, 从另一个地址接收响应
const eventSource = new EventSource('/mcp/events');

eventSource.onmessage = function(event) { // 处理回调
  const mcpResponse = JSON.parse(event.data);
  if (mcpResponse.id === 123) {  // 通过ID匹配请求
    console.log('收到响应:', mcpResponse.result);
  }
};
```

### **3. streaming HTTP：**

Streaming HTTP ，其实就是短连接的同步请求模式。结果是流式拿到的。

```
// 客户端发送请求
const response = await fetch('/mcp/tools/call', {
  method: 'POST',
  headers: {
    'Accept': 'text/plain', // 或 application/json-stream
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    jsonrpc: "2.0",
    method: "tools/call",
    params: { name: "search", arguments: { query: "hello" } },
    id: 123
  })
});

// 服务器返回流式响应: 同步等待结果
const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  const chunk = decoder.decode(value);
  console.log('收到数据块:', chunk);
}
```
