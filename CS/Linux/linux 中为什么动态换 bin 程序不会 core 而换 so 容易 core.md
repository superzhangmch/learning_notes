# linux 中为什么动态换 bin 程序不会 core 而换 so 容易 core

Linux中， 如果一个程序正在运行中，那么要动态替换程序，```cp new old```, 会发现报“text file busy"。用 strace 查看cp命令输出，会发现报：open old的时候，用了 O_WRONLY|O_TRUNC，open 返回 ETXTBSY (Text file busy)。也就是说，这时候这个文件已经是不可更改的了。如果用 cp -rf 复制，检验下又会发现，其实复制得到的文件的文件虽然还是原来的名字，但是 inode 已经变了。也就是说，cp -rf 其实还是没有真正的覆盖成功。

这些都是为什么呢？

这首先不得不说下linux中二进制文件执行的时候的延迟加载。也就是说如果一个bin文件并不会一次性加载进内存，而是按需逐步加载的。为了防止bin文件修改后动态按需load的时候出错，所以内核系统就会把文件锁死，使得不能随便更改。

这解释了为什么会“text file busy”。同时也说明了，rm + cp方式动态替换程序的时候，或者动态删除 bin 的时候，“延迟加载”不会导致程序出core。因为文件的inode还没有释放，等于说原文件还存在。

对于 .so 动态库文件，动态覆盖容易导致出core，是因为系统没有对so作特殊保护，不会"text file busy"之故。
