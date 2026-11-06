对 LLM 做 agentic RL，就是带工具调用的 LLM RL。

先只考虑单个用户轮次。

没有工具调用时，是一问一答；有工具调用时，就是模型与环境来回多步：每次调用后，环境把 tool result 插回上下文，模型再接着往下走。

训练的关键是奖励放在哪里。 若每次tool call 都打分，就成了过程奖励，但调用时任务还没完成，中间步骤很难给出可靠的评价。这与一般 LLM RL 里的 PRM(Process Reward Mode) vs ORM（Outcome Reward Model) 之争中 ORM 占了主流类似，目前主流的 agentic RL 也是只对最终结果给奖励（多为规则可验证：测试、答案、环境状态）。当然, 常常还需要再叠加轨迹级的约束，如超轮数、超预算的惩罚，以及格式错误的惩罚。

agentic RL 做法：先让模型与环境交互，直到结束（自行收尾，或被轮数和预算截断），再对整条轨迹打一次分。这条轨迹

`prompt + [思考内容 + tool_call + tool_result] × N + final_response`

作为一个样本参与 RL。算 loss 时，间隔出现的 tool_result 被屏蔽，只有模型生成的 token 参与优化，但它们仍留在上下文里。

难点在于长序列：轨迹可达上千次调用、百万 token，所以要靠 partial rollout、持久的沙箱状态和长上下文训练来支撑。

多轮用户交互其实和这个很类似，只是用户这一侧也成了"环境"。真人实时参与不可行，所以真要做多轮 RL, 用户一侧需要由 LLM 模拟、脚本化的事件流，或从真实日志里选定的起点替代。这时候, 用户那一侧的内容在 loss 里被屏蔽，和 tool_result 一样.

奖励放在对话结束，还是每一轮，决定了训练粒度。

----

### 假如有一个 agent 的大量的用户真实数据, 怎么用于 agentic RL training?

这类数据用于 SFT 可以理解, 如果用于 RL, 没那么简单: 一者 RL 一般是需要当场用 training 中的model 现采样的; 如果是 GRPO 系列的 RL, 那都是要 sample N 个的(对 grpo, 铁定不能用真实数据). 

真实采集的用户数据, 也就可以用于这几种:
- (1). train reward mode, 或搞出 reward rule
- (2). 做 DPO/KTO 或者 SFT train
- (3). RL 的 task 来源
- (4). 评测集：用真实的分布和失败案例，用 trained model 来做 replay, 看看问题是否解决
