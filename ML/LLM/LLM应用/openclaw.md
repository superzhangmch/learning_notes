openclaw 允许从不同的渠道使用: 不同的聊天工具, 以及在不同的聊天群里把它拉进去, 甚至其他使用入口.

这些不同来演的消息, 经过一个网关层后, 会把消息处理成统一格式, 并根据消息来源作路由, 打向不同的 session. 而每个 session 是一个 LLM agent loop. 也就是并不是一个 openclaw instance 全局只有一个 llm loop.

这样对于每个 session 来说, 其实这才算是一个标准的一般意义上的 agent. 


就 openclaw 来说, 记忆会存下来, 用的时候拼入. 怎么避免记忆内容在不同session 泄漏的? 从代码看，OpenClaw 并没有做 session 级别的记忆隔离。记忆（src/memory/manager.ts）是 per-agent 的，用  agentId + workspaceDir 作为缓存 key。同一个 agent 下的所有 session 共享同一份记忆索引。这是 by design，不是泄漏——因为记忆代表的是"这个 agent 知道什么"，不是"某次对话说了什么"。真正按 session 隔离的是 transcript（对话历史）。

### agent 与 session 关系

在 openclaw 里, 同一个 Agent, 代表了同一个人格/角色. 所以记忆隔离, 其实是 agent 级别的. 同一个 agent 可以有不同 session, 每个session 可以是关于不同地方的(不同 WhatsApp 群 / 不同 Slack thread) —— 但是就像一个人可以加入不同app的不同群组.

**(1). agent = 人格/角色**

在 config 里定义的, agent 的定义大约这样:

```
agents: 
  list: 
    - id: assistant
      model: claude-sonnet-4-6 
      heartbeat: { every: 30m }
    - id: coder 
      model: claude-opus-4-6
```

一个 OpenClaw 实例可以配多个 agent。每个 agent 有自己的：
- 模型配置 
- workspace 目录（文件、HEARTBEAT.md）
- 记忆库（embeddings）
- 心跳设置

如果不配 agents.list，就只有一个默认 agent。

**(2). Session = 一次对话**

同一个 agent 可以有多个 session。session key 的生成取决于 session.scope：

```
┌────────────────────┬──────────────────────────┬───────────────────────────────────────────┐ 
│       scope        │    session key 怎么来     │                      效果                 │
├────────────────────┼──────────────────────────┼───────────────────────────────────────────┤
│ per-sender（默认）  │ agent:<agentId>:<sender> │ 张三和李四跟同一个 agent 聊，各自有独立对话历史  │
├────────────────────┼──────────────────────────┼───────────────────────────────────────────┤
│ global             │ global                   │ 所有人共享同一个对话历史                      │
└────────────────────┴──────────────────────────┴───────────────────────────────────────────┘
```

`同一个 agent` + `不同 WhatsApp 群 / 不同 Slack thread / 不同人 DM` → `不同 session`。

(3). 关系    

```
OpenClaw 实例
 └── Agent "assistant"
 │    ├── 共享: workspace 文件、记忆库、系统 prompt 配置
 │    ├── Session: 张三 WhatsApp DM   (独立 transcript, 独立 LLM loop)
 │    ├── Session: 李四 Telegram DM    (独立 transcript, 独立 LLM loop)
 │    └── Session: 某 Slack 群 thread  (独立 transcript, 独立 LLM loop) 
 └── Agent "coder" 
      ├── 共享: 自己的 workspace、记忆库
      └── Session: ...
```

所以, 请求路由到不同 session，其实是：路由先按 agent 分，再按 sender/group 分出 session。记忆共享发生在 agent 层级，对话隔离发生在 session 层级。


### 关于时间驱动,永不退出

openclaw 是周期timer + event + 定时crotab 等驱动的, 这是说代码框架层, 说的并不是每个 session. timer + event + cron 驱动的是 heartbeat runner（定期唤醒 agent 做自主检查）和 cron service（定时任务）。而每个 session 内部的 LLM loop 本身就是个同步式的 while(hasToolCalls) 循环，不涉及 timer 向驱动。用户消息进来后直接触发一次 LLM loop 跑完就结束。

参考:
- https://zhuanlan.zhihu.com/p/2010385772486878215 (原始: https://ppaolo.substack.com/p/openclaw-system-architecture-overview )
