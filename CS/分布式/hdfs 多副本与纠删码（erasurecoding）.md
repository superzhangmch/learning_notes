# hdfs 多副本与纠删码（erasurecoding）

纠删码原理是，一个(m+n)*m的（且一头是单位矩阵）矩阵作用于n维原数据向量，生成一个m+n维的新向量；其中前m维是原数据，后n个是纠删用的。当确实不超n个时，可以通过解方程方式或者说乘某个类似逆矩阵一样的矩阵，还原原数据。

本来hdfs是按几十上百M大小的block以此顺序存放；同时每个block多复本。

用了假设是6+3的纠删码后：每9个block构成一个group，然后每个block内分为多个strip条带，假设strip大小是S。原始数据按S大小切分，每6个块做一次纠删编码生成9个块，依次占据 block group的一层strip(是为striping layout存储)；如是逐层直到占满整个block group；然后重新开启一个group(这样每个hdfs的block存放的并不是连续的数据)。block group内的block全分散存储。这样当只坏了一台机器的时候，往往只损坏了一个block group内的一个block，是可以得到修复的。按6+3的话，用了原始数据的1.5倍空间（而用3复本则是3倍空间）

参：
- https://blog.cloudera.com/introduction-to-hdfs-erasure-coding-in-apache-hadoop/
- https://cloud.tencent.com/developer/article/1031637


另外，hdfs不用以上纠删码码时，为了数据安全，存多个副本，但是其同步并不用raft、paxos之类。而是用数据作签名后namenode存下签名，保证各个节点的签名值一样的方式。后台有进程周期性作check，以修复损坏的数据。大体这样，细节需确认后补。
分享：
