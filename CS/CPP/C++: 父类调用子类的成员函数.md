# C++: 父类调用子类的成员函数

C++ 中，父类是没法调用到子类的成员函数的。当然，静态函数可以被父类调用到；这里只说普通函数。所以不能，是因为父类的定义中，还没有见到子类的定义，所以没法引用到子类的成员函数。

上面说的是在直接调用上，做不到。那么有没有别的方式做到呢？其实方法是有的。就是通过函数指针。当然，成员函数指针与一般函数指针有所区别。

例子如下：

```
#include < stdio.h >
class c2; // child class
class c1  // parent class
{
   public:
       c2 *c; // note here
       void (c2::*f)(int); // note here
       void f1() // want to call a method of child class C2
       {
          (c->*f)(123);     // 这里就可以随便调了，只要对c、f都赋好值了。
                            // 如果要把子类同一类成员函数通过函数指针数组方式调用，
                             // 那么也类似地当然是可以实现的
                             // 注意这里的括号与*，都需要
       }
};

class c2: public c1
{
   public:
       void f2(int i)
       {
          printf("f2(%d);\n", i);
       }
       void f3()
       {
          c = this;      // 传对象的指针。成员函数访问需要通过对象，所以还必须用它
          f = &c2::f2; // 给函数指针赋值
       }
};

int main()
{
   c2 c;
   c.f3();
   c.f1();
   return 0;
}
```

执行结果为：

```f2(123);```
上面实际上也演示了成员函数指针的用法。

那么，只能通过成员函数指针吗？有没有别的方法了?其实还有个方法是通过模板类，至于怎么做，具体就看例子吧：
```
#include< stdio.h >
template< typename T >
class c1 { //父类
public:
   T *t;
   void f1()
   {
       printf("%d\n", t->xxx); // t 是模板类型T的指针，这样即使不知道t的具体定义,
                                          // 也可以访问到其成员，可以调用到其方法
                                          // 若非通过模板，就不能这样
       t->f2(); // 调用子类的方法
   }
};

// 子类
class c2: public c1< c2 > {   // 这里这样
public:
   void f2(){ printf("f2()\n");}
   int xxx ;
   void f3()
   {
       xxx = 123;
       t = this;  // 这个需要这样设置
   }
};
int main()
{
   c2 c;
   c.f3(); 
   c.f1();
   return 0;
}
```

运行结果为：

```
123
f2( )
```

如果要以指针数组的方式调用子类成员函数，显然只能用第一种方法。
