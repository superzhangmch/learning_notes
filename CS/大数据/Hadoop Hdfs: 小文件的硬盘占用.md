# Hadoop Hdfs: 小文件的硬盘占用

2014.01

hadoop hdfs 文件存储的时候的block 大小是很大的，比如64M一个，远大于机器的本地文件系统的block大小。

那么如果在hdfs上存储一个小文件，到底会占用多大的硬盘空间呢？

从 http://stackoverflow.com/questions/15062457/hdfs-block-size-vs-actual-file-size 看，其实只占用很小的硬盘空间。实际上 64M 的块大小，只是文件切分存储的大小。小文件对于 hadoop的影响在于对于 namenode的影响。

### [附]
http://stackoverflow.com/questions/15062457/hdfs-block-size-vs-actual-file-size 引用如下：
#### Q:
> I know that HDFS stores data using the regular linux file system in the data nodes. My HDFS block size is 128MB. Lets say that I have 10GB of disk space in my hadoop cluster that means, HDFS initially has80 blocks as available storage.
>
> 
> If I create a small file of say 12.8MB, #available HDFS blocks will become 79. What happens if I create another small file of 12.8MB? Will the #availbale blocks stay at 79 or will it come down to 78? In the former case, HDFS basically recalculates the #available blocks after each block allocation based on the available free disk space so, #available blocks will become 78 only after more than 128 MB of disk space is consumed. Please clarify.

#### A:

> But before trying, my guess is that even if you can only allocate 80 full blocks in your configuration, you can allocate more than 80 non-empty files. This is because I think HDFS does not use a full block each time you allocate a non-empty file. Said in another way, HDFS blocks are not a storage allocation unit, but a replication unit. I think the storage allocation unit of HDFS is the unit of the underlying filesystem (if you use ext4 with a block size of 4 KB and you create a 1 KB file in a cluster with replication factor of 3, you consume 3 times 4 KB = 12 KB of hard disk space).
>
> 
> Enough guessing and thinking, let's try it. My lab configuration is as follow:
> - hadoop version 1.0.4
> - 4 data nodes, each with a little less than 5.0G of available space, ext4 block size of 4K
> - block size of 64 MB, default replication of 1
>
> 
> After starting HDFS, I have the following NameNode summary:
> 
> - 1 files and directories, 0 blocks = 1 total
> - DFS Used: 112 KB
> - DFS Remaining: 19.82 GB
>
>
> Then I do the following commands:
> - hadoop fs -mkdir /test
> - for f in $(seq 1 10); do hadoop fs -copyFromLocal ./1K_file /test/$f; done
>
> With these results:
> - 12 files and directories, 10 blocks = 22 total
> - DFS Used: 122.15 KB
> - DFS Remaining: 19.82 GB
>
> So the 10 files did not consume 10 times 64 MB (no modification of "DFS Remaining").
