# 共识算法 paxos、 raft

它不关心怎么保证分布式的 a=a+1 这类操作的事务性、原子性。而是关心分布式下怎么共识地执行一系列操作，保证最终每个分布式实例都执行了相同的命令序列。

它天然适合做的一个事就是分布式的配置同步。从原始配置开始，每个实例都做了相同的序列更改，所以配置总是保持一致。

另一个场景是分布式系统选举 leader，保证选出的是大家都公认的leader。

chatgpt 给出的对 mysql 集群，paxos 可以用来保证什么：

- 配置复制:在分布式MySQL系统中，Paxos可以用于配置管理，确保所有节点都有一致的配置信息。例如，当增加或移除数据库节点时，Paxos算法可以保证这些变更在所有节点间一致地应用。
- 写操作的一致性:对于写操作，可以使用Paxos算法来保证跨节点的一致性。每个写操作都通过Paxos算法来协调，确保只有当大多数节点同意时，操作才会被提交。
- 分布式事务:Paxos也可以用来实现分布式事务的一致性提交。通过在事务提交阶段使用Paxos，可以保证事务要么在所有相关节点上都提交，要么都不提交。

参考：
- https://ongardie.net/static/raft/userstudy/paxos.pdf: Implementing Replicated Logs with Paxos
- https://cloud.tencent.com/developer/article/1158799
- https://zhuanlan.zhihu.com/p/45742830
- https://stackoverflow.com/questions/29619185/why-is-it-legit-to-use-no-op-to-fill-gaps-between-paxos-events
- https://stackoverflow.com/questions/47013036/why-is-it-legit-to-take-the-next-two-commands-to-fill-gaps-between-paxos-events?noredirect=1&lq=1
- https://max.book118.com/html/2019/0602/8121055051002026.shtm: PaxosStore分布式数据库的应用实践

----

## html+js demo: raft

https://superzhangmch.github.io/tiny_tools/demo/computer_science/raft.html


RAFT QA:

Q1：数据只能 master（leader）写入吗？

是，这是刻意设计。共识最难的是"多个提议者并发提议怎么达成一致"（Paxos 的复杂性大半来自这里）； Raft 釜底抽薪：先选举保证任意时刻至多一个合法提议者，"达成一致"就退化成 leader 说了算 + 多数派抄作业。 follower 收到写请求只会重定向到 leader（事件日志里能看到"重定向"）。 注意读也不能随便读 follower——它的数据可能落后甚至是未提交的分叉，线性一致读要走 leader（ReadIndex/lease）。

Q2：follower 靠同步得到数据，那 leader 挂了最多丢几条吧？

不对——已提交的一条都不丢，零条。会消失的只有"没提交的"，而那些客户端从未收到成功回执（ack）， 语义上等于请求没发生，重试即可。机制是选举限制：投票时日志不够新的候选人拿不到票，而"已提交"意味着在多数派上， 任何能当选的多数派必与之有交集 → 新 leader 数学上必然携带全部已提交日志。这是定理不是运气。
你的直觉描述的其实是 MySQL 异步主从：先 ack 后同步，主挂真丢已确认数据。Raft 恰好反过来：先多数派落盘、后 ack， 代价是每笔写多一个复制 RTT。

Q3：写入全是串行的，撑不起大并发吧？现实中怎么解决？

两层手段。
- 第一层：单组没那么慢——"串行"指日志顺序串行，不是一条一个 RTT。 生产实现靠 batching（把并发到达的几百条请求打包进一条 AppendEntries、一次 fsync、一个 RTT）+ pipelining（不等上批 ack 就发下批）。RTT 决定延迟（几毫秒），不决定吞吐；单个 etcd 组实测几万写/秒。 本 demo 的 MAX_ENT=8 就是 batching 的极简版（消息上标"日志×8"）。
- 第二层（真正的答案）：分片——TiKV/CockroachDB/Spanner/OceanBase 把数据按 key 切成上万个 region， 每个 region 一个独立 Raft 组，leader 均匀散布在所有机器上（multi-raft）。串行只在单分片内，分片间完全并行， 吞吐随机器数线性扩展。

Q4：那银行交易系统怎么办？撑得起大规模交易吗？

银行反而是最佳案例：账户天然就是分片键，而同一账户的操作本来就必须串行 （余额检查、扣款不串行才是灾难）——Raft 单分片内的串行不是性能缺陷，是业务刚需白送了； 不同账户间毫无顺序约束，分片后天然并行。跨账户转账（两个分片）在两个 Raft 组之上跑两阶段提交 （Percolator/Spanner 模式）。存在性证明：支付宝双十一峰值几十万笔/秒，底下的 OceanBase 就是 "Paxos 分片 + 多副本零丢失"架构。

Q5：就是说，不同用户走了不同的 Raft？

对。一笔请求的路径：账户号 → 定位到分片 region_1382 → 该 region 自己的 Raft 组（3 副本）→ 组内走完整 Raft 流程。隔壁账户落在 region_2907，是完全不同的一组 leader/follower，两笔写入互不照面。 关键细节：① 一台机器同时是几百个组的 leader、几百个组的 follower，负载天然摊平； ② 分片是动态的，变热就分裂/迁 leader；③ 每组独立选举独立故障，一台机器挂了只影响它当 leader 的那些组， 爆炸半径被切碎。

分层图景：Raft 管一个分片内的顺序与持久 → 2PC 管分片间的原子性 → 路由层管谁去哪。 Kafka 同理：partition 内严格有序、partition 间并行。

Q6：还有个和 Raft 类似的叫什么来着？用它的不多吗？（Paxos）

Paxos，Lamport 1989 年提出，是 Raft 的前辈，两者本质等价：Basic Paxos 只对单个值共识， 工程上用的 Multi-Paxos（稳定 proposer + 日志复制）结构上已和 Raft 几乎一样。 Raft 论文标题就叫《In Search of an Understandable Consensus Algorithm》——动机就是 Paxos 太难懂、 论文与工程之间鸿沟太大，各家实现的都是无法互相验证的魔改变体。

"用得不多"是错觉，只是分布不同：Paxos 藏在大厂闭源系统里（Google Chubby/Spanner、Azure 存储、 OceanBase、PolarDB），Raft 统治开源（etcd/Kubernetes、Consul、TiKV、CockroachDB、Kafka KRaft）， 2014 年后新系统几乎无脑选 Raft——工程师能看懂、能实现对、能调 bug。 另有两个亲戚：ZAB（ZooKeeper）和 Viewstamped Replication（1988 年，想法比 Paxos 还早，名气小得多）。 一句话：同一个定理的两种讲法，Paxos 赢了历史和大厂，Raft 赢了人心和开源。

Q7：Paxos 和 Raft 是不是基本等价？

是，且有学术背书（Howard & Mortier 2020《Paxos vs Raft》）：Raft 可视为 Multi-Paxos 的一个特定变体， 安全性保证完全相同。等价的部分：同解状态机复制问题（2F+1 容忍 F 故障）、同样的"多数派交集 + 单调任期号 （term ≡ ballot）+ 见高就退"、正常路径同为 leader 一个 RTT 提交、同受 FLP 约束（安全性恒成立，活性靠随机化）。
不等价的是工程性状，全是同一个取舍的侧面——Raft 用"只许日志最新者当选"换掉了 Paxos 最烧脑的"当选后修补"：
- 谁能当 leader：Paxos 任何节点 / Raft 只有日志最新的节点（选举限制）
- 当选后：Paxos 要反向学习补自己缺的日志 / Raft 天生最全，什么都不用做
- 日志形态：Paxos 允许有洞、槽位乱序敲定 / Raft 严格连续无洞
- 数据流向：Paxos 双向 / Raft 永远单向 leader→follower

代价是灵活性：Paxos 的洞支持乱序提交的并行度，Flexible Paxos 还允许选举与复制用不同大小的法定人数 （如 5 节点 2 票复制 + 4 票选举），这些在原版 Raft 里施展不开。一句话：数学上是同一个东西的两种参数化， 工程上是两种性格——Paxos 把复杂度留给实现者换灵活性，Raft 把灵活性上交换可实现性。这正好解释 Q6 的现象。

----

下面是 chatgpt 给的资料：

在分布式系统中，**Paxos** 和 **Raft** 是两类常用的强一致性共识算法，目标是在多个节点间，即使有节点或网络故障，也能就某个值或一系列操作达成一致。这种一致性是**逻辑顺序一致性**（logical order），而不是依赖真实时间的物理顺序。

## 1. 典型应用场景

* **分布式数据库 / 存储系统元数据一致性**：如表结构、分片位置、主节点信息等必须强一致的元信息。
* **Leader 选举**：保证集群中同时只有一个有效 leader。
* **分布式日志复制**：维护副本间完全相同的有序操作日志。
* **分布式锁服务**：确保同一资源在同一时间只被一个客户端占用。
* **关键配置管理**：动态更新全局配置，确保所有节点视图一致。

## 2. 关键数据 vs 非关键数据

一个大系统重，一般用他们保证的是关进数据的一致性。

* **关键数据**：影响系统正确性，必须走 Paxos / Raft，保证强一致性。
* **非关键数据**：可短暂不一致，常用异步复制、最终一致性等方式同步，以换取性能。

## 3. 粒度问题：不是单个用户，单条记录，或者单个表。而是聚合后的某种数据分片上做数据一致性

实际系统中，**共识协议的运行单位不是单个用户、记录或表，而是聚合后的数据分片**（Shard / Region / Tablet / Partition），每个分片有自己的副本组（Paxos group / Raft group）。
原因：

1. **降低固定开销**：维护一个共识组有常驻成本，不能为每条记录建组。
2. **提高并行度**：多个分片的共识可同时进行，避免单 Leader 瓶颈。
3. **负载均衡**：分片的 Leader 分布在不同节点，均衡资源消耗。

所以关系数据库用它时，也不是针对具体的单个记录，或者是某个表，而是在更宏观的层次用。

## 4. 共识组的工作方式

* 每个分片的多个副本分布在不同节点 / 机房。
* 写操作只需在该分片的多数派副本间达成一致（多数写入成功即可提交）。
* 同一共识组内，所有写操作的顺序和内容一致（状态机复制原理）。
* 不同共识组间没有天然的全局顺序，除非额外引入事务协调。

## 5. 工程案例

* **Spanner**：每个 Tablet 是一个 Paxos group，写操作在组内多数副本间达成一致；用 TrueTime 协调跨组事务。
* **TiKV（TiDB）**：数据切为 Region，每个 Region 是一个 Raft group。
* **MySQL Group Replication**：基于 Paxos 思路的多副本一致性协议。
* **微信 PhxStore**：核心用户数据分片，每片是一个 Paxos group。
* **Kafka KRaft**：每个 Topic 分区是一个 Raft group。
