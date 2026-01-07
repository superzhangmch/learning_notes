1. 根目录下的 CLAUDE.md 一定自动加载, 其他目录的, 在访问相关目录的时候, 才加载. 相关命令 "/memory"
2. plan mode: 可以在prompt 中,让他启用
3. subagent: Subagent 运行时是阻塞的（blocking），在 subagent中运行时, 用户无法与 Claude Code 主循环交互。 用 "/agents" 命令管理 subagent
4. 假如是做web 开发, 怎么和浏览器交互:
   - claude code 自己回答:  `MCP Server with Browser Control; You can use an MCP (Model Context Protocol) server that gives Claude Code direct browser access. Here's how:; Playwright MCP Server - The most mature option:`
   - zhihu 文章: https://zhuanlan.zhihu.com/p/1991676530150110556
   - 基于playwright: https://zhuanlan.zhihu.com/p/1979830200477976445


### claude code 解读
- https://zhuanlan.zhihu.com/p/1961002540868024184

### 关于 TodoWrite tool

- 它用来跟踪复杂task 的分步执行
- 步骤拆解是 LLM 做的, 该 tool 只是记录下.
  - 假设一开始拆解为任务 [a, b, c, d], 在执行过程中, 有可能调整为 [a, b, new_step, c, d]. 也就是说, 这个步骤, 只有已经执行完的是确定不变的, 未执行的: 无论step num, 还是content 都可能变.
- 为什么要用它:
  - 显式地把步骤列出来,放进 context, 时时提醒 LLM
  - tool 本身则是把这个步骤传给 UI,让 UI 统一格式地渲染(而不是作为 llm output 一部分, 淹没在它的回复里, 且这样做输出格式也难以统一)
