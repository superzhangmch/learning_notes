# C++: 析构函数与异常

在《more effective C++》中提到了，析构函数中不应该抛异常。大概说就是两个异常不能共存；总之是没有看明白，于是查阅不少资料，终于知道了怎么回事。

实际上是这样的：在任何一个异常被抛出后，异常处理会沿栈逆上，查找第一个适当的异常处理catch 块，在一路逆行的时候，只要遇到某个stack frame 上有局部对象，那么就会调用到该对象的析构函数。现在问题来了，如果某析构函数抛出了异常，那么按理说这个异常也应该处理的，那么这时候，到底应该怎么办呢（经试验，直接就 core dump 了）？确实不好办，因此才建议析构函数总不应该抛异常。

也可以这么说：一个try block 中，最多只能抛出一个异常，如果将会发生抛出两个或以上异常的情况，那么就会导致混乱了。而这个“抛出两个或以上异常”的情形如果发生，只可能是析构函数跑出了异常。

试验代码如下：
```
class Bad
{
    public:
       int i;
       Bad()
       {
           i = aa;
          aa++;
          printf("Bad %d\n", i);
       }
       ~Bad()
       {
          printf("<<~Bad %d\n", i);
           //if( i == 3) // 若去掉这个条件，那么就会导致一个try块抛出多个异常。
              throw 1;
          printf("~Bad %d>>\n", i);
       }
};
int main()
{
    try
    {
       //Bad bad[7];
       Bad bad1;
       Bad bad2;
       Bad bad3;
       Bad bad4;
       Bad bad5;
       Bad bad6;
       Bad bad7;
       //throw "xx";
    }
    catch(...)
    {
       std::cout << "Never print this " << std::endl;
    }
    return 0;
}
```

参考：http://blog.csdn.net/nodeathphoenix/article/details/6045937

