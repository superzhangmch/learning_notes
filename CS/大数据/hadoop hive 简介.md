# hadoop hive 简介

2014-03-23

hive 从外部看，和一般的关系型数据库没什么两样，基本一样的表定义方式，基本一样的SQL；尤其是在最终用户看来，一样的使用方式（不考虑适用场景的话）。

从底层实现看，hive又相当于是一个明文格式存储的文本数据库：select * 出来的是表格长什么样，在底层存储上也是这样存的（用分隔符把明文字段分割存放）。实际上，往hive添加数据只能通过导入方式，而导入的实现很简单，就是copy，都没有一点格式检查。

当然了，在具体的实现上，其实远不是以上这样，但是确实按以上理解就是。

实际实现上，hive是利用map/reduce在hadoop hdfs上所存的有一定格式的文件上进行数据检索。往hive导入数据，实际就是把数据文件复制到hdfs特定地方；hive的sql执行，实际上就是转化为实际的map/reduce job并执行，而map/reduce得到的结果正是该sql的查询结果。但是hive毕竟太像一般的关系数据库了，而导致很像的hive中的表结构等等信息其实是存在关系数据库中的，比如 mysql。

hive sql工作的时候，是靠从mysql等数据库中，取得sql中所涉及到的表的具体相关信息，然后转化成map/reduce job，然后在hdfs的相关文件上查询得到结果。

大概就是这样。

贴一段实际操作过程吧：
### （1）创建表
```
hive> create table test_hive2 (id int,id2 int,name string) row format delimited fields terminated by '\t';
create table test_hive2 (id int,id2 int,name string) row format delimited fields terminated by '\t';;
OK
Time taken: 0.033 seconds
```

### （2）导入数据
./data.txt中内容为：
```
$cat data.txt 
1      1234   aa1
2      1234   aa2
3      1234   aa3
4      1234   aa4
5      1234   aa5
6      1234   aa6
7      1234   aa7
9      1234   aa8
```
导入：
```
hive> LOAD DATA LOCAL INPATH './data.txt'  OVERWRITE INTO TABLE  test_hive2;
LOAD DATA LOCAL INPATH './data.txt'  OVERWRITE INTO TABLE  test_hive2;
Copying data from file:/home/work/hadoop-2.2.0/hive-0.11.0-bin/bin/data.txt
Copying file: file:/home/work/hadoop-2.2.0/hive-0.11.0-bin/bin/data.txt
Loading data to table default.test_hive2
rmr: DEPRECATED: Please use 'rm -r' instead.
Deleted /user/hive/warehouse/test_hive2
Table default.test_hive2 stats: [num_partitions: 0, num_files: 1, num_rows: 0, total_size: 72, raw_data_size: 0]
OK
Time taken: 0.28 seconds
```
### （3）查看导入结果
```
hive> select * from test_hive2;
select * from test_hive2;
OK
1      1234   aa1
2      1234   aa2
3      1234   aa3
4      1234   aa4
5      1234   aa5
6      1234   aa6
7      1234   aa7
9      1234   aa8
Time taken: 0.088 seconds, Fetched: 8 row(s)
```

### （4）实际sql检索下
```
hive> select * from test_hive2 where id >2 and id< 5;
select * from test_hive2 where id >2 and id< 5;
Total MapReduce jobs = 1
Launching Job 1 out of 1
Number of reduce tasks is set to 0 since there's no reduce operator
Starting Job = job_1395576653572_0004, Tracking URL = http://cq01-testing-ps1006.cq01.xxx.com:8088/proxy/application_1395576653572_0004/
Kill Command = /home/work/hadoop-2.2.0/bin/hadoop job  -kill job_1395576653572_0004
Hadoop job information for Stage-1: number of mappers: 1; number of reducers: 0
2014-03-23 23:22:05,262 Stage-1 map = 0%,  reduce = 0%
2014-03-23 23:22:09,422 Stage-1 map = 100%,  reduce = 0%, Cumulative CPU 1.46 sec
2014-03-23 23:22:10,457 Stage-1 map = 100%,  reduce = 0%, Cumulative CPU 1.46 sec
2014-03-23 23:22:11,490 Stage-1 map = 100%,  reduce = 0%, Cumulative CPU 1.46 sec
MapReduce Total cumulative CPU time: 1 seconds 460 msec
Ended Job = job_1395576653572_0004
MapReduce Jobs Launched: 
Job 0: Map: 1  Cumulative CPU: 1.46 sec   HDFS Read: 328 HDFS Write: 22 SUCCESS
Total MapReduce CPU Time Spent: 1 seconds 460 msec
OK
3      1234   aa3
4      1234   aa4
Time taken: 11.845 seconds, Fetched: 2 row(s)
```

### (5).数据导入后查看下 hdfs 的存储
```
$./hadoop fs -D fs.defaultFS=hdfs://10.48.41.39:9000  -cat /user/hive/warehouse/test_hive2/data.txt 
1      1234   aa1
2      1234   aa2
3      1234   aa3
4      1234   aa4
5      1234   aa5
6      1234   aa6
7      1234   aa7
9      1234   aa8
```
与源文件是相符的

### （6）从mysql中看到了test_hive2表的相关信息：
```
6 1395587037 1 0 work 0 6 poke(表名) MANAGED_TABLE NULL NULL
8 1395587666 1 0 work 0 8 test_hive2(表名) MANAGED_TABLE NULL NULL
```
