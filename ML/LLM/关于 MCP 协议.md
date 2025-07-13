
----

### client-server 网络连接方式

<img width="1174" height="408" alt="image" src="https://github.com/user-attachments/assets/44970ba2-5ed0-4a4e-8f6e-a8f9c54896a7" />

如上，stdio 是 client 与 server 同机部署的进程间通信，其他方式才是远程调用。而 SSE=Server-Sent Events。

#### **1. stdio：**

官方例子 https://github.com/modelcontextprotocol/python-sdk/blob/main/examples/clients/simple-chatbot/mcp_simple_chatbot/main.py 中，就用了 stdio 方式。所以它里面才会提到启动 server 的 命令行参数：

<img width="1404" height="492" alt="image" src="https://github.com/user-attachments/assets/64cd7dde-7ee9-46ca-a625-d78c530ffe55" />

#### **2. SSE:**

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

#### **3. streaming HTTP：**

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
