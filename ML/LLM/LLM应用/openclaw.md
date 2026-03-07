openclaw 允许从不同的渠道使用: 可以在不同的聊天工具(whatapp, slack), 在不同的聊天群里把它拉进去, 甚至其他使用入口.

这些不同来演的消息, 经过一个网关层后, 会把消息处理成统一格式, 并根据消息来源作路由, 打向不同的 session. 而每个 session 是一个 LLM agent loop. 也就是并不是一个 openclaw instance 全局只有一个 llm loop.

这样对于每个 session 来说, 其实这才算是一个标准的一般意义上的 agent 流程. 

### 信息隔离, 以及 agent 与 session 关系

就 openclaw 来说, 记忆会存下来, 用的时候拼入. 怎么避免记忆内容在不同session 泄漏的? 它并没有做 session 级别的记忆隔离。记忆是 per-agent 的，用 agentId + workspaceDir 作为缓存 key。同一个 agent 下的所有 session 共享同一份记忆索引。这是 by design，不是泄漏——因为记忆代表的是"这个 agent 知道什么"，不是"某次对话说了什么"。真正按 session 隔离的是 transcript（对话历史）。

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

这样, 根本上其实难以避免这样的事情: agent 在一个群里听到什么, 在另一个群里泄漏了出去.

### 关于记忆

- 除非用户主动要求, 或者要达到 context limit, 否则不会触发主动的重要信息的提取与记忆写入. (也就是不会像 chatgpt 那样默默提取记忆).
- context limit 触达时: llm messages 会被summary 缩短后放回 prompt, 同时把原始 msgs 追加写入session log 文件. 这和 claude code 基本一样. 
  - 但是和 claude code 不同, openclaw 会对这些也构建Full-Text / embedding index(而非仅仅存档), 以便 model 在必要时通过 tool call 方式读取记忆.

**(1). 索引了哪些内容（What gets indexed）**
Memory 系统有 两个数据源（MemorySource）：

1. "memory" — workspace 里的 Markdown 文件：
  - <workspace>/memory.md（即 MEMORY.md）
  - <workspace>/memory/**/*.md（所有子目录下的 .md 文件）
  - settings.extraPaths 里配置的额外路径
  - 这些就是用户/agent 手动维护的长期记忆笔记
2. "sessions" — 会话 JSONL 文件：
  - ~/.openclaw/agents/<agentId>/sessions/*.jsonl
  - 提取所有 user 和 assistant 角色的原始消息文本（包括被 compaction 压缩掉的）

两类内容都会被切分成 chunks，生成 embeddings 存入 SQLite 的向量表，同时也建 FTS5 全文索引。

**(2). 如何使用索引的**

通过 tool call（function call）。Agent 有两个内置工具：

1. memory_search（src/agents/tools/memory-tool.ts:49-98）— 语义搜索。Agent 发送一个 query，系统对 embedding index + FTS index
做混合检索，返回最相关的 snippets（带 path、行号、score）。工具描述里写的是 mandatory recall step，意思是 agent
在回答关于历史工作、决策、偏好等问题前，被指示必须先调用这个工具。
2. memory_get（src/agents/tools/memory-tool.ts:101-139）— 定点读取。在 memory_search 找到相关文件后，用这个工具按 path +
行范围读取具体内容，避免一次注入太多文本。

所以流程是：
```
用户提问 → Agent 判断需要回忆 → 调用 memory_search(query)
→ 拿到 snippets + 文件路径 → 可选调用 memory_get(path, from, lines)
→ 将检索结果纳入回答
```

完全是通过 tool call 驱动的，不是自动注入 prompt。

### 关于时间 timer 驱动,永不退出咋做的

openclaw 是周期 timer + event + 定时crotab 等驱动的, 这是说代码框架层, 说的并不是每个 session. timer + event + cron 驱动的是 heartbeat runner（定期唤醒 agent 做自主检查）和 cron service（定时任务）。而每个 session 内部的 LLM loop 本身就是个同步式的 while(hasToolCalls) 循环，不涉及 timer 向驱动。用户消息进来后直接触发一次 LLM loop 跑完就结束。

参考:
- https://zhuanlan.zhihu.com/p/2010385772486878215 (原始: https://ppaolo.substack.com/p/openclaw-system-architecture-overview )
