# so 动态链接库: 用命令 ldd 查看程序运行需要加载那些 so 共享库

用 ldd 命令可以查看命令需要加载那些so共享库。但是不能查看静态链接库。而且对于用dopen方式加载的动态库也不用用ldd 查看。

一个命令 ./bin 被编译出来的时候，假设需要加载A、B、C、D、E五个动态库，那么这五个库可以用
```
ldd ./bin
```
来找出来。但是可能只有某三个库比如说C、D、E才是真正运行时候必须（或者不是直接依赖）的，这时候可以用 -u 选项，也就是这样：```ldd -u ./bin ```，把其实本来用不着的共享库找出来。

#### 【例子】
run: 
```
$ldd ./o
```
output:
```
 libtmp.so (0x0000002a95557000) 
 libstdc++.so.6 => /usr/lib64/libstdc++.so.6 (0x000000302d300000) 
 libm.so.6 => /lib64/tls/libm.so.6 (0x000000302b400000) 
 libgcc_s.so.1 => /lib64/libgcc_s.so.1 (0x000000302c800000) 
 libc.so.6 => /lib64/tls/libc.so.6 (0x000000302af00000) 
 /lib64/ld-linux-x86-64.so.2 (0x000000302ad00000)
```

run:
```
$ldd -u ./o
```
output:
```
Unused direct dependencies:
   libtmp.so
  /usr/lib64/libstdc++.so.6
  /lib64/tls/libm.so.6
  /lib64/libgcc_s.so.1
  /lib64/tls/libc.so.6
```
注意以上的除了libtmp.so是编译的时候特别编译进去的外，其他的都是自动连接进去的。但是 ldd 把他们都找了出来。

#### 【Note】
- 如果编译一个程序的时候，把无关的一个共享so链接库也链接了进去，那么在程序启动的时候，是会加载这个so的，哪怕用不到。如果这时候这个so找不到，甚至会导致这个程序启动失败。
- 要想编译的时候把无用的so排除出去，用"```g++ -Wl,--as-needed ...```"。
- 除了用 ldd 来查看启动的时候会加载的so，还可以 ```export LD_DEBUG=libs```, 然后执行要查看so的命令，然后就可以看到so加载信息了。（可以看这里：http://www.linuxidc.com/Linux/2010-12/30726.htm ）

#### 【附网络资料】
http://linux.chinaunix.net/techdoc/system/2008/10/13/1037839.shtml , 摘录：
- 首先ldd不是一个可执行程序，而只是一个shell脚本
- ldd 能够显示可执行模块的 dependency，其原理是通过设置一系列的环境变量，如下： ``` LD_TRACE_LOADED_OBJECTS、LD_WARN、LD_BIND_NOW、LD_LIBRARY_VERSION、LD_VERBOSE ```等。当
```LD_TRACE_LOADED_OBJECTS``` 环境变量不为空时，任何可执行程序在运行时，它都会只显示模块的 dependency，而程序并不真正执行。要不你可以在shell终端测试一下，如下：
  - (1) ```export LD_TRACE_LOADED_OBJECTS=1```
  - (2) 再执行任何的程序，如 ```ls``` 等，看看程序的运行结果
- ldd显示可执行模块的dependency的工作原理，其实质是通过 ```ld-linux.so```（elf动态库的装载器）来实现的。我们知道，ld-linux.so 模块会先于executable模块程序工作，并获得控制权，因此当上述的那些环境变量被设置时，ld-linux.so选择了显示可执行模块的dependency。
- 实际上可以直接执行ld-linux.so模块，如：```/lib/ld-linux.so.2 --list program```（这相当于```ldd program```）

