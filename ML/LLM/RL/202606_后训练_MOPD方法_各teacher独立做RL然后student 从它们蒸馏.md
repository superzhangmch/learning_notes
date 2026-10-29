# Multi-teacher On-Policy Distillation (MOPD)

- 《MOPD: Multi-Teacher On-Policy Distillation for Capability Integration in LLM Post-Training》 小米 https://arxiv.org/abs/2606.30406
- 《MiMo-V2-Flash Technical Report》 https://arxiv.org/pdf/2601.02780, 就用到了它

一句话说: 先SFT然后以他为基础, 不同领域分别 RL, 这样得到多个领域专家, 然后再对原来的 sft model, 把这些能力蒸馏过去.

<img width="2020" height="1160" alt="image" src="https://github.com/user-attachments/assets/21c830d0-c002-4dc4-9286-1b175a4df545" />

对于stage3: student 蒸馏 teachers, 是做的KL距离逼近. 这一step, 也是通过 RL 来做的. 方法来自 《MiniLLM: On-Policy Distillation of Large Language
Models - https://arxiv.org/pdf/2306.08543》.


