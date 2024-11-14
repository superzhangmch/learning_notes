# so 动态链接库：用环境变量 LD_LIBRARY_PATH 指定 so 加载地址

如果运行程序 ``` ./bin_to_run ```的时候提示找不到某个so，即报错
```
./bin_to_run: error while loading shared libraries: libXXXX.so.4: cannot open shared object file: No such file or directory
```
，而你知道这个 .so 其实是存在于什么地方的，这个时候就需要用到 LD_LIBRARY_PATH 环境变量了。 

----

只需要把搜索路径（如果多个用":"分割）赋给 ``` LD_LIBRARY_PATH ```，并export出去， 问题就解决了:
```
export LD_LIBRARY_PATH=$PATH
./bin_to_run
```
或者不 export，而是在命令行直接把 LD_LIBRARY_PATH 传进去：
```
LD_LIBRARY_PATH=$PATH ./bin_to_run
```
