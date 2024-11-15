# hadoop map-reduce使用: 分隔符问题

第一次用，调试半天，原因竟然出在一个 TAB 上，先简单记录下吧。

### 关于 TAB 坑
通过hadoop stream 执行 的时候，如果用了TAB（\t）外的分隔符，自然需要特别指定；如果用TAB作字段分隔符，可以不指定（默认就是TAB）。
但如果对TAB要特别指定，则不能写"\t"或'\t'或\t, 而需要是不转义的TAB字符本身($"\t" 或者输入TAB)。

### 怎样实现按前几列切分，不同列排序
以下实测通过：

用 ```-partitioner org.apache.hadoop.mapred.lib.KeyFieldBasedPartitioner```来表示要自定义partition方法。用 ```-jobconf mapred.text.key.partitioner.options=-k1,2``` 来表示用哪些字段作partition，这里-k指定key中的start\~end 范围。注意是key中的字段，而非整行中的字段。所以需要指定key由哪些字段组成。一种方式是用 ```-jobconf stream.num.map.output.key.fields=3```，表示前几个字段是key。

只由以上 ```-jobconf mapred.text.key.partitioner.options=-k1,2``` 与 ```-jobconf stream.num.map.output.key.fields=3 ```，实测是可以实现按前两列最终文件分桶，且每个桶内按前三列排序的。

### 题外话：
1. hadoop map-reduce 的job参数很繁杂。对我等新手，真是搞个半死，因此需要从整体上认识它。从整体上说，map-reduce就是个输入行间无序的管道处理系统，且此管道只能有两节(map, reduce)。除了作为2节管道，能得到的额外好处只有两个：1. 输出到多个文件的时候，可以选择输出到哪个文件； 2. 输出到每个文件的时候，数据可以按哪些字段排序。控制这两点的hadoop client 参数才是实实在在的，能帮助实现业务逻辑。其余参数只是为了高效执行任务。
2. hadoop 就像是一个分布式计算机系统。job运行系统就像是操作系统，hdfs就像是硬盘（Unix只有一个根目录，而hadoop 像windows有c盘d盘一样，允许有多个不同hdfs://hostname:port:/ 或afs://hostname:port/等指定出的跟目录）。

hadoop-site.xml 的 hadoop.job.ugi 指定了 user/password。这个账号是关于 job 执行系统的，但该账号在hdfs文件系统上也需要有相应的读或写权限。否则就像Unix系统中，可以登进系统，但执行不了文件操作。因此，执行 job 的时候，如果执行失败，需要看是否没有文件系统的读、写权限。对于-input，需有读权限，对于-ouput,需要写权限。因为hadoop 支持类似windows C、D盘一样多个“盘”（对应一个独立的hostname:port确定的hdfs文件系统）读写，因此需要保证每个“盘”上有相应的权限。当-input, -output 会跨越多个hdfs文件系统的时候，除了使用默认的那个，其他的都应该写全路径：hdfs://hostname:port/xx/bb/cc 这样。

### 更进一步：
1. 怎样指定分割符？
```
    -D map.output.key.field.separator="."
```
2. 怎样指定按某些列，而不是前几列排序？
```
   -D mapred.text.key.comparator.options="-k3,3nr"， 具体参数取值和sort命令一样。
```

### 一个简单说明示例
```
#提交hadoop任务
$HADOOP_HOME/bin/hadoop streaming \
    -D mapred.job.name=hadoop-task-name \
    -D mapred.job.map.capacity=100 \            #mapper程序的最大槽位数
    -D mapred.job.reduce.capacity=100 \          #reducer程序的最大槽位数
    -D mapred.reduce.tasks=100 \                #reducer程序的总数。该参数为0时为map-only任务
    -D mapred.job.priority=VERY_HIGH \          #设置任务优先级
   #上传自己的压缩包，系统会自动解压，#号之后为该压缩包解压后所在文件夹
    -cacheArchive hdfs://xxx:54310/yyy/yyy1/yyy2/lib.tar.gz#lib \
    -D stream.map.output.field.separator="." \      #设置map任务输出分隔符，默认为\t
    -D stream.num.map.output.key.fields=4 \       #设置map任务输出的前4列为key，如果指定了partition和sort，两项配置可省略，默认为1
   #sort之前会进行partition操作，相同partition才会分到相同的机器上进行reduce
   #默认按照整个key进行partition，同样也可以自定义
    -D map.output.key.field.separator="." \             
    -D mapred.text.key.partitioner.options="-k1,2" \    
   #以上两项配置表示按key中以.号分隔的前两列进行partition
   #partition之后便是sort，默认以整个key进行sort，同样也可以自己设置sort的方式
    -D mapred.text.key.comparator.options="-k3,3nr" \    
   #将partition后的key按第3列以数字大小反向排序，列的划分由上述的-D map.output.key.field.separator设定
    -D mapred.output.key.comparator.class=org.apache.hadoop.mapred.lib.KeyFieldBasedComparator \ 
    -partitioner org.apache.hadoop.mapred.lib.KeyFieldBasedPartitioner \
    -input /xxx/xxx1/xxx2/xxx3_*/* \          #指定输入文件HDFS目录，可以是目录，文件，正则表达式
    -output /aaa1/aaa2/aaa3/output/ \                    #输出文件
    -mapper "cat" \                                                         #map程序
    -file "reduce.py"                                      #上传reduce阶段需要的文件
    -reducer "lib/bin/python2.7 reduce.py"                   #reduce程序，此处使用的python为-cacheArchive打包上传的python
   #集群机器上python版本过低，不能import json，同时reduce.py运行的依赖也同样打包在lib.tag.gz文件中，可以将文件down到本地解压查看
```

参考：
http://hadoop.apache.org/docs/r1.2.1/streaming.html
