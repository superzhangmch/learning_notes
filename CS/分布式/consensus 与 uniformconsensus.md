# consensus 与 uniformconsensus

《Designing Data Intensive Applications》一书367页提到 uniform consensus 的概念。

其实uniform consensus与非uniform consensus的区别在于agreement这条。前者要求所有节点都需要decide，无论是否故障；而后者只要求没故障的dicide即可。wiki上可查到这点，书中提到的参考论文中也可见。

另外design一书提到:
> uniform consensus, which is equivalent to regular consensus in asynchronous systems with unreliable failure detectors。

参看：
- https://en.wikipedia.org/wiki/Uniform_consensus
- http://events.jianshu.io/p/268aca0d6030 （里面提到：一般的Consensus问题通常用来解决状态机复制时容错处理的问题, 比如Paxos, 而Uniform Consensus所处理的是分布式事务这样的问题, 在Uniform Consensus中我们要求所有节点在故障恢复后都要达成一致. 所以Uniform Consensus的定义在agreement上更加严格）
