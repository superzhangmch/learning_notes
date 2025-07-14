
一说到 MCP，就会说它有 host、client、server 三部分。它是为了方便 LLM 以统一方式调用外部工具而设计的，那么这三者怎样关系，以及怎么和 LLM 结合起来，其实很是很扑朔迷离的。

其实 MCP 只是定义了 client 与 server 之间的网络交互协议，这部分是死的。其他部分并没严格规定，具体怎么实现无一定之规。

官网文档： https://modelcontextprotocol.io/

**简介:**
- **server**：只是对于各种后端资源做了统一接口的封装。所以 server 其实是薄薄一层。server 不会请求 LLM，当需要的时候，通过反向让 client 用 sampling 来完成（client 转发给 host 作 LLM 采样）。
- **client**：只是负责与 mcp server 的交互。它是供 host 使用的，暴露给 host 的核接口，都是怎么与 server 打交道的，所以核心接口其实就是：server 的 tool、resource、prompt 三种资源的 list，以及 get。
  - 即暴露给上游 host 的核心接口是： list_resources， list_tools， list_prompts， read_resource， call_tool。但是这些接口属于 host 天然需要的，但是它们长什么样（名字、参数等），并不是 mcp 协议的一部分。而取决于你怎么实现它。 
  - client 本身也是轻量的，不与 LLM 打交道。
- **host**：即应用本身（比如 ai 编程 IDE）。应用通过 client 提供的统一接口和 server 们打交道。
  - host 掌控 LLM，它引导用户和 host 的人机交互界面的交互，并驱使 LLM 作回答、智能选择工具等等。
  - 特别的，对于 server 提供的那些 tool、resource、prompts 资源（甚至 host 可以连好多个 clients, 好多个 servers），需要选择恰当的那些用于处理用户当前请求。这个 tool/resource/prompt selection 的工作，是 host 来做的。

<img width="728" height="516" alt="image" src="https://github.com/user-attachments/assets/4be8ca20-fa5c-4a6b-801d-556dd9f146b7" />

**代码实现，怎么做：**
- server：对于每一个 server，按照 mcp 协议实现即可。
- client：固然可以按照 mcp 协议自己实现。但是只要 server 符合 mcp 协议，实现完好的 client 一定可以支持它。所以 client 不需要重复造轮子，用别人实现好的就行——比如官网实现的：https://github.com/modelcontextprotocol/python-sdk/blob/main/src/mcp/client/session.py ，即 mcp.ClientSession。对于官网例子 https://github.com/modelcontextprotocol/python-sdk/blob/main/examples/clients/simple-chatbot/mcp_simple_chatbot/main.py 来说， 这里是在使用 mcp.ClientSession，所以严格说来，它其实是实现了一个 host，而非 client。
- host：上面提到的 https://github.com/modelcontextprotocol/python-sdk/blob/main/examples/clients/simple-chatbot/mcp_simple_chatbot/main.py 就是一个例子。通过使用 mcp.ClientSession，实现了一个具有面向用户的有实际功能的 host。

**和function calling 关系:**

function calling 和 mcp 协议本身没关系。但是 function calling 可以被 host 使用，用来选择调用 mcp.client -> mcp.server 链路提供的工具。

----

# mcp-server

## mcp server 和 LLM 的关系

MCP Server 内部通常不包含 LLM 的使用。server 是一个轻量级的接口层（对接文件系统、数据库等），而不是智能处理层。

如果 mcp server 要请求 LLM，固然可以直接请求某一个 LLM，但是按 mcp 的做法，是 server 向 client 发起 sampling 请求（LLM调用请求），让 client 把 LLM 结果返回给自己。

这样做让 server 和 LLM 调用解耦， client 可以控制 LLM 的调用：一个是 LLM api 的选择与鉴权问题，还有是可以给用户以安全性控制（human-in-the-loop)）：用户可以检查 server 的 prompt 以及 LLM 的 结果，用户觉得有问题可以阻止。

## mcp server 的 tools 功能

- https://modelcontextprotocol.io/docs/concepts/tools
- https://modelcontextprotocol.io/specification/2025-06-18/server/tools

这是最基本功能。server 需要有接口，能让 client 查询有哪些 tools（每个工具有详细描述），这样具体任务来了，上游才能知道使用哪个工具。

上游可能发现有很多 tools，怎么选择本次请求用哪一个呢？
- function calling
  - 按官网例子 https://modelcontextprotocol.io/quickstart/client ：
  - <img height="700" alt="image" src="https://github.com/user-attachments/assets/cd8eda51-1290-4e16-8445-56bb15e61224" />
- tools 描述拼到 prompt 里, 由 LLM 来选
  - 按官网例子 https://github.com/modelcontextprotocol/python-sdk/blob/main/examples/clients/simple-chatbot/mcp_simple_chatbot/main.py
  - <img height="600" alt="image" src="https://github.com/user-attachments/assets/1201bd32-90ef-47ca-9887-049da49eb2f0" />
- 如果 tools 非常多，乃至于几十上百，全部给到 LLM 就不太现实了。这时候可能就需要一个额外的工具选择步骤，把精选的几个候选工具给到 LLM
  - 比如 https://arxiv.org/pdf/2505.03275 （RAG-MCP）提供的方式，对工具建索引作检索，优选出 top-k 个。

## mcp server 的 prompts 功能

mcp server 的 tool 功能是直接执行、干 "完" 一件事，而 prompts 功能也可以说是干一件事，只是不像 tool 调用后就干完了。prompts 只是返回了怎么做——具体还需 client 拿到结果后调用下 LLM，LLM 结果才算是这次任务的执行结果。

按官网文档，prompts 应该是用户可控的，需要暴漏给用户，由用户选择执行；典型使用场景是 UI 界面上由用户触发。

- https://www.speakeasy.com/mcp/building-servers/advanced-concepts/prompts
- https://modelcontextprotocol.io/specification/2025-06-18/server/prompts
- https://modelcontextprotocol.io/docs/concepts/prompts

### （1）、client-server 的数据交互

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
**针对具体任务，请求获得响应的 LLM prompt：**
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

### （2）、prompt 选择

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

不过当前多用静态绑定的方法。

## mcp server 的 resources

server 支持 client 查询它有哪些资源（resources/list），这样client 才知道怎么用。resources 都是通过 URI 形式指定的。

上游怎么知道当前场景用哪个 resource？按 https://modelcontextprotocol.io/specification/2025-06-18/server/resources ，或者靠 UI 界面展示让用户点选，或者靠 ai 模型自动选择。

tools、prompts、resources 区别： https://www.speakeasy.com/mcp/building-servers/advanced-concepts/prompts ： 
<img width="1952" height="1102" alt="image" src="https://github.com/user-attachments/assets/0727d19a-0cb2-4827-8717-3f883e8758c2" />

----

# mcp-client

client 除了被 host 使用，还需要提供 sampling、roots、elicitation 等接口供 mcp server 调用。

### mcp client 的 sampling

client 给 server 提供了 LLM 代理访问能力。

用户的任务，下发到 server 后，如果 server 发现需要借助于 LLM，就会向 client 发起 sampling，拿到结果后，再发给用户。
 
- https://www.speakeasy.com/mcp/building-servers/advanced-concepts/sampling
- https://modelcontextprotocol.io/docs/concepts/sampling
- https://modelcontextprotocol.io/specification/2025-06-18/client/sampling

### mcp client 的 roots、elicitation

**（1）、elicitation：**

https://modelcontextprotocol.io/specification/2025-06-18/client/elicitation

在 client 调用某个 server tool 的时候，server 不知道某些信息，需要向 server 发起 elicitation 请求，以便获得这些信息。

那么，为什么 server 不在定义它的 tool 参数的时候，就把这些信息定位必须呢？这可能因为 server 内处理逻辑复杂，不方便 client 一下子把参数都提供，或者是为了安全和隐私考虑。

**（2）、roots：**

- https://modelcontextprotocol.io/specification/2025-06-18/client/roots
- https://modelcontextprotocol.io/docs/concepts/roots

roots 返回给 server 一个或多个 URI 的 base 地址（不只限于文件系统）：
```
{
  "roots": [
    {
      "uri": "file:///home/user/projects/frontend",
      "name": "Frontend Repository"
    },
    {
      "uri": "https://api.example.com/v1",
      "name": "API Endpoint"
    }
  ]
}
```

有问题是，为啥不放到 client 请求 server 的参数里，而要让 server 主动问？

按 https://modelcontextprotocol.io/specification/2025-06-18/client/roots ， Roots 定义的是 整个 Server 的工作边界，不是某个具体工具的参数, 而且一次获取就把各种类型资源的 roots 指定了。

----


**其他一些细节：**

<img width="1144" height="536" alt="image" src="https://github.com/user-attachments/assets/44226b34-18fa-458b-af99-da0fcdb93235" />

如上，建立连接后，首先要做一个“首次握手”， client 与 server 宣称自己的能力，以及协议版本(这都封装在了 py mcp.clientSession.initialize()里)。而 tools.list， prompts.list 等，并不是在 initialize 阶段完成，而是 operation 的事。

此外，协议还规定需要处理处理 notification、subscribe、分页等。比如，initialize 的时候，就宣称了可变项：
```
client：
      "roots": {
        "listChanged": true
      },
server：
      "prompts": {
        "listChanged": true
      },
      "resources": {
        "subscribe": true,
        "listChanged": true
      },
      "tools": {
        "listChanged": true
      }
```

如果中途有变或有更新，需要能通知对方，也就是能热更新。

notification 机制：当资源状态变化，实时事件推送，任务进度（method=notifications/progress），配置和环境变化等触发。特别在 initialize() 三部曲的最后一步就是一个 notification。

以上这些，都是需要 client 与 server 的实现都能支持到。

----

# client-server 网络连接方式

参： https://modelcontextprotocol.io/specification/2025-06-18/basic/transports

<img width="1174" height="408" alt="image" src="https://github.com/user-attachments/assets/44970ba2-5ed0-4a4e-8f6e-a8f9c54896a7" />

如上，stdio 是 client 与 server 同机部署的进程间通信，其他方式才是远程调用。而 SSE=Server-Sent Events，该方法是早起版本的。

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
