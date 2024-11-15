# man: 怎样man新安装的程序的man手册

源码安装的程序/命令往往会附带一个share文件夹，这里面往往放就放有该程序/命令的配套的man手册。一般的share文件夹布局是这样的：
```
share/man/man1/manfiles, share/man/man2/manfiles,..., share/man/manN/manfiles
```
这里的 manN(N是个数字)表示的是对应man手册的章节号（一般的，1表示命令，2表示系统调用，3表示库函数，等等），也就是一般使用man命令时的章节号（比如 man 2 open，就是查看系统调用open的man手册）。


对于系统里已经安装的命令，man手册已经是安装好的了，直接man可以看到man手册。对于新安装的程序/命令，怎样使用这附送的man手册呢？可以有多种方式：

1. export MANPATH=$PATHPATH:命令的MAN路径，然后就可以像正常使用man那样man新安装的命令/程序了。
2. man的时候制定搜索路径：
```
man -M 命令的MAN路径 命令
```
比如 
```
man -M /home/path1/path2/share/man  cmd_name
```
  这时候， cmd_name 和 -M 之间还可以夹有man章节号，则man命令会自动去share/man/man*相应的目录下寻找。

3. man 命令的MAN路径/man手册文件. 比如 
```
man /home/path1/path2/share/man/cmd_man_file_name
```
