# Multi-teacher On-Policy Distillation (MOPD)

- 《MOPD: Multi-Teacher On-Policy Distillation for Capability Integration in LLM Post-Training》 小米 https://arxiv.org/abs/2606.30406
- 《MiMo-V2-Flash Technical Report》 https://arxiv.org/pdf/2601.02780, 就用到了它

一句话说: 先SFT然后以他为基础, 不同领域分别 RL, 这样得到多个领域专家, 然后再对原来的 sft model, 把这些能力蒸馏过去.

<img width="2020" height="1160" alt="image" src="https://github.com/user-attachments/assets/21c830d0-c002-4dc4-9286-1b175a4df545" />

对于stage3: student 蒸馏 teachers, 是做的KL距离逼近. 这一step, 也是通过 RL 来做的. 方法来自 《MiniLLM: On-Policy Distillation of Large Language
Models - https://arxiv.org/pdf/2306.08543》.


----

### 《miniLLM》

通过 RL 来拟合 reverse-KL, 以便做蒸馏, 来自 miniLLM 一文. 

<img width="2496" height="1828" alt="image" src="https://github.com/user-attachments/assets/42fa33ba-fad0-4331-91c6-27966289ae5a" />

上图公式编号同其 paper中编号(每个公式有所调整). 

是现有loss 然后看怎么用 RL 解. 然后通过形变, 强行构造了一个 reward = Rₜ = log p/q_θ . 而且注意reward 居然含有和策略中的参数θ. 这不算是典型的 RL 了. anyway, 对这个 loss 求导, 可以得到(2). 

推导: -∇_θ L = ∇_θ [ ∑ q_θ · log(p/q_θ) ] = ∑ [ q_θ′ · log(p/q_θ) + q_θ · (−q_θ′/q_θ) ] = ∑ [q_θ′ · (log(p/q_θ) − 1) ] == ∑ [q_θ′ · (Rₜ − 1) ] = E_q (Rₜ − 1)  ∇_θ(log q_θ).  注意 q′ = q · ∇log q.
