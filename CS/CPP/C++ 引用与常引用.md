# C++ 引用与常引用

复制构造函数的参数是需要写成引用类型的(类型转化构造的时候，也往往)，但是往往需要写成const常引用。虽然用非常引用好多时候也可以工作，但是有些情况下会不行：

当源对象是个常对象（比如源对象是这样定义的临时对象：className(arg1)）的时候，如果没有const 那么就会不工作。

实际上，一般引用与常引用的差别还不止于此。

实际上，**在函数(包括成员函数)的重载中，常引用与非常引用是可以用来区分重载的。看例子：**
```
 int ff(int &i) { return i; }
 int ff(const int &i) { return i+11; }
 
 printf("%d\n", ff(11) );  // 输出 22， 则调用到第2个ff。这个好理解，若无第二个，则编译不过
 int x=11;
 printf("%d\n", ff(x) );  // 输出 11， 说明调用到了第一个。若无第一个ff，则输出22
```
当然的，在复制构造函数中当然也是类似表现了。实际上，经过实验，发现也确实这样。
