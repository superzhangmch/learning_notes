# C++中的静态变量小结 

我们知道C++中的静态变量：类的静态数据成员，或者函数内的静态变量，都是存储在静态存储区。和全局变量的存放地方是一样的。从这个角度来说，静态变量和全局变量的主要差别在于访问权限的不同。全局变量到处可见，静态变量，只有在适当的地方才可见。

全局变量是在main函数进入之前就初始化的。而**函数内的静态变量是在函数的*第一次调用*的时候，才初始化**的；虽然如此，但是是早已经分配好的空间，这样才能保证函数调用结束后不丢数据。对于**类的静态数据成员，却是和全局变量一样，在main函数*之前*就初始化好**了。

实例代码如下：
```
#include< stdio.h >
class tt {
   public:
      tt(){printf("xxxx\n");}
};
class ttt {
   public:
      ttt(){printf("yyyy\n");}
   private:
       static tt t;
};
tt ttt::t;

void ff()
{
   static tt t;
   printf("zzzz\n");
}
int main()
{
   printf("main();\n");
   ff();
   ff();
   return 0;
}
```
运行结果：
```
$ gcc a.cpp
$ ./a.out
xxxx   //  tt ttt::t; 初始化时输出
main(); // 进入main()
xxxx // void ff() 中的 static tt t 初始化时输出
zzzz // 表示ff 确实进入了
zzzz // 再次进入 ff，但是没有再次初始化static tt t 
```

另外，如果把 main 函数中的两条“ff()”去掉，会发现，仍然在“main()”前打印了“xxxx”，这就是说，类中的静态成员果真是和全局变量很一样，即使你用不到它，它也会初始化。

但是注意，在这点上，有个不算意外的意外。这个"意外"就是类模板中的静态变量。

代码也不上了。总之就是，你会感觉到，类模板中的静态变量是只有引用到了这个类的时刻，这个静态成员才开始初始化。否则就不初始化。

其实，这并不是意外。第一，上面说的“类模板中的静态变量是只有引用到了这个类的时刻，这个静态成员才开始初始化”，如果加几句debug log，你会发现，这个初始化依然是发生在main函数之前。第二，类模板本来就是如果没有用到，那么这个类模板就仿佛没有一样（因此里面有严重的程序bug也是没事的），既然这时候等价于没有，当然不会执行到。
