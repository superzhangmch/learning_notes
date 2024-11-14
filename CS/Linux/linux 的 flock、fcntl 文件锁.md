# flock/fcntl: linux 文件锁 

多个进程写同一个文件的时候，总是需要一些机制来保证操作正常的。一个机制就是用锁:flock 或 fcntl。fcntl 可以实现对文件的局部或全部加锁，而flock 只能对整个文件加锁。

#### 下面说下flock：
用flock 加锁的进程退出后，锁自动释放，但是如果进程又fork 了别的进程且这别的进程还在运行，这时候，往往这个锁不会被自动释放——因为flock 是通过文件描述符来加锁的，而这些信息被继承了下去。

man 手册说“Locks created by flock() are associated with a file, or, more precisely, an open file table entry. ”，这让我以为 flock 锁是在 open file table entry 上面实现的，因此以为只有在父进程以及fork的子进程间才可以用flock。如果这样的话，这个锁的实用性就大打折扣了。

经过试验，发现并不是这么回事，一个进程完全可以被另一个八竿子打不着的进程的flock操作所影响。后来查看些资料( http://www.ibm.com/developerworks/cn/linux/l-cn-filelock/index.html )原来，flock的锁，并不是在open file table entry 上面实现的，只是会被open file table entry 获得锁而已。因此与 open file table entry 关联的进程都退出后，锁自动就释放了。

fcntl的锁有所不同，但是同样是完全的跨进程锁。

这样，多进程比如写同一个log的时候，就完全可以这样子操作了（其实pwrite， open(O_APPEND)也都可以）。
