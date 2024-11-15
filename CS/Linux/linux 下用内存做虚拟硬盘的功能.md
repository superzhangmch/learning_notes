# linux 下用内存做虚拟硬盘的功能

2014-04-06

linux 下如果需要用内存虚拟出一块存储，从而提高文件读写速度，可以通过通过 ramdisk、tmpfs、ramfs三种方式实现。

/dev/ramN(N是数字)这些就是关于 ramdisk的。/dev/ramN 这些的属于虚拟设备，所以用的时候需要像真实设备一样 tune2fs 格式化，然后才能使用： ```mke2fs -m 0 /dev/ram0```。然后就可以正常 mount了。
可以参看： http://blog.csdn.net/hshl1214/article/details/8513972

而 tmpfs 则是可以直接加载使用的虚拟文件系统，并不关联/dev/下面可见的设备。查看/etc/fstab 可能就会发现/dev/shm 往往就是tmpfs 文件系统的。读写/dev/shm 里面的文件会超快，因为直接用的是内存。

用下面的命令可以加载一个tmpfs 文件系统：size=2m 可以换成其他的大小，/root/aa/可以换成其他的加载点：
```
mount -t tmpfs -o size=2m tmpfs /root/aa/
```
要卸载则用：
```
umount /root/aa
```

Ramfs 和 tmpfs 很类似，也是一个虚拟文件系统，并不关联/dev/下面可见的设备。用的时候，直接mount就是了：```mount -t ramfs ramfs /testRAM```。
但是和tmpfs不一样的是，ramfs是工作在直接的RAM上，也就是物理内存上，而tmpfs工作在虚拟内存上，因此tmpfs中的文件可能交换到交换分区中去。一般性使用，忽略这个差别吧。

【参考】：
- http://leeon.me/a/linux-ramdisk-tmpfs-ramfs
- http://www.linuxidc.com/Linux/2012-11/74356.htm
- http://blog.csdn.net/heyutao007/article/details/7051269
- http://blog.csdn.net/hshl1214/article/details/8513972
