# so 动态链接库：依赖冲突怎么解决

如果编译依赖有冲突：

假设D依赖于B又依赖于C,而B与C都依赖于A，而B与C使用了不同的A版本，那么在编译出的D就不知道到底会是使用了B的A还是C的A。如果随便哪个都无所谓，那ok。但是就怕有的时候用哪个的A都会导致B、C中会有一个不工作。

这是从某地方学来的怎么解决这种情况，答案是把B或者A做成一个so动态库，然后对这个so动态库再来一层封装，这层封装就是用 dlopen + dlsym 来调用so里的对外接口。

试验了下，确实可行：
```
// a.cpp 
int test1()
{
       printf("a.cpp::test1();\n");
       return 0;
}
extern "C"
{
       int test2()
       {
             printf("a.cpp::test2();\n");
              return 0;
       }
}
```

```
// b.cpp  
int test1()
{
       printf("b.cpp::test1();\n");
       return 0;
}

bash$ cat bb.cpp 
#include
int test1()
{
       printf("bb.cpp::test1();\n");
       return 0;
}
```

```
// c.cpp   
int test1();
extern "C"
{
int test2()
{
       test1();
       return 0;
}
}
```

```
// d.cpp: 调用 libaa.so
void test_so()
{
    void *handle;
    int (*callfun)();
    handle = dlopen("./libaa.so",RTLD_LAZY); // b.cpp  c.cpp  => libaa.so
    callfun=(int(*)())dlsym(handle,"test2");
    callfun();
    dlclose(handle);
}
```

```
// dd.cpp：调用 libaaa.so
void test_so_1()
{
    void *handle;
    int (*callfun)();
    handle = dlopen("./libaaa.so",RTLD_LAZY); // libaaa.so: bb.cpp  c.cpp
    callfun=(int(*)())dlsym(handle,"test2");
    callfun();
    dlclose(handle);
}
```

```
// main.cpp
int test1();
extern "C" int test2();
void test_so();   // from d.cpp
void test_so_1(); // from dd.cpp
int main()
{
       test1();
       test_so();
       test_so_1();
       test2();
}
```

如上有三个test1() 想要在 main.cpp 中都能调用到。如果不用so法，那么会发现最后用的全是某一个的test1()。

```
bash$ g++ -shared -fPIC -o libaaa.so bb.cpp  c.cpp  # => libaaa.so
bash$ g++ -shared -fPIC -o libaa.so b.cpp  c.cpp    # => libaa.so
bash$ g++ main.cpp a.cpp d.cpp dd.cpp -ldl          # => a.out
bash$ ./a.out
```
output:
```
a.cpp::test1();
b.cpp::test1();
bb.cpp::test1();
a.cpp::test2();
```

从上面可见，分别调用到了自己的test1()。

上面其实用一个so做试验就可以了；所以用2个只是想看看是不是dlopen的so内的同名函数会相互独立。发现结果是“是”。

### 【原理分析】
当程序已经运行开始的时候，也就是当main已经开始执行的时候，所有的符号解析已经是结束的了，这时候其实 .a 与 .so 的区别已经不存在了，所以不用 dlopen+dlsym 执行的函数的函数地址已经是确定的了。所以不用 dlsym 调用的函数会调用到正确的那个；而且在dlopen之后才被调到的同名函数，因为其实早就绑定好地址的了，因此也不会受到dlopen的影响而调用错。

dlopen的so中的没有被dlsym的函数所以不会影响到程序中的同名函数的执行，就因为那个同名函数早已经把函数地址定好了的缘故。

dlopen的so中的没有被dlsym的函数，实际上等于是不存在的函数（当然除非被so内间接调用到）。就因为它已经没有机会发生函数地址绑定了。

