### LLM 多轮训练怎么做的, 怎么模拟的

- 在多轮对话 RL 中，如果直接回放真实对话日志，当新模型在早期就回答正确时，原日志里后续“用户纠正”的轮次就会变得不合理；那工业界到底是如何利用真实多轮对话数据训练模型的？
- 是否主流方法其实只是固定前 n 轮历史来训练第 n+1 轮回复，而不是完整回放整段对话做 RL？


chatgpt deepresearch 报告结论是：这种问题本质上是轨迹不一致（trajectory mismatch / off-policy inconsistency），因为用户下一轮发言依赖模型上一轮回答，一旦策略改变，原日志后续用户轮次就不再成立；因此工业界通常不会整段回放真实多轮对话做 RL，而是以 step-level 训练（固定前 n 轮 → 学第 n+1 轮） 为主，必要时在偏离原日志时 截断回放或让用户模拟器接管继续生成后续轮次，并在少数任务中用 短 rollout 的多轮模拟训练，以避免不合理的“纠正轮”伪轨迹。

---

### claude 的答案:

1. What most people actually do -- **单论训(one-step RL)**

  Single-turn RLHF/GRPO — [prompt] → response → score. The most common. Simple, proven, scales well. OpenAI's original InstructGPT, most open-source RLHF work (TRL,
  OpenRLHF) all started here.

2. Conversation history as context (easy next step) -- **多轮当context, 只训单论(仍然是 one-step RL)**

Slice real production logs at turn N, feed turns 1..N-1 as prompt, train turn N:

[user₁, assis₁, user₂, assis₂, ..., userₙ] → expect assisₙ → score

Still single-response RL, but the prompt is richer. This is what most teams doing "multi-turn improvement" actually do. It's the lowest-hanging fruit this repo is missing
 — if you already have production logs, just need to slice them.

3. Simulated user (becoming common for agentic) -- **模拟用户, 真正 multi-step**

  Use another LLM to play the user role. The trained model and the simulated user have a full conversation, then score the final outcome.

  - DeepSeek, Tulu 3, and many agent-training papers use this
  - The "user simulator" can be prompted to give corrections, ask follow-ups, be adversarial, etc.
  - Reward is on the whole conversation outcome, not per-turn

  This is essentially what the Deep Research pipeline already does — except the "user" is tool APIs, not a simulated human. Extending it to a simulated human corrector
  would be straightforward architecturally.

4. Per-turn credit assignment (research frontier)

  The hard problem: if a 5-turn conversation ends badly, which turn was at fault?

  Approaches:
  - Process Reward Models (PRMs) — score each intermediate step, not just the final answer. OpenAI's "Let's Verify Step by Step" paper. Math-focused mostly.
  - Turn-level advantage estimation — like GAE in classic RL, propagate the final reward backwards with discount. Academic mostly.
  - Per-turn human preference — have annotators mark which specific turn went wrong. Expensive but high signal. Anthropic and OpenAI reportedly do this internally.

5. Correction-specific training (niche but relevant to your goal)

  Some teams specifically curate (bad_response, user_correction, improved_response) triples and:
  - SFT on the improved response given the correction context
  - Or use DPO with (correction → good_response) as chosen vs (correction → still_bad_response) as rejected
