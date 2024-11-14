# kafka 为什么不丢数据

kafka有多副本机制，所以不丢数据。

多副本间会选取出leader，承担读写任务，非leader只作数据备份。写入的时候会通过ISR(in-sync Replica；所有和leader同步的副本构成的集合)机制，保证leader写入ok，以及ISR也需要有副本写入ok（后者写入失败，则给上游报错，让上游重试），才告诉上游本次写入ok。这样leader挂掉后，还是有副本保留有数据的——这时候只需要让有完整数据的副本成为leader即可了。怎样保证数据更完整的副本成为leader，有kafka的内部组件（controller）来负责该选取。而controller的选取，是用的zookeeper的抢占式节点注册机制（最新的kafka要支持抛掉zk，直接用raft了）。

除非所有副本挂掉，否则总可以恢复出数据。

大体如上。

<br>

kafka要做的数据不重，方式是上游的请求包带一个序列数字，kafka据此去重 （ https://www.zhihu.com/question/54480847 ）。

再另外，如果只就主副本而言，如果有丢数据，一定是本来就没写成功（client没检查返回的状态码）。

参：https://blog.csdn.net/qq_35688140/article/details/103923461

producer的消息发送的3种确认机制：根据leader写入后，对follower的同步情况而分；如果leader写完不等同步就返回，那么还是可能丢数据的。
参考：https://www.jianshu.com/p/c98b934f2c2b
