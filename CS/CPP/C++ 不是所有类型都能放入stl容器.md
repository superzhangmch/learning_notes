# C++：不是所有类型都能放入stl容器

本文就以stl中的vector 为例来叙说吧，其他stl container 也是大体一样的。
 
我们知道，只要有一个类型T，就可以以 T 来这样定义：std:vector。  
再想想，C++ 中的类型一般是怎样子的：一般是由 int char 等内置类型、struct/class、函数类型、*、[]等等，各种组合出来的。往往会看起来很复杂，那么没关系，就typedef下，就 typedef 成 T 吧。  
然后，我们就开始 std:vector 了。

确实，这样基本都是没啥问题的，对于这样的定义，往往也能编译通过。但是在要具体使用这个vector 的时候，有时候却发现怎么样都不能 push_back 元素！！  
这怎么回事？！各种探寻，但就是没法push 元素。

其实问题**出在 std:vector 这句上。直接说吧，正如标题所言，实际上，这个 T 还真不是随便什么类型都行**！！也就是说，其实stl 容器并不能容纳所有类型！  
那么不能容纳哪些类型呢？  
不能容纳的类型是：**数组类型**。  
解说下什么是数组类型：假如有个任意的C++类型T1，那么 typedef T1 T[5]；一下，这样定义出的T就是数组类型。当然5可以换成别的数字。

所以：std::vector或者 std::vector 都是不行的。一到了push_back 的时候，就会编译不通了。

代码：
```
#include< vector >
using namespace std;
class a{
       public:
       int data;
};
int main() 
{
       vector< a[4] > x;

       a aa[4];
       //x.push_back(aa); // 有这句，编译不过，没有的话，能过。无论如何，说明不可这样用vector
       return 0;
}
```
或者更简单些，把a用int代替。也一样。  
从提示的错误：ISO C++ forbids initialization in array new 看，问题大概是vector 内部会对T 做这样的操作： new T(xxx); 而 T ==T1[5]那么就是 new T1[5](xxx); 而这时不允许的。
