# 库函数 memcpy()

程序员面试中，常常被问到memcpy。首先承认，我自己就曾栽倒在这个上。因为是电话面试，只能对着空气想，于是难免想得不周到。当时就感觉可以对于地址对齐后，按每四个或八个字节(即按int/long 方式逐个copy)这样的copy，当然就把想法说了出来，说着说着，发现不对啊，因为源地址与目的地址，是难以同时对齐的。接下来，当然就是一阵手乱脚忙了。

当然，按对齐的方式，即使源地址与目的地址不能完全对齐，但是如果只对齐其中的一种(源或目的)，那么理论上说，就假如是64位机器上对齐到八字节方式吧，也可以由每copy 8字节分8次变成2次完成，还是会快不少。虽然比理想情况下的1次完成还是差点。

<br>

前几天，又有人提到了memcpy这个问题。他也是说到对齐方式。我以为他解决了我的那个问题。经过一阵细问，其实他也没用考虑到这个细节。不过却激起了我的好奇。就是 glibc 下，到底是怎样实现的memcpy，是有什么特别方法吗？

<br>

为了搞清楚这个问题。当然的，只好自己写一段代码，一方面看看glibc 的 memcpy 到底性能怎样，另一方面也看看自己实现的memcpy 效果到底怎样。把测试代码发如下：
```
#include < stdio.h >
#include < sys/time.h >
#include < string.h >

int main(int argc, char ** argv)
{
   if(argc < 4) return -1;
   long size = 0;
   int off_src = 0;
   int off_dest = 0;
   sscanf(argv[1], "%ld", &size );
   sscanf(argv[2], "%d", &off_src );
   sscanf(argv[3], "%d", &off_dest );

   if(size < 1024*1024) printf("size=%.2fK\n", 1.*size/1024);
   if(size < 1L*1024*1024*1024) printf("size=%.2fM\n", 1.*size/1024/1024);
   if(size < 1L*1024*1024*1024*1024) printf("size=%.2fG\n", 1.*size/1024/1024/1024);

   char * dest = new char[size];
   char * src = new char[size];
   char * dest_1 = dest + off_dest; // 为了把源地址与目的地址的对齐彻底打乱
                                                // 注意 new 出来的地址一般是对齐的
   char * src_1 = src + off_src;

   int i = 0;
   for(i=0; i < size; i+= 500) src[i]=i; //先给源数据点真实数据吧。
   printf("src_0=%ld\tdest_0=%ld\n", long(src), long(dest));
   printf("src_1=%ld\tdest_1=%ld\n", long(src_1), long(dest_1));
  
   struct timeval tpstart,tpend;
   size -= 200;  // 下面的测试，每次copy的字节数并不严格一样，而是基本一样。这是为了方便。
                     // 因为这时候，并不影响测试结果。
                     // 这里减去200为了使得在调节了对齐方式后，下面的各个操作不会出core
   memcpy( dest_1, src_1, size ); // 这句是必要的。否则下面测试不公平。
                                            // 否则，第一遍给dest_1的内容赋值事，会发生缺页中断
                                            // 这里就是要消除这个对测试的影响
 
   // 1. memcpy。 原生 memcpy
   gettimeofday(&tpstart,NULL);
   memcpy( dest_1, src_1, size );
   gettimeofday(&tpend,NULL);
   printf("memcpy\t=\t%ld\n", (tpend.tv_sec-tpstart.tv_sec)*1000000+tpend.tv_usec-tpstart.tv_usec);

   // 2. long by long. 每次copy 一个 long，同时循环展开为每循环做8个
   gettimeofday(&tpstart,NULL);
   for(i=0; i < size; i=i+64)
   {
       *(long*)(dest_1+i)    = *(long*)(src_1+i);
       *(long*)(dest_1+i+8)  = *(long*)(src_1+i+8);
       *(long*)(dest_1+i+16) = *(long*)(src_1+i+16);
       *(long*)(dest_1+i+24) = *(long*)(src_1+i+24);
       *(long*)(dest_1+i+32) = *(long*)(src_1+i+32);
       *(long*)(dest_1+i+40) = *(long*)(src_1+i+40);
       *(long*)(dest_1+i+48) = *(long*)(src_1+i+48);
       *(long*)(dest_1+i+56) = *(long*)(src_1+i+56);
   }
   gettimeofday(&tpend,NULL);
   printf("long8\t=\t%ld\n", (tpend.tv_sec-tpstart.tv_sec)*1000000+tpend.tv_usec-tpstart.tv_usec);

   // 3. long by long. 每次copy 一个 long，同时循环展开为每循环做16个
   gettimeofday(&tpstart,NULL);
   for(i=0; i < size; i=i+128)
   {
       *(long*)(dest_1+i)    = *(long*)(src_1+i);
       *(long*)(dest_1+i+8)  = *(long*)(src_1+i+8);
       *(long*)(dest_1+i+16) = *(long*)(src_1+i+16);
       *(long*)(dest_1+i+24) = *(long*)(src_1+i+24);
       *(long*)(dest_1+i+32) = *(long*)(src_1+i+32);
       *(long*)(dest_1+i+40) = *(long*)(src_1+i+40);
       *(long*)(dest_1+i+48) = *(long*)(src_1+i+48);
       *(long*)(dest_1+i+56) = *(long*)(src_1+i+56);
       *(long*)(dest_1+i+64) = *(long*)(src_1+i+64);
       *(long*)(dest_1+i+72) = *(long*)(src_1+i+72);
       *(long*)(dest_1+i+80) = *(long*)(src_1+i+80);
       *(long*)(dest_1+i+88) = *(long*)(src_1+i+88);
       *(long*)(dest_1+i+96) = *(long*)(src_1+i+96);
       *(long*)(dest_1+i+104) = *(long*)(src_1+i+104);
       *(long*)(dest_1+i+112) = *(long*)(src_1+i+112);
       *(long*)(dest_1+i+120) = *(long*)(src_1+i+120);
   }
   gettimeofday(&tpend,NULL);
   printf("long16\t=\t%ld\n", (tpend.tv_sec-tpstart.tv_sec)*1000000+tpend.tv_usec-tpstart.tv_usec);

   // 4. long by long 每次copy 一个 long，不做循环展开
   gettimeofday(&tpstart,NULL);
   for(i=0; i < size; i=i+8)
   {
       *(long*)(dest_1+i)    = *(long*)(src_1+i);
   }
   gettimeofday(&tpend,NULL);
   printf("long\t=\t%ld\n", (tpend.tv_sec-tpstart.tv_sec)*1000000+tpend.tv_usec-tpstart.tv_usec);


   // 4. byte by byte。 每次copy 一个字节
   gettimeofday(&tpstart,NULL);
   while(size --) *dest_1++ = *src_1++;
   gettimeofday(&tpend,NULL);
   printf("byte\t=\t%ld\n", (tpend.tv_sec-tpstart.tv_sec)*1000000+tpend.tv_usec-tpstart.tv_usec);
   
   return 0;
}
```
贴上测试结果吧(加-O编译。发现，-O1和-O3，几乎没有差别。memcpy肯定是优化版的。这样 比才公平。)：
### 【1】、源与目的地址的不调节，从而总是对齐的：
```
[(10:24:43)-(0) ps1006:~/z]$./a.out  100000000 0 0
```
output:
```
size=95.37M
size=0.09G
src_0=182994124816    dest_0=182894120976
src_1=182994124816    dest_1=182894120976
memcpy  =      33483
long8   =      33582
long16  =      31572
long   =      34999
byte   =      302131
[(10:24:43)-(0) ps1006:~/z]$./a.out  100000000 0 0 
size=95.37M
size=0.09G
src_0=182994124816    dest_0=182894120976
src_1=182994124816    dest_1=182894120976
memcpy  =      31557
long8   =      31543
long16  =      30930
long   =      35045
byte   =      301763
[(10:24:44)-(0) ps1006:~/z]$./a.out  100000000 0 0 
size=95.37M
size=0.09G
src_0=182994124816    dest_0=182894120976
src_1=182994124816    dest_1=182894120976
memcpy  =      31479
long8   =      31487
long16  =      31021
long   =      35017
byte   =      302697
[(10:24:45)-(0) ps1006:~/z]$./a.out  100000000 0 0 
size=95.37M
size=0.09G
src_0=182994124816    dest_0=182894120976
src_1=182994124816    dest_1=182894120976
memcpy  =      31512
long8   =      31475
long16  =      31005
long   =      34994
byte   =      302115
```
从三遍执行看，memcpy确实是很快，但是其实和long8/long16/long这三种方式的copy速度差不多。另外，long8/long16/long这三种方式的速度差不多，但是long16稍微快过long8，long8快过long更多些。这附带说明了，循环展开，确实能有效提高性能。

而逐字节的copy方式，却性能查了一大截。

从上面，也可见，memcpy应该基本上就用的和long* 差不多的方式来实现的。glibc 我也不想分析了，从网上找了一篇分析文章：http://zhangzhibiao02005.blog.163.com/blog/static/3736782020116154291197/ ，大概看也确实那样。

### 【2】、令源与目的的开始地址，都没有良好对齐，且没法调整得同时对齐：
依然运行多遍，运行结果如下：
```
[(10:24:54)-(0) ps1006:~/z]$./a.out  100000000 1 3
```
output:
```
size=95.37M
size=0.09G
src_0=182994124816    dest_0=182894120976
src_1=182994124817    dest_1=182894120979
memcpy  =      32125
long8   =      33898
long16  =      33037
long   =      37265
byte   =      302466
[(10:26:34)-(0) ps1006:~/z]$./a.out  100000000 1 3
size=95.37M
size=0.09G
src_0=182994124816    dest_0=182894120976
src_1=182994124817    dest_1=182894120979
memcpy  =      32452
long8   =      34286
long16  =      33207
long   =      37532
byte   =      303473
[(10:26:35)-(0) ps1006:~/z]$./a.out  100000000 1 3
size=95.37M
size=0.09G
src_0=182994124816    dest_0=182894120976
src_1=182994124817    dest_1=182894120979
memcpy  =      32285
long8   =      34269
long16  =      33157
long   =      37383
byte   =      303901
[(10:26:36)-(0) ps1006:~/z]$./a.out  100000000 1 3
size=95.37M
size=0.09G
src_0=182994124816    dest_0=182894120976
src_1=182994124817    dest_1=182894120979
memcpy  =      34454
long8   =      35266
long16  =      33261
long   =      36865
byte   =      299786
```
令人惊奇的发现，其实竟然对齐与否几乎没有产生影响！！！

不过对于对10次的数据求平均值，发现还是稍微有点差别：
```
diff_memory = (321895 - 318267)/ 318267. = 0.0113992339765 = 1.1%
diff_long8     =  (339473 - 318867)/ 318867. = 0.0646225542311 = 6.4%
diff_long16   =  (328687 - 312946)/ 312946. = 0.0502994126782 = 5% 
diff_long      =  (371891 - 351829)/ 351829. = 0.0570220192196 = 5.7%
diff_byte       = (3020652 - 3022575)/ 3022575. = -0.00063621250093 = - 0.06%(还些微上升。其实就是不变)
```
从这个看，一方面说明对齐，确实是有好处，还有就是，靠，memcpy果然实现的牛逼！！

2014-07-20
