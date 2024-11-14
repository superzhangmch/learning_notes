#  库函数 malloc 返回地址的字节对齐

对于系统自带的malloc，man手册说了：
> For  calloc()  and malloc(), the value returned is a pointer to the allocated memory, which is suitably aligned for any kind of variable, or NULL if the request fails.

既然 for any kind of variable， 从这个看，x86+linux+gcc下， sizeof(long double) == 16, 因此可以解释为什么这种情况下的malloc返回的地址会是16字节对齐的吧。

另外，看到SSE指令要求内存地址是16字节对齐的，而malloc 返回的地址需要可以做任何事，那么因此也需要16字节对齐吧。

<br>

这里有 intel 关于alignment 的解释：

https://software.intel.com/en-us/articles/data-alignment-when-migrating-to-64-bit-intel-architecture
摘抄如下：

> **Alignment of Data Items**
> 
> Developers who undertake the migration to the 64-bit operating environment will discover that a small set of issues tend to recur most frequently, on both Win64* and Linux* platforms.
>
> 
> One of these is the alignment of data items – their location in memory in relation to addresses that are multiples of four, eight or 16 bytes. Under the 16-bit Intel architecture, data alignment had little effect on performance, and its use was entirely optional. Under IA-32, aligning data correctly can be an important optimization, although its use is still optional with a very few exceptions, where correct alignment is mandatory. The 64-bit environment, however, imposes more-stringent requirements on data items. Misaligned objects cause program exceptions. For an item to be aligned properly, it must fulfill the requirements imposed by 64-bit Intel architecture (discussed shortly), plus those of the linker used to build the application.
>
> The fundamental rule of data alignment is that the safest (and most widely supported) approach relies on what Intel terms "the natural boundaries." Those are the ones that occur when you round up the size of a data item to the next largest size of two, four, eight or 16 bytes. For example, a 10-byte float should be aligned on a 16-byte address, whereas 64-bit integers should be aligned to an eight-byte address. Because this is a 64-bit architecture, pointer sizes are all eight bytes wide, and so they too should align on eight-byte boundaries.
>
> It is recommended that all structures larger than 16 bytes align on 16-byte boundaries. In general, for the best performance, align data as follows:
> 
> - Align 8-bit data at any address
> - Align 16-bit data to be contained within an aligned four-byte word
> - Align 32-bit data so that its base address is a multiple of four
> -Align 64-bit data so that its base address is a multiple of eight
> -Align 80-bit data so that its base address is a multiple of sixteen
> -Align 128-bit data so that its base address is a multiple of sixteen
>
> 
> A 64-byte or greater data structure or array should be aligned so that its base address is a multiple of 64. Sorting data in decreasing size order is one heuristic for assisting with natural alignment. As long as 16-byte boundaries (and cache lines) are never crossed, natural alignment is not strictly necessary, although it is an easy way to enforce adherence to general alignment recommendations.
>
> 
> Aligning data correctly within structures can cause data bloat (due to the padding necessary to place fields correctly), so where necessary and possible, it is useful to reorganize structures so that fields that require the widest alignment are first in the structure. More on solving this problem appears in the article "Preparing Code for the IA-64 Architecture (Code Clean)."
