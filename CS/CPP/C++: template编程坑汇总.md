# C++: template编程坑汇总

C++下的template编程，隐藏着不少不为人所知的坑。往往踩到了之后，只好绕着走。因此如果在没有踩到之前就能绕坑而过，那么就省去以后的不少麻烦了。

#### 1、stl 容器中不是什么都能放。
以vector 为例。 vector 中不能放数组类型的东西。如果非要放，那么就自己包装一个数组template class，或者多套一层vector。

#### 2、继承于某模板类的时候，若模板某类型指定为本类，那么该模板类中没法引用到本类中定义的typedef 类型成员。
例子：
```
template< typename T>
class a
{
   public:
      typename  T::t a; // A. 
};
class x{public:typedef int t;};
class b: public a< b > // 如果是 b， 那么上面A那里不过。如果是x，则可以
                                // 当时如果是b，那么class a 中可以引用b中定义的方法与变量，类型不行。
{
   public:
       typedef int t;
};
int main()
{
    b bb;
    return 0;
}
```

#### 3、继承于某模板类的时候，不可在本类中以模板中的类型定义为本类的友元。但是可以定义模板类型的成员函数为本类的友元函数。
```
#include< stdio.h >
template< typename T > // 基于模版 T 的类
class a
{
   public: 
       int data;
       //friend class T;  // 若想这样，不可以
       friend void T::f(); // 这样就可以了可以
   private:
       static void f_a(){printf("f_a();\n");}
};
class x{public: void f(){a::f_a();} };
int main()
{
   x xx;   
   xx.f(); 
   return 0;
}
```
参考：
- http://stackoverflow.com/questions/6321191/using-friend-in-templates
- http://www.comeaucomputing.com/techtalk/templates/#friendclassT

或曰：
```
template
struct FriendMaker
{
    typedef T Type; 
};
```
这样一下，就可以简介解决。不过似乎需要高版本的gcc.

#### 4、模板的.h 与 .cpp 应该写到一个文件里。否则最后编译不过。g++下如此。

#### 5、如果一个模板类继承自另一个模板类，那么不能直接引用父类中的成员数据。
例子：
```
template< typename T >
class B {
public:
 void f() { } // ← member of class B< T >
};

template< typename T >
class D : public B< T > {
public:
  void g()
  {
   f(); // ← bad (even though some compilers erroneously (temporarily?) accept it)
  }
};
```
如上，f() 没法直接引用，会编译出错。解决办法是：
```
(a). this->f()
(b).  using B< T >::f; 然后可以直接用了
(c).  B< T > ::f().
```

参考：
http://www.parashift.com/c++-faq-lite/nondependent-name-lookup-members.html

上面网页有对以上的解释，摘抄如下：
> This might hurt your head; better if you sit down.
>
> Within D::g(), the name f does not depend on template parameter T, so f is known as a nondependent name. On the other hand, B is dependent on template parameter T so B is called a dependent name.
Here's the rule: the compiler does not look in dependent base classes (like B) when looking up nondependent names (like f).
This doesn't mean that inheritance doesn't work. Class D is still derived from class B, the compiler still lets you implicitly do the is-a conversions (e.g., D* to B*), dynamic binding still works when virtual functions are invoked, etc. But there is an issue about how names are looked up.
>
>
> Workarounds:
>
> 
> - Change the call from f() to this->f(). Since this is always implicitly dependent in a template, this->f is dependent and the lookup is therefore deferred until the template is actually instantiated, at which point all base classes are considered.
>
> - Insert using B::f; just prior to calling f().
> 
> - Change the call from f() to B::f(). Note however that this might not give you what you want if f() is virtual, since it inhibits the virtual dispatch mechanism.

大概说原因就是：编译器处理模板类的时候，如果一个变量名与typename的类型无关，那么这个名字就不会主动去模板父类中查找。

再参考：
- http://www.parashift.com/c++-faq-lite/nondependent-name-lookup-types.html
这个是和上面的一样的道理。
- http://stackoverflow.com/questions/7481967/variable-not-declared-in-scope-using-template-inheritance

#### 6、模板没有机会被用到的时候，仿佛本来没有这段代码。

#### 7、模板类中引用到typename T中定义的类型时要加typename：typename T::type_in_T;
例子：
```
template< typename T >
class a {
public:
   typename T::type_in_T ttt; // 若省typename 一词，编译器以为type_in_T 是T中静态变量。从而编译错误。
};
```

#### 8、某些地方会看到 aaa. template func(); 这样的。其中的 template 不可省，只是修饰作用。
参考：
- http://stackoverflow.com/questions/610245/where-and-why-do-i-have-to-put-the-template-and-typename-keywords
- http://en.cppreference.com/w/cpp/language/dependent_name

```
#include < stdio.h>
#include < stdlib.h>
template< typename T1>
class x{
public:
       T1 t;
       template< typename T>
       static void f()
       {
             printf("xxx\n");
       }
};

template< typename T>
void ff()
{
       typedef x< T> vv;
       vv::template f< int>(); // 这里的 template 不可省，只是修饰作用。
}

int main()
{
       ff< char>();
       return 0;
}
```

#### 9、模板类中若有模板成员函数，这个函数在类外定义的时候，需要写两层的template。不可合并写一个。
例子：
```
template< typename T >
class a {
public:
  template< typename T1>
   T1 * f();
};
template< typename T > // for 模板类
template< typename T1> // for 模板成员函数.不可合二处为：template< typename T, typename T1 >
T1 * a< T >::f()
{
  return new T1;
}
```

#### 10 、类成员函数不能是模板函数。。。（这句话写错了。但是忘了忘了本来应该是什么来着。。）
http://blog.csdn.net/jcwkyl/article/details/3771059
