openclaw 允许从不同的渠道使用: 不同的聊天工具, 以及在不同的聊天群里把它拉进去, 甚至其他使用入口.

这些不同来演的消息, 经过一个网关层后, 会把消息处理成统一格式, 并根据消息来源作路由, 打向不同的 session. 而每个 session 是一个 LLM agent loop. 也就是并不是一个 openclaw instance 全局只有一个 llm loop.

这样对于每个 session 来说, 这才算是一个标准的 agent. 就 openclaw 来说, 记忆会存下来, 用的时候拼入. 怎么避免记忆内容在不同session 泄漏的?

openclaw 是周期timer + event + 定时crotab 等驱动的, 这是说代码框架层, 说的并不是每个 session. 

参考:
- https://zhuanlan.zhihu.com/p/2010385772486878215 (原始: https://ppaolo.substack.com/p/openclaw-system-architecture-overview )
