MOR：《Mixture-of-Recursions: Learning Dynamic Recursive Depths for Adaptive Token-Level Computation》 https://arxiv.org/pdf/2507.10524

<img width="1584" height="954" alt="image" src="https://github.com/user-attachments/assets/718ff2a4-776e-4c6e-8eec-31849b364b56" />

如图，model 结构为：第一层，最后一层不走循环，其他中间层分成多个 block，每个 block 循环 N 次——每个 token 根据 router 的决定，走其中的前几个。

而 router，有两种方式：

