## paper 《Kimi-VL Technical Report》 https://arxiv.org/abs/2504.07491》 -- 2025

乃一只激活 2.8B 参数的 MOE VL thinking 模型。

![image](https://github.com/user-attachments/assets/25597b0f-df89-471f-ad51-4d25de90f94c)

### vision encoder 
支持**任意**分辨率的图片与视频。所用 vision encoder 为 ViT 结构，从已有的 SigLIP-SO-400M 预训练 model 上扩展来的（用它初始化参数并继续 pretrain）。原 SigLIP 没用 2D rope 位置编码而是用了绝对位置编码，为此 kimi 把它插值化，从而能支持可变的图片分辨率。另外，还补充了 2D rope 位置编码。所以一共用了两种位置编码。
   
![image](https://github.com/user-attachments/assets/02d2d8cc-8ae9-4e8d-9b19-49bd5f3ab149)

### 主体 model 部分
1. 用了 MOE。代码上就是引用到了 deepseekV3, 所以就是 deepseek 版本的 MOE。
2. 图文二模态的关联，自从 llava 之后都用 MLP，它也不例外。
3. 图文二模态并存，位置编码怎么处理的：没有给 vision 模态 token 特别设计位置编码（这和 qianwen2-vl 是不同的），是当做 text token 一样处理的。vision token 的行列位置关系，靠 vision encoder 编码到 token emb 里。

### 所用强化学习
和 《Mkimi k1.5》中方法简直一模一样。
