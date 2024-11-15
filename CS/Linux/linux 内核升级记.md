# linux 内核升级记
2014-01-01

心血来潮，忽然晚上想把虚拟机上的linux的内核升级下。原内核是2.6.9.34，就想用源代码的方式升级到2.6.32版本。
万分曲折，最后好不容易算是成功了吧。赶快把过程记载下来，备忘。过程也是在网上找的：

1. 去 www.kernel.org 下载想要升级到的内核源代码。
2. copy 到 /usr/src下，然后解压。多说一句，下载下来的是tar.xz包，需要安装xz解压程序的。
3. 解压出源代码后，执行 ```make menuconfig```,在图形界面下选择要编译进去的功能。
4. ```make； make modules；make modules_install; make install；```（我是这样执行的；大约如此；具体可看make help） reboot
5. ok

说下遇到的问题：
一直到4 其实都很成功，但是到了5后，发现启动不起来，kernel panic了，屏幕上打印：
```
Reading all physical volumes. This may take a while...
No volume groups found
Volume group "VolGroup00" not found
ERROR: /bin/lvm exited abnormally! (pid 342)
.....
Kernel panic - not syncing: Attempted to kill init!
```
各种查询原因：
1. 有的说是 initrd.img 不对，需要重新生成；
2. 有的说是vmware虚拟机导致的bug，需要改内核代码；
3. 有的说是LVM 虚拟卷这个模块没有编译进去。

我只好一一试：
- 对于（1），想想不应该，编译最后最新生成，我自己再生成不也那样吗？后来看到，似乎（1）可以解决的是非升级导致的该问题；
- 对于（2），只好改了源代码，编译后发现还是有问题，再一想不对啊，我用的是virtualbox，又不是vmware；
- 对于（3），实在找不到哪里开启LVM，只好把所有LVM相关的全都打开，还是通不过。
- 最后，看到了第四个（4）：在make menuconfig的时候，要在基本设置里吧```enable deprecated sysfs features to support old userspace too``` 这个打开（ http://wenku.baidu.com/link?url=76erejLHbCPlvin4aVcdozNrFW_esfr9R8Gm-mD4iRYmIamZLw-ShBAEBGbyoF1C-ehALsXe12xpohxfs8xx8tfWunZ0s-rfFyYEyv4_NFS ）。这个是为了兼容旧的。最后发现，这个OK，可以不一样的启动了（话说好几百个配置也不止，哪里能知道需要把这个打开？）

但是却发现，只是不一样的错误了，结果还是 kernel panic。但是，这一次屏幕打印的内容却着实令人更加郁闷啊：
```
2 logical volume(s) in Volume Group"VolGroup00" now active.
。。。。
kernel panic - not syncing: attempted kill init
```

   刚才是找不到 group VolGroup00, 这下可倒好，一下子找到了两个！！
   没办法，继续搜索答案吧。中间的再次曲折省去，最后找到了这个：
    http://www.linuxquestions.org/questions/linux-kernel-70/2-logical-volumes-in-volume-group-volgroup00-now-active-633607/ ,
   按着/etc/selinux/config 把SELINUX = enforcing 改成 SELINUX = permissive.最后reboot，一切ok。
   为什么这样就行？明天看下原因。

   第二天补记： 
   
   在grub menu.list文件的相应行行尾追加 selinux=0 也能搞定。查看了下selinux是什么，selinux大概的是关于权限控制的一个东西；上面所说的解决方案其实是关闭或弱化该权限控制从而ok的。【为什么改grub后可行，原因是其实只是改了grub传递给内核的启动参数。见http://blog.csdn.net/zhongyou2009/article/details/4764986。传递的这些个参数都是grub不管的，只传递】


【补记】

安装完后，应该记得安装下新内核的头文件。```cd src_dir && make headers_install``` 就把源码根目录下的usr/include 里的东西安装到/usr/include了(参考h ttp://blog.chinaunix.net/uid-24780853-id-3301606.html)。特别注意，不能用src_dir/include/下的。
