# CPU也可能故障而计算出错：slienterror、SilentDataCorruption，不知觉间硬件错误

对于内存，是有可能不知不觉发生bit翻转的，所幸有相应的检验或纠错码。

实际上，各个硬件都是有可能有类似问题的。特别是CPU。

谷歌spanner论文中，关于truetime的实现中，一个假设是clcok drift 不会超过每秒0.2ms。如果超过怎么办？google的理由是：时钟比cpu可靠多了，故障率只有cpu六分之一。如果是cpu直接挂掉的故障，在分布式系统里并不算什么问题，可以忽略。因此猜测这里 google 给出的应该是这类 slient error 问题。

参：https://support.google.com/cloud/answer/10759085?hl=en：
> Silent Data Corruption (SDC), sometimes referred to as Silent Data Error (SDE), is an industry-wide issue impacting not only long-protected memory, 
> storage, and networking, but also computer CPUs. As with software issues, hardware-induced SDC can contribute to data loss and corruption. An SDC 
> occurs when an impacted CPU inadvertently causes errors in the data it processes. For example, an impacted CPU might miscalculate data (i.e., 1+1=3). 
> There may be no indication of these computational errors unless the software systematically checks for errors.
cpu 都可能因此把1+1算出3。
