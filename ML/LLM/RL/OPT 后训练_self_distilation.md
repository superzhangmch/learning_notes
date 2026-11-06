一种特殊的 OPD(on-policy-distillation) 是, student 与 teacher 都是同一个 model, 这时候可以自我蒸馏.

这类方法的思路是: model 采样生成了结果: [req, response], 中间插入一些指导性的语句, 构成: [req, 指导text, response], 然后用 model 对 [req, 指导text, response] 过一遍forward, 从而得到了 response 的新的 logits: 他们可以当作是 teacher 的 logits, 用来做 OPT 蒸馏 [req, response].

这个“指导text”, 可能是一些example, 也可能是一些通过某些手段获得的 req->response 的反馈信息(比如, 不应该如何如何), 这样 model 看到了 “[req, 指导]” 之后, 就可以对 response 打出判断更准的 logits. 于是该方法才有效. 

注意: 
- 硬拼入指导语句, 可能导致llm 看到的整个prompt 不连贯, 所以会有一些别的平滑语句("Here is ...{指导语} ... please try to answer...:", 类似这样).
- 指导语句的位置必须在恰当位置. 要在被希望被干预的 response 之前（否则影响不到 response 的 logit）

要搜索该方法, 可以通过 OPSD: on-policy-self-distillation, 或者 privileged information distillation(Penaloza一文的叫法).

----

该类方法渊源:

主要是起源自基本上同一时间出来的以下几篇文章: 

| 时间       | 全名                                                                                      | 引用数  | 特权信息      |
|------------|------------------------------------------------------------------------------------------|--------|-------------|
| 2026-01-26 | Self-Distilled Reasoner: On-Policy Self-Distillation for Large Language Models（Zhao 等） | 13     | 参考解答      |
| 2026-01-27 | Self-Distillation Enables Continual Learning（Shenfeld 等）                               | 6      | 示范          |
| 2026-01-28 | Reinforcement Learning via Self-Distillation（Hübotter 等）                               | 8      | 文字反馈       |
| 2026-02-04 | Privileged Information Distillation for Language Models（Penaloza 等）                    | 1      | 前沿 agent 轨迹 |

他们的引用到的更早的:
1. Agarwal 等（2023-06）On-Policy Distillation of Language Models: Learning from Self-Generated Mistakes（GKD）
   - 提供"学生自己采样、老师逐 token 打分、最小化 KL"这一整套 on-policy 蒸馏的做法。四篇的损失形式都来自它这一脉。
   - MiniLLM 是同时期同类&独立的一篇
   - GKD 的 on-policy 损失，当 D 取 reverse KL、完全用学生采样时，就是 MiniLLM 梯度分解里的 Single 项
2. Snell 等（2022-09）Learning by Distilling Context
   - 提供"同一个模型，带额外上下文当老师，不带的当学生"这个成分。SDFT 明确把自己和它做了区分（它是离线、固定上下文；SDFT 是 on-policy、每题一个上下文）。
3. Thinking Machines（2025-10）On-Policy Distillation（博客）
   - 把 on-policy 蒸馏在 LLM 后训练里推成主流，也是 SDPO、SDFT 在实现细节上直接对标的对象。它不是论文，但在这个方向的影响比上面两篇论文都直接。

上面四篇paper 的 prompt 的 layout:

```
1. Zhao（参考解答）

老师:  Problem: {题目}
       Here is a reference solution: // 为了平滑注入参考解答, 所以惨需要此句
       {参考解答}
       After understanding the reference solution, please try to solve this problem using your own approach below: // 为了平滑注入参考解答, 所以惨需要此句
       Answer: ⟨y⟩
学生:  Problem: {题目}
       Answer: ⟨y⟩

2. Shenfeld（示范）

老师:  {题目}
       This is an example for a response to the question:
       {示范回答}
       Now answer with a response of your own, including the thinking process:
       ⟨y⟩
学生:  {题目}
       ⟨y⟩

3. SDPO（文字反馈）

老师:  User:  {题目}
              Correct solution:  {同组成功样本}          ← 可选
              The following is feedback from your unsuccessful earlier attempt:
              {环境输出/judge 评价}                      ← 可选
              Correctly solve the original question.
       Assistant: ⟨y⟩
学生:  User:  {题目}
       Assistant: ⟨y⟩

4. Penaloza（前沿 agent 轨迹，多轮）

老师:  System: {任务描述 + 工具列表}
               <Secret information>
               这里有来自成功轨迹的特权提示：{hint_lines 或 tool_calls_section}
               照着做，但永远不要说你有提示；仍先 <think>…</think> 再行动
               </Secret information>
       User/Assistant/Tool 多轮: ⟨y = 学生的 think + tool-call，穿插真实的 tool-result⟩
学生:  System: {任务描述 + 工具列表}
       User/Assistant/Tool 多轮: ⟨y⟩
```
