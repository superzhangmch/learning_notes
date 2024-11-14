# linux 启动过程与init

linux启动过程大概是这样的：

### 1. 内核加载器 grub 把 vmlinuz 与 initrd 加载进内核。同时grub会根据配置文件给内核传递一些内核参数。
下面的grub配置中：
```
title linux 2.6.32.61
root (hd0,0)
kernel /vmlinuz-2.6.32.61 ro root=/dev/sda1 rhgb quiet selinux=0
initrd /initrd-2.6.32.61.img
```

“```ro root=/dev/sda1 rhgb quiet selinux=0```”就是传给内核的内核参数。

加载器只是把 kernel 与 initrd 加载进内存而已，具体initrd被怎么处置，是 kernel的事。

### 2. vmlinuz 启动，也就是真正的内核启动
### 3. 内核运行 initrd 里的某些东西，运行完后就会开始启动 init 进程
所以需要 initrd 因为实际的硬件环境差别很大，如果不引入initrd的话，内核文件也就是vmlinuxz将会很大；引入initrd后可以把一些驱动之类的放到里面。

### 4. 启动init：比如从 inittab 读取启动级别，然后运行 /etc/rc.N 中的脚本等等；启动getty等等。
这时候已经在用户空间了。开始运行init之后，与内核就没有多少关系了。当linux启动的时候，会需要不少时间，其实几乎所有时间都用在init开始执行后这个阶段了。

----

对于linux启动的介绍书或者资料，好多时候，都在init的启动上介绍了好多，总会把人搞晕，以为init就是内核的一部分呢。

实际上呢，init并没有什么奇特的。你可以写一个不依赖于so动态库的叫做 init 的程序（比如死循环一直打印个hello world，gcc -static -o init hello.c编译），然后放到/sbin/下，重启动后就会发现它在工作了。

当然，这样写出的init实在没什么好玩的。可以下载安装busybox。然后你发现你可以在一张空白盘上只用vmlinuz、initrd、busybox（busybox有个特点就是它支持非常多的unix命令，把它命名（软链也一样效果）为相应的命令名，它就表现的就像就是这个命令(mv busybox awk,然后busybox就想完全就是awk命令)，因此busybox可以用来通过软链扩展出一堆unix命令。）这三个文件，另外建立几个相关的文件夹以及一批软链，就可以把最简单的linux跑起来了。

<br>

我正好就做了这样的试验，把过程简述下来。备忘。

下载busybox后，make menuconfig,然后make，然后make install，就会在 busybox 根目录下生成一个叫 _install 的按照一般 linux 命令组织方式放好的文件夹：有bin,sbin,usr/bin,usr/sbin 等，有各种busybox支持的命令，都是软链到 bin/busybox 的。

在一个空白盘(当然已经安装好grub了)里放置好 vmlinuz，initrd，把 _install 里的东西都copy到这个盘里。因为busybox支持的init 和一般的init一样的，那需要设置 inittab等等，所以我就自己写了一个最简单的init: init里 execl 运行sh命令(这个sh也是busybox提供的支持)。

启动后，就发现已经进入shell了。但是发现 top、ps 命令不能用。原来是缺少proc文件夹(注意这时候只有usr,bin,sbin等文件夹，sys，proc，dev等都没有呢)，而这两个命令需要读取proc。所以一开始就要试这两个命令因为如果他们有显示，那么说明系统确实都启动起来了（在只需要几个文件的基础上）。然后建立proc文件夹并把proc mount(busybox 提供的mount功能)出来： mount proc /proc -t proc。再试，ps、top都工作起来了（这也说明一个空文件夹，只要把procfs mount 出来，里面那一大堆东西自然就有了）。主意这时候，dev、etc等文件夹都还没有建立。顺势用同样方式把/sys 也弄了出来，也是一mount sysfs后，/sys后就有了那一堆东西。

但是，这时候发现没法把别的盘mount起来。这个容易理解，因为没有/dev嘛。然后建立/dev后重启动，发现/dev下已经有各种的设备文件了(或者自己 mknod出来，一样)。然后mount别的盘什么的，都是ok的了。

这时候，有了/proc,/sys,/dev 但是还没有/etc呢。没有建立/etc，当然更没有建立/etc/inittab，/etc/init.d等等，所以，正常功能的init还是没法拿来用。但是这已经是一个正在工作的linux系统了。另外，用户权限验证的功能（实际上，用户权限控制这块，只是靠用户空间的程序维护的；在内核层面，只知道对比下权限位与用户id是否合，合则执行，不合则拒绝）也是没有的，所有总是有root权限。

要一步步这样子手工构建出一个实际可用的linux系统，当然需要把/dev/inittab,/dev/fstab,/dev/init.d等等都建立起来，并用实际的原生init程序。但是作为让linux运行起来，上面所述的已经够了。

<br>

【总结】：
- init程序，自己随便写的都行。附带说一句，系统中默认的那个init，叫做sysV init。
- /proc,/sys,/dev/,/etc存在与否，不影响一个最简单系统的运行。只是没有/proc没法知道系统的运行信息，从而不能运行top等;没有/dev没法通过设备文件mount硬盘，没法通过设备文件在用户空间与设备交互而已；没有/etc只是对于依赖于/etc的一些用户态程序没法正常使用而已。
也即是说一些系统文件夹存在与否，只是影响到使用到它们的用户态程序而已。

<br>

附：
http://www.cnblogs.com/cndc/archive/2012/05/03/2480882.html ，讲自制一个linux系统。但是为了让linux运行起来，其实都不用像里面说的那样做那么多。

2014-04-12
