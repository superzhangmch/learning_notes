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
