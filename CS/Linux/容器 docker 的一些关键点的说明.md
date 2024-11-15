# docker 的一些关键点的说明

2017-03-17 

docker 和宿主机共享 os kernel；docker的os kernel version 由宿主机决定。

在mac os和windows上运行docker的秘密：Boot2docker。就是通过这个叫做boot2docker的玩意启动了一个虚拟linux kernel，所有的docker容器都跑在这个kernel上。

以上来自：https://zhuanlan.zhihu.com/p/22382728

大约说，docker 只是把内核外的其他文件层次结构，以及相关文件，放到了镜像里。
