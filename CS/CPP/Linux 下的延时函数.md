# Linux 下的延时函数

Linux下延时函数，大概是这么几个: ```sleep，usleep，nanosleep，select```。
- sleep提供秒级的延时
- usleep是微秒（百万分之一）级别
- nanosleep是纳秒（10亿分之一）级别
- select 从其参数看是为微秒（百万分之一）级别的。

其中，nanosleep，select是内核提供的系统调用，而前两个一般使用nanosleep实现出来的。

虽然宣城能达到怎样怎样的延时精度，但是未必为真。在传统上，nanosleep与select都是基于内核的时钟中断所实现的定时器来实现的，而时钟中断的频率大概是1000HZ（或更早的100HZ），所以这两个函数的延时精度其实是毫秒（千分之一）级别的。在所测试的 2.6.9.5 内核的机器上，经过试验，确实是这样的，当然别的几个函数的精度也是如此。

后来得知在较新内核的机器上，以及实现了高精度定时器（HPET），可以达到纳秒精度的延时，于是在 2.6.32.1 内核（记得说2.6.16开始支持的）的机器上试验。发现在这个内核下，几个延时函数的精度确实是提高了不少，达到了毫秒以下，nanosleep(1纳秒)的gettimeofday统计的用时是52微秒（相对之下，旧内核是一两千呢）。说明确实是实现了高精度的延时。当然，真正纳秒的延时，那是简直不可能的，只是用于统计时间的gettimeofday调用就要消耗不少时间呢。

而且发现，sleep，usleep，nanosleep，select这四个函数都达到了同样精度的毫秒以下的精度。

测试用的函数大概是这样：
```
#define SLEEP_USEC 1
int main()
{
       struct  timeval   s;
       struct  timeval   e;
       struct  timezone   tz;

       struct  timeval   tv;

       struct timespec ts;
       ts.tv_sec=0;
       ts.tv_nsec = 1000 * SLEEP_USEC; 
       int i=0;
       for(i=0;i < 10; i++)
       {     
             tv.tv_sec=0;
             tv.tv_usec= SLEEP_USEC;
             gettimeofday(&s,&tz);
             nanosleep(&ts, 0);
              // sleep(...);
              // usleep(...);
             // select(0, NULL, NULL, NULL, &tv);
             gettimeofday(&e,&tz);
             printf("%ld ", (e.tv_sec-s.tv_sec)*1000000+(e.tv_usec-s.tv_usec));
       }     
      printf("\n");
       return 0;
}
```
新内核下，nanosleep(1毫秒)，输出为：
```
1056 1055 1054 1055 1054 1054 1054 1054 1054 1054
```
旧内核下是：
```
2219 1982 1998 2002 1996 1999 1998 1999 2001 1996
```
old 内核下，即使是nanosleep（<<1毫秒），输出也差不多是这个数据。

