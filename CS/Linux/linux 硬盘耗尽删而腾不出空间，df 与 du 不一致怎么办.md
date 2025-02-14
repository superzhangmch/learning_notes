# linux 硬盘耗尽删而腾不出空间，df 与 du 不一致怎么办

一般来说，linux下用```df -h XXX```, 可以看XXX所在硬盘的使用情况。如果将满，执行相应的```du -sh ```后可能查看哪些文件夹占用较多，从而有选择性地清理硬盘空间。

当你根据```du -sh``` 删除了一些文件后，发现空间还是不够。于是再次删，删来删去，删无可删了——回想起上次发生同样的情况时，这招很有用的。为啥这次没效了？
于是你对整个磁盘的所有文件夹做了```du -sh```操作，并做了累加，发现du 和 df的结果居然不一样。而且是相差很大。

这时候往往是因为：df 是看的未释放的文件占用总大小；而du看的是未删除的文件的总大小。有可能某文件被你手动rm删除了，但是还被某后台进程占用着（比如写日志文件）——于是du是看不见了，但是df还看得到它(linux底层是用inode机制管理的，文件名指向它；你删除的只是文件名到inode的映射；别的进程还在指向这个inode，于是文件不会释放；甚至文件还能默默变大)。

这时候怎么处理呢？用那个```lsof | grep delete``` 就可以找出相应的已删文件，以及其大小，以及占用它的进程。这时候把进程啥了，空间自然就会被释放了。

note：对于长期后台会写日志的任务，删除其日志的时候，用　重定向符号 ( > ) 的方式；而别直接删除。否则这个文件就变成孤魂野鬼了。

参看：https://www.pianshen.com/article/10701774084/
