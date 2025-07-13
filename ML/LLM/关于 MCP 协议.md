### client-server 网络连接方式

https://blog.csdn.net/2401_84494441/article/details/147457645 ：

<img width="1424" height="688" alt="image" src="https://github.com/user-attachments/assets/fada0761-0bda-4382-ad69-c71ded0b312e" />


如上，stdio 是 client 与 server 同机部署的进程间通信，其他方式才是远程调用。

官方例子 https://github.com/modelcontextprotocol/python-sdk/blob/main/examples/clients/simple-chatbot/mcp_simple_chatbot/main.py 中，就用了 stdio 方式。所以它里面才会提到启动 server 的 命令行参数：

<img width="1404" height="492" alt="image" src="https://github.com/user-attachments/assets/64cd7dde-7ee9-46ca-a625-d78c530ffe55" />

