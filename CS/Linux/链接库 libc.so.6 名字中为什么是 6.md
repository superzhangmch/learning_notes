# 链接库 libc.so.6 名字中为什么是 6

据wikipedia：
> In the early 1990s, the developers of the Linux kernel forked glibc. Their fork, called "Linux libc", was maintained separately for years and released versions 2 through 5.
>
> When FSF released glibc 2.0 in January 1997, it had much more complete POSIX standards compliance, better internationalisation and multilingual function, IPv6capability, 64-bit data access, facilities for multithreaded applications, future version compatibility, and the code was more portable.[9] At this point, the Linux kernel developers discontinued their fork and returned to using FSF's glibc.[10]
>
> The last used version of Linux libc used the internal name (soname) libc.so.5. Following on from this, glibc 2.x on Linux uses the soname libc.so.6[11] (Alphaand IA64 architectures now use libc.so.6.1, instead). The soname is often abbreviated as libc6 (for example in the package name in Debian) following the normal conventions for libraries.

因此可见libc.so.1~5用的是fork出来的glibc，而libc.so.6则是原本的glibc。这里的6当然有版本的意思，但是这个版本是对应于好多个glibc 版本的。只要用的是glibc的libc，看样子这个6会一直保留下去，那么这样说这个6就当做是固定的吧。

另外大概看了下LSB(给linux整体环境定的标准)，标准就要求应该用6,而不是别的。

上面的wiki提到了soname, 下次看是怎么的一个东西。

2014-01-28
