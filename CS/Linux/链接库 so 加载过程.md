# 链接库 so 加载过程

除非用 ```gcc -static ``` 方式编译出一个独立 bin 程序，否则，都会链接一些 .so。分析了下，大概过程是这样的：

首先程序被执行到肯定需要执行到execve系统调用，该系统调用会做 “#!”判断并最终调用到实际的可执行程序。execve在执行可执行程序的时候，会判断bin程序的类型，比如是ELF还是别的。

对于ELF来说内核会从ELF的.interp段中读到so 动态加载器，一般是ld.so；然后加载之。然后由这个ld.so来把所有需要的so都加载起来。所以关键就是ld.so，具体可以 ```man ld.so```。所有与so相关的环境变量，比如LD_LIBRARY,LD_DEBUG,以及加载次序等，都是与ld.so相关的。ld.so本身是 glibc的一部分。

也就是说程序启动的时候，会有某个阶段由ld.so接管，用来加载so或做一些别的事的。所以，运行“LD_DEBUG=help ls”的时候，可以做到ls根本没有执行，反而只是打印了LD_DEBUG的帮助信息。

关于.interp段：

readelf 会看到一个程序一般都有一个.interp端，这里指定的就是动态加载器（/lib64/ld-linux-x86-64.so.2），内核正式从这里读到的。

### 【附】
- ELF在Linux下的加载过程： http://blog.csdn.net/joker0910/article/details/7686836
- Linux 动态库剖析: http://www.ibm.com/developerworks/cn/linux/l-dynamic-libraries/index.html
- ld.so 分析: http://blog.csdn.net/maimang1001/article/details/9429941
- http://stackoverflow.com/questions/5130654/when-how-does-linux-load-shared-libraries-into-address-space
  
摘录部分：

> Libraries are loaded by ld.so (dynamic linker or run-time linker aka rtld, ld-linux.so.2 or ld-linux.so.* in case of Linux; part of glibc). It is declared as "interpreter" (INTERP; .interp section) of all dynamic linked ELF binaries. So, when you start program, Linux will start an ld.so (load into memory and jump to its entry point), then ld.so will load your program into memory, prepare it and then run it. You can also start dynamic program with
>
> 
> /lib/ld-linux.so.2 ./your_program your_prog_params
>
> ld.so does an actual open and mmap of all needed ELF files, both ELF file of your program and ELF files of all neeeded libraries. Also, it fills GOT and PLT tables and does relocations resolving (it writes addresses of functions from libraries to call sites, in many cases with indirect calls).
>
> 
> The typical load address of some library you can get with ldd utility. It is actually a bash script, which sets a debug environment variable of ld.so (actually LD_TRACE_LOADED_OBJECTS=1 in case of glibc's rtld) and starts a program. You even can also do it yourself without needs of the script, e.g. with using bash easy changing of environment variables for single run:
>
> 
> LD_TRACE_LOADED_OBJECTS=1 /bin/echo
>
> The ld.so will see this variable and will resolve all needed libraries and print load addresses of them. But with this variable set, ld.so will not actually start a program (not sure about static constructors of program or libraries). If the ASLR feature is disabled, load address will be the same most times. Modern Linuxes often has ASLR enabled, so to disable it, use echo 0 | sudo tee /proc/sys/kernel/randomize_va_space.
>
> You can find offset of system function inside the libc.so with nm utility from binutils. I think, you should use nm -D /lib/libc.so or objdump -T /lib/libc.so and grep output.



