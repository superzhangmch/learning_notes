# hive: 分桶与分桶 mapjoin

若有分区，则分桶是在分区下的更细粒度的划分。一个分桶对应一个hdfs的文件（连续标号的那种文件）。

### 分桶表的创建： 
```
create .... clustered by(字段可多个) into 桶数 buckets
```

### 数据引入：

```set hive.enforce.bucketing = true```然后```insert ... select ... from```或者```set mapreduce.job.reduces = 桶数; set mapreduce.reduce.tasks = 桶数;``` （所以reducer数量和桶数一致），然后【```insert into ... select ... distribute by ...```】，distribute by 用来分桶存放。

执行join的两个表，如果分桶数一样或者是倍数关系，且join字段是分桶字段，则可以执行bucket map join。原理是对应的桶直接作map join（非bucket map join，则是某个表的全表数据内存load后和另一个表join）。用```set hive.optimize.bucketmapjoin = true```开启。

### 参看：
https://blog.csdn.net/wisgood/article/details/80068834
https://www.linkedin.com/pulse/quick-card-apache-hive-joins-kumar-chinnakali： hive的各种join
