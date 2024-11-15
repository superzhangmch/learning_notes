# hadoop：mapper数据切分

hadoop mr任务会把输入分到多个mapper。并不按输入文件数划分，而是对单个文件，也可能划分给不同的mapper。而一个文件内部是连续的行，那么单个文件切分的时候就可能切到了一行内。

非常大体的说，hadoop不会提前记住行的分界点，而是如果分界点在一行中间，则分界点后的跳过首行，分界点前的多读半行或一行。具体还没深究。


参考：
- https://blog.csdn.net/wanghai__/article/details/6583364
- https://community.cloudera.com/t5/Support-Questions/How-hadoop-handles-line-record-when-it-spans-block-boundary/td-p/219668/questions/14291170/how-does-hadoop-process-records-split-across-block-boundaries
