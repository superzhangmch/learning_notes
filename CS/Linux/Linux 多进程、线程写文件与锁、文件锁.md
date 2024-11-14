# Linux 多进程、线程写文件与锁、文件锁

Linux下多线程/线程写同一个文件（本文只说普通文件，而不考虑socket，pipe等）的时候，往往需要很谨慎，因为一不小心，就容易写乱写交叉。

下面讨论都基于写同一个文件的时候，每个进程都是独立的open了这个文件然后进行的操作，这样才会保证不同进程使用的不同的打开文件表中项。另外，只讨论write系统调用的情况，因为别的写（比如fwrite）都是间接通过write来实现的。再另外，多线程与多进程其实类似，所以这里就只讨论多进程。

<br>

首先，多进程写同一个文件的时候，如果导致了写交叉，其实只与write的时候的文件偏移指针有关。所以，如果每个进程write的时候，已经通过lseek 定位到了SEEK_END以外的确切的offset位置，那么这时候，其实不应该导致写交叉的。本来嘛，写的时候在文件中的偏移位置都是定的了，如果还交叉，只可能是多个进程没有就offset协调好而已。

因此，这个写交叉问题其实就在于文件追加写这种情况。下面也只讨论这种情况。

<br>

而不管怎样导致的写交叉，通常可以通过上锁或者上文件锁，来避免这种情况。但是锁应该怎样上呢？什么时候上锁是必须的？

如果一个进程要连续多次（比如fwrite 库函数调用内部实现中往往会多次write）调用write系统调用追加（只考虑追加）写一段内容，且希望所写的内容在文件中保持连贯，那么就应该给这一段内容的连续多次write加锁。这一点，也是很容易理解的。

<br>

但是如果是每个进程每次追加写只调用一次write呢？也就是只希望每一次write的内容不与别的进程交叉就行。这种场景的一个例子就是多个进程同时写一个log文件。

这时候需要分析下每次追加写到底是怎样写的。一般是 lseek(SEEK_END)令文件指针指向文件末尾，然后从这个位置开始write。也就是需要 lseeek(SEEK_END) + write() 一对的组合才能完成。

既然这样，考虑下面的场景：

> 假设有一个500M普通文件，write 系统调用在文件的末尾追加了另外500M数据，调用用了100ms（该时间纯属假设）；
>
> 然后在另外一个进程中lseek（SEEK_END）（当然这时候需要两个进程不共享关于这个文件的打开文件表项），如果lseek 发生在write运行了50 ms 的时候，那么这时候的lseek的结果会指向什么地方？是文件的500M地方，还是1000M地方，还是500~1000M之间某个地方？

可见，这个场景下的那个问题是不好回答的，而这个问题的回答，会导致“每个进程每次追加写只调用一次write时是否会写交叉”有不同的答案。如果lseek到的位置是500~1000M的某个地方，那么就等于说，一次write调用在执行到一半还有部分内容没有写完的时候，可能在这个间隙被别的进程的write所影响，从而导致写混乱；从而意味着write是非原子性的。

因此，为了弄明白“每个进程每次追加写只调用一次write时是否会写交叉”这个问题，必须设计几个实验，才能回答这个问题。

先把答案写出来，答案是：如果另一个进程中的lseek发生在，别的进程正在write的过程中，那么不会导致写交叉。因为假如一个进程正在500M大小的文件上追加write500M内容；在写了100M的时候，如果在另外一个进程中用stat看文件大小会是600M，但如果用lseek(SEEK_END)看，会得到1000M，而且这时候会导致stat返回文件大小是1000M（看起来lseek 会等待write完成)。

<br>

也就是说，多进程同时追加写一个文件的时候，如果只要求每个write系统调用所write的内容别发生交叉，是貌似不需要上锁的。但是，先别开心太早，注意 lseek(seek_end) + write 两个组合才能完成追加。当一个进程在追加写的时候，可能只完成了lseek，还没有开始write，另外一个进程就在lseek了；结果，两个进程读到了同一个文件末尾，因此又写乱了。这样看，还是免不了加锁（只对write加文件锁都不行的）。

其实，只需要open的时候加O_APPEND就是了。用O_APPEND可以令“每个进程每次追加写只调用一次write时是否会写交叉”不会发生写交叉，还能保证不用加任何锁（内部已经有锁了吧）。

=====================================

附上试验如下（注意先估计了下1G文件一次write调用用时大约500ms左右（再注意这不代表写硬盘速度），每次运行的时候，都先清空文件）：

```
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include <stdio.h>

#include <sys/wait.h>
#include <sys/time.h>

int main()
{
       int fd=open("./a.txt", O_CREAT|O_RDWR, S_IRWXU );
       int ll= 1 * 1024* 1024* 1024;
       char * buf = new char[ll];

       struct timeval tpstart,tpend, t1;

       pid_t p = fork();          
       if(p == 0)
       {
             gettimeofday(&tpstart,NULL);
              int ffdd=open("./a.txt", O_CREAT|O_RDWR );
              int len=-1;
              off_t of=-1;
              struct stat b;
              int i=0;
              for(i = 0; i ＜ 30 ;i++ )
             {
                    gettimeofday(&t1,NULL);
                    if(i>7)
                    {
                           of=lseek(ffdd, 0 , SEEK_END ); // note here 
                    }
                    len=stat("./a.txt", &b); // note here 
                    gettimeofday(&tpend,NULL);
                    printf("%d:stat=%d, lseek=%d time_diff=%ld time_sum=%ld\n",
                           i, b.st_size, of, 
                          (tpend.tv_sec-t1.tv_sec)*1000000
                             +tpend.tv_usec-t1.tv_usec,
                          (tpend.tv_sec-tpstart.tv_sec)*1000000
                             +tpend.tv_usec-tpstart.tv_usec);
                    usleep(25000);
             }
             printf("proces_end\n");
       }
       else
       {
             gettimeofday(&tpstart,NULL);
             printf("write_begin\n");
              int r=write(fd, buf, ll-1);
             gettimeofday(&tpend,NULL);
             printf("write_end time=%ld\n", 
                   (tpend.tv_sec-tpstart.tv_sec)*1000000
                      +tpend.tv_usec-tpstart.tv_usec);
             close(fd);
             wait(0);
       }
       return 0;
}
```
运行结果为：

```
0:stat=0, lseek=-1 time_diff=5 time_sum=8
write_begin
1:stat=37957632, lseek=-1 time_diff=7 time_sum=27197
2:stat=75878400, lseek=-1 time_diff=6 time_sum=54196
3:stat=114728960, lseek=-1 time_diff=6 time_sum=81198
4:stat=154476544, lseek=-1 time_diff=6 time_sum=108189
5:stat=196689920, lseek=-1 time_diff=7 time_sum=135236
6:stat=240586752, lseek=-1 time_diff=7 time_sum=162242
7:stat=284123136, lseek=-1 time_diff=6 time_sum=189229
＃注意在write过程中stat结果在一直增长，stat调用所用时间还是很短的，这时候一直没有lseek
8:stat=1073741823, lseek=1073741823 time_diff=469366 time_sum=685582
＃开始调用lseek。lseek调用后，lseek返回位置与stat结果一样。且lseek所用时间很长
＃lseek返回后，write已经结束，也就是说lseek一直在等待write结束
write_end time=685521
9:stat=1073741823, lseek=1073741823 time_diff=3 time_sum=713168
10:stat=1073741823, lseek=1073741823 time_diff=3 time_sum=740166
11:stat=1073741823, lseek=1073741823 time_diff=2 time_sum=767163
12:stat=1073741823, lseek=1073741823 time_diff=2 time_sum=794159
13:stat=1073741823, lseek=1073741823 time_diff=2 time_sum=821157
14:stat=1073741823, lseek=1073741823 time_diff=2 time_sum=848153
15:stat=1073741823, lseek=1073741823 time_diff=2 time_sum=875151
16:stat=1073741823, lseek=1073741823 time_diff=2 time_sum=902148
17:stat=1073741823, lseek=1073741823 time_diff=2 time_sum=929146
18:stat=1073741823, lseek=1073741823 time_diff=2 time_sum=956143
19:stat=1073741823, lseek=1073741823 time_diff=2 time_sum=983142
20:stat=1073741823, lseek=1073741823 time_diff=2 time_sum=1010138
21:stat=1073741823, lseek=1073741823 time_diff=2 time_sum=1037136
22:stat=1073741823, lseek=1073741823 time_diff=2 time_sum=1064133
23:stat=1073741823, lseek=1073741823 time_diff=2 time_sum=1091132
24:stat=1073741823, lseek=1073741823 time_diff=2 time_sum=1118128
25:stat=1073741823, lseek=1073741823 time_diff=2 time_sum=1145125
26:stat=1073741823, lseek=1073741823 time_diff=1 time_sum=1172122
27:stat=1073741823, lseek=1073741823 time_diff=1 time_sum=1199120
28:stat=1073741823, lseek=1073741823 time_diff=1 time_sum=1226117
29:stat=1073741823, lseek=1073741823 time_diff=2 time_sum=1253115
proces_end
```
