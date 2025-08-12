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
