# linux 的两个 time 命令

一般的linux下有2个time 命令：直接time, /usr/bin/time。今天才知道两个的不同。

直接 time 的时候，其实是执行的bash内置的命令，不，是内置关键词。```type time``` 或 ```man bash``` 可知。

直接 time的结果是这样的：
```
$time sleep 1
```
output:
```
real   0m1.001s
user   0m0.000s
sys    0m0.000s
```

但是，更加强大的是作为命令的time， 一般在/usr/bin/里。直接看例子吧，能把转瞬即逝的命令的各种运行情况都打印出来。
```
$ /usr/bin/time -v sleep 1
```
output'
```
       Command being timed: "sleep 1"
       User time (seconds): 0.00
       System time (seconds): 0.00
       Percent of CPU this job got: 0%
       Elapsed (wall clock) time (h:mm:ss or m:ss): 0:01.00
       Average shared text size (kbytes): 0
       Average unshared data size (kbytes): 0
       Average stack size (kbytes): 0
       Average total size (kbytes): 0
       Maximum resident set size (kbytes): 2192
       Average resident set size (kbytes): 0
       Major (requiring I/O) page faults: 0
       Minor (reclaiming a frame) page faults: 175
       Voluntary context switches: 2
       Involuntary context switches: 0
       Swaps: 0
       File system inputs: 0
       File system outputs: 0
       Socket messages sent: 0
       Socket messages received: 0
       Signals delivered: 0
       Page size (bytes): 4096
       Exit status: 0
```

