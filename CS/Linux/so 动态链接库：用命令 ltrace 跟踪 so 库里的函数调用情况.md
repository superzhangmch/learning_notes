# ltrace：跟踪so库里的函数调用情况

ltrace 用于跟踪一个程序的共享so lib 库的函数调用。
一般用法是： ```ltrace ./cmd_to_run```

比如有一个./o, 连接了一个 so 库里的test函数，那么：
```
$ltrace ./o
```
ouput：
```
__libc_start_main(0x4006c8, 1, 0x7fbffff818, 0x400700, 0x400760  
_Z4testv(1, 0x7fbffff818, 0x7fbffff828, 32, 0x7fbffff770) = 20 
printf("aa=%lf, test=%d\n", ...aa=1.200000, test=20 ) = 21 
+++ exited (status 0) +++
```
可以看到test 函数的调用已经被trace出来了（当然，编译的时候函数名 test 被改写成了 _Z4testv）。

ltrace 只能用来跟踪共享so lib 库的函数掉用，而对于静态库则没有办法。

ltrace有一些选项比如：
```
-S：把系统调用也显示出来
-c：Count time and calls for each library call and report a summary on program exit.
-p：pid Attach to the process with the process ID pid and begin tracing.
-T: Show  the  time  spent inside each call.
```
ltrace 的实现是基于程序的一些链接、符号等信息，再结合ptrace来实现的（从-p选项也可以看出来）。
