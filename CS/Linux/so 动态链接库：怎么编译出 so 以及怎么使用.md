# so 动态链接库：怎么编译出 so 以及怎么使用

so的编译一般是通过命令： ```gcc -shared -fPIC -o xxx.so xxx xxx xxx ... ```，注意用 “-shared -fPIC” 参数选项。
  
编译完成后，如果某程序要用到这个so：

### 1. 静态联编

如果是通过 -Lxxx -lXXX 方式指定的，那么就按照so的搜索规则来找so，需要的时候设置```LD_LIBRARY_PATH```环境变量就是了。可以用``` readelf ```来查看具体so的路径被指定成了什么。注意so名字需要是 libXXX.so 形式。

如果没用-L -l方式，而是直接指定路径联编（```gcc a.cpp /aa/bb/cc/libX.so ``` 这样），LD_LIBRARY_PATH经试验对绝对路径和具体相对路径(比如./)的情况没效。实际运行的时候会在相应绝对或相对路径下寻找so文件，找不到则报错。

联编后的生成文件并没有把so包括进去，运行的时候，是由系统自动加载（mmap方式）。

C++调用C++写的so的时候，不需要 ```extern "C"```.

### 2. 动态调用：用 dlopen / dlsym等

用dlopen的时候需要联编 dl 库（ldd看到所用机器上是libdl.so.2）。

用dlopen方式加载使用so，本质上仍然是用mmap系统调用，只是只有在使用到这个so的时候，mmap才会调用到。可以通过查看 /proc/PID/maps看到这点。

dlopen 方式使用 so，不能被ldd看到，也不能被 LD_DEBUG=libs 所看到。

对于c程序产出的so，dlsym调用so里的函数的时候，非常容易。对于so 里的 c++ 函数，就没有那么简单了，因为c++编译的时候，会把函数名字变得千奇百怪,所以需要用extern "C" 把可输出的函数包起来。

### 【附】
C++中怎样用 dlopen 动态加载so: 答案是用extern "C"。

即使是C++中的普通的普通的C函数也需要extern "C"一下。而对于成员函数这样的，一般需要包装出一个C函数，像这样：
```
extern "C" void GetName(std::string &str)
{
   ModuleBasic::GetName(str);
}
```
