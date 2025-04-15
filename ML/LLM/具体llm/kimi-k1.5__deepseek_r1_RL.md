openai o1出来后，表现强劲，大家猜测用了什么 PRM、MCTS 吗？无论它用了什么技术，deepseek-r1、kimi k1.5 的出现，证明了直截了当地直接用 RL 优化 long-COT（chain-of-thoughts） 就可以达到同样的效果。

# kimi-k1.5

kimi-k1.5 在 pretrain 后，仍然做了普通的 SFT，然后开启强化学习。不过在开启 RL 之前，它先构造 long-COT 数据，做了 long-cot SFT，然后才 RL。

## long-cot SFT

先构造拟覆盖的 problem set，然后用 prompt engineering 生成含有 long-COT 的数据。最终数据集应该像人思考一样包括：planing(先规划再做事），evaluation（评价做的对不对），reflection(反思刚才思路），exploration（如果反思刚才有问题，那么应该探索新思路）。

problem set：涵盖的领域要光，各种难度的题目都要有，结果可以简单清晰判答案读错，不能不经思考直接猜出答案。每一点，都是尽量用自动化的方式来处理。

## RL

#### 范式转变：tree search => long-COT

之前的方法是按 planning algorithm 思路来做：把思考分成多个step，用 tree search 的方式来做——每个step当一个节点，往树枝方向伸展作探索，如果路不通则回退找新方向，直至找到最终答案。

![image](https://github.com/user-attachments/assets/de545268-c8bf-4c6c-9e75-cb64ff7ebcc9)

这个 tree search 的求解过程，其实可以展开拍平(flatten)成序贯的一条线的。然后可以把这个一条线的序贯思考过程用 text 表示——这就是 long-COT 了——直接用 RL 来探索好了。

![image](https://github.com/user-attachments/assets/ae9d0bb9-3c90-47bc-8928-4a8a77f1065d)

也就是说，RL 只要保证能得出正确答案就行了，至于中间过程如何，它自由探索好了。这迥异于 tree search 那样的方式。

下面是它的 RL 的一些细节。

#### RL 算法本身
long-COT 需要作各种探索，歧途步骤不见得不好。于是抛弃了每个 token 位置都需算一次的 value model——否则会打压误入歧途的探索。整体上就是把整个生成过程当做一个 RL step。它还不需要 sft reference model 作 KL 计算。所以可以说比 GRPO 还简单。

#### 题目的采样策略
每次迭代，选择训哪些题目呢？整个训练过程中，先训简单的题目，慢慢增加难度。题目本身有难度值，可以按此调整采样比例。训练时要跟踪每个题目的正确率，从而动态调整采样概率。

### RL reward 设计
1. 编程类题目：用自动化生成获得的 test case，在 sandbox 环境中测试 rollout 出的代码是否符合要求，从而赋予reward。
2. 数学题：有些题目不能靠字符串比较来判断正误【比如 sqrt(2) vs 2^(1/2)】。对复杂情形，固然可以训练 model 作 0-1 来判断解答是否正确，但是作者发现用一个 COT model 来判断正误更合适（先来一段分析，最后给出判断）。
3. 长度惩罚：有时有过度思考问题，即输出的思维太长。于是对能做对的题，惩罚长输出，奖励短输出；对做错的题，惩罚长输出；并融入 reward。不过训练早期这样做会减缓训练，于是逐步 warm up。

#### 多模（vision）数据
既要用真实世界数据，也用了合成数据。另外，为了保证 vision 能与 text 能力持平，把一些 text 题目 print 到图片，然后训（model 应该训得：见图如见文）。

#### 往 short-COT 迁移（long2short）
1. 未经long-COT RL 的model，与经此过程的model，直接做参数 average。
2. 蒸馏：从 long_COT RL model, 采样出结果正确但是输出短（多次采样选最短）的数据后，作 SFT 或者做 DPO。
3. 对业已训好的 long_COT RL model，在做作一轮 RL，但是要对“长度惩罚”做强化，强力缩短输出长度。

## RL 底层实现

![image](https://github.com/user-attachments/assets/fae59a87-1149-4904-b665-2fbae6f39f95)

如图，先 rollout（即完整 trajectory 的采样），结束后 train，如是往复。如果有某个 prompt 正巧 rollout 的输出过长，那么就会导致 rollout 阶段时间太长，整体训练效率太低。partial rollout 正是为了解决这个问题。强制一轮 rollout时间只能有那么长，时间到就强制切走。下一次rollout 时间到了，把刚才没做完的继续做。如此而已。只是 rollout 到一半的不能用于训练，需要等待最终 rollout 结束。鉴于时 on-policy training, rollout 出的结果要很快用于训练，对于 partial rollout的结果，可能会前半段是老策略生成的，后半段是新策略生成的，这是有问题的，于是算loss的时候，会用 mask 把前面段mask掉（During training, certain segments can be excluded from loss computation to further optimize the learning process, making the entire system both efficient and scalable.）。

![image](https://github.com/user-attachments/assets/29e2186e-97e9-4d04-a6c5-bc01378db35f)
（RDMA：直接存储访问）

training 与 rollout 是共存的。作training的时候，需要把 rollout 杀掉。作rollout的时候， training 需要作 offload（转化速度： training->rollout, 一分钟内，反向：10秒）。为了加速采样，用的 vllm。

----

# deepseek-R1

deepseek-R1-zero 更激进一步，证明了 pretrain 后，不经任何 SFT，直接做 RL，所得到的 model 虽然有多个问题，但是在数学难题上，是真的做的出来，得分还很高。

![image](https://github.com/user-attachments/assets/3201dd41-cc0c-4ddb-8126-4336f7b542fd)

当然实用化的 R1，仍然是先做 SFT，再 RL。《deepseek-R1》paper 中对于细节没有《kimi-k1.5》那么细，但就大体而言，两者可以说一模一样。

### RL 算法
所用的 GRPO，从本质上和 PPO，乃至 kimi-k1.5 的 RL 算法，无本质区别。略过不提。

### reward
reward 完全靠规则（是否做对，以及格式是否正确），没用任何 reward model。

![image](https://github.com/user-attachments/assets/f0d92d5a-bf17-4742-a835-96b24623df93)

### rollout 采样的 prompt 模版

![image](https://github.com/user-attachments/assets/136d7747-9865-46e9-8cc9-03933ff0588a)

再用以上 prompt template 对每个问题采样，就可以驱动 R1-zero 的训练 run 起来了。不过这样打造的 R1-zero，强则强矣，有几个问题：（1）思考过程可读性差（2）多语言混合（3）huggingface 某处看到还有一个问题时，容易有repeat 复读机问题。

### R1 打造四部曲
1. 给 RL 一个好的起点：首先做一次 long-COT SFT。数据收集方式是：用 few-shot prompting 生成 long COT，从 R1-zero生成的结果里挑选一些符合要求的数据（加上人工后处理）。
2. RL:这一步和 R1-zero 一样，这是额外加了语言一致性 reward。
3. 补充非推理能力(写作、QA、翻译等)：接下来收集了 60万 COT 数据（从上一阶段model采样并选出），20 万普通数据（复用打造deepseekV3的sft数据， 但是要适当用model生成 COT），作 SFT。
4. 偏好对齐：接下来做了有用性与无害性的 RL(推理类数据仍用规则 reward，非推理类引入偏好 reward model)。helpfulness: 只看最后 summary 部分；harmlessness: 审查整个输出（包括 reasoning 过程）

### 能力迁移到小模型
用前述第3步的80万数据对小模型作 SFT。
