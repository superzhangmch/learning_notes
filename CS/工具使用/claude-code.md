1. 根目录下的 CLAUDE.md 一定自动加载, 其他目录的, 在访问相关目录的时候, 才加载. 相关命令 "/memory"
2. plan mode: 可以在prompt 中,让他启用
3. subagent: Subagent 运行时是阻塞的（blocking），在 subagent中运行时, 用户无法与 Claude Code 主循环交互。 用 "/agents" 命令管理 subagent
4. 假如是做web 开发, 怎么和浏览器交互:
   - claude code 自己回答:  `MCP Server with Browser Control; You can use an MCP (Model Context Protocol) server that gives Claude Code direct browser access. Here's how:; Playwright MCP Server - The most mature option:`
   - zhihu 文章: https://zhuanlan.zhihu.com/p/1991676530150110556

