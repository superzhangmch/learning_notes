![image](https://github.com/user-attachments/assets/51282531-5e7b-45e4-9dc7-6be61cbbbb3c)

单条数据的 G 个不同采样，决定出一个平均 reward。然后可以用它来得到G个采样各自的 advantage。critic model 计算出的 advantage, 也不过是作为 baseline 能提供平均值的估计; 既然多次采样能算出平均值, 就不用 critic model 好了——于是 grpo 省略了 critic model(或者说 value model).

注意区别: 
- PPO 的 critic model 的 output 是token-wise 的, 不同 token 不同取值(reward 引入 KL, 导致 reward 是 token-wise 的, 然后导致 value-func 是 token-wise 的)
- GRPO 用多次采样的 reward 平均值, 则不再是 token-wise, 而是这一组采样生成的样本, 都用这一个 avg reward.

![image](https://github.com/user-attachments/assets/919ffe18-2d26-4242-9a4e-081c1860891f)

如上 V(..) 就是 value func, 由value model(或者说 critic model)产生.

GRPO 中把 KL 项独立了出来，就不能通过蒙特卡洛采样来算了（否则只用 log(../..) 一项就行了）。但是有它的 unbiased estimator 估计，拿它来算即可。

**GRPO 为啥提取 KL 项出来** 

paper 原文说在于使得 advantage Â_{i,t} 更好计算:
> instead of adding KL penalty in the reward, GRPO regularizes by directly adding the KL divergence between the trained policy and the reference policy to the loss, avoiding complicating the calculation of Â_{i,t}

假如不这样则需要这样: R'_i := r_i − β·KL_i，Â_i := (R'_i − mean({R'_1, .., R'_G})) / std({R'_1, .., R'_G}). 注意这样和paper的把KL提出来之间, 并不是严格数学等价的.

**one-step RL, 还是 per token per step RL?**

PPO 是 per token per step RL 的. GRPO 和 PPO 有区别, 严格来说仍然是 per token per step RL 的. 
- PPO 有 critic 给每个前缀估一个 V(s_t)——这是 KL 项进 reward 导致的，同一条样本的不同位置会拿到不同的优势.
- GRPO 没有 critic，基线是只以 prompt 为条件的组均值，所以每个前缀拿到的都是同一个数。grpo 的 G个采样中的一条样本只有一个奖励 r_i，它的 output 的所有 token 位置共用同一个值，优势也一样：Â_{i,t} = (r_i − mean(r)) / std(r)，对所有 t 都相同(i 是第几条样本、t 是第几个 token)。所以同一条样本 i 的各个位置 t 共用一个 Â_i。
  - 还保留了两处逐 token 的东西(功劳分配按单步，信任域按 token)：
    - ratio 和 clip 是逐 token 算的：每个 token 都有自己的 π_θ/π_old 和裁剪判定。
    - KL 也是逐 token 算的：放在 loss 里，每个位置单独约束。
    - 不看正则项, grpo 可以看作是最后一个 token step 才拿到 reward 的多step RL.

![image](https://github.com/user-attachments/assets/5dfd14e7-faae-438c-99b4-ad97b3122cd7)

