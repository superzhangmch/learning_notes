# gdb 加载core时如何找到动态链接库

大概的说，在某个地方（core 文件中？），存在着一个已经加载的so库的链表（struct link_map。不管是启动时加载，还是dlopen加载），因此只要设法找到这个后，就可以把所有so都打印出来了，包括每个库的基地址。
具体的没有看清。

参考：http://blog.csdn.net/_xiao/article/details/23177577 等等
