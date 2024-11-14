# typename：用法小结

typename 当然是用于模板定义中。但是除了在"```template < ... typename ... >```"中使用之外，在“模板定义中用到了某个**模板类的类内类型**”的时候，也会需要它。

比如：

### 1. 用户定义一个变量
```template <T>
void ff(T t) 
{
       typename T::some_type a;
}
```
T::some_type 是类T内定义的一个类型，那么如果要用 T::some_type 来定义一个变量，就需要前面加typename。

### 2. 用于函数返回值指定
```
template <T>
typename T1::t ff(T t)
{
       typename T1::t a;
       return a;
}
```
### 3. 用于模板类中
下面例子外，模板类中的函数，以及变量用到的时候也需要加typename。
```
template <T>
class bb
{
    public:
       typedef  int ii;
       static int jj;
};
template <T>
class cc
{
       public:
              typedef typename T::jj T1;
              typedef typename bb<T>::ii TT;
};
```

之所以这些情况下必须加 typename，是因为 T::jj 这样的还可以解释为 静态变量。否则的话：
```
template <T>
void ff(T t) 
{
       T::some_type * a; //若前面不用 typename，即不：“typename T::some_type * a”
}
```
本来为了定义一个类型的```T::some_type *```的变量a，还可以解释为 ```T::some_type 乘以 a```，就歧义了。另外好些情况下，其实是可以决定出到底是指的变量还是类型，但是因为 模板只有在用的到时候才展开，不方便编译器提前查错，所以就规定了发生这种歧义的时候，优先解释为变量。

另外，据 http://blog.csdn.net/pizzq/article/details/1487004，是有几种情况下，确实可以不用加typename的，直接摘抄：
#### （1）类模板定义中的基类列表。
例如
```
template
class Derived: public Base::XXX
{
...
}
```
#### （2）类模板定义中的初始化列表。
```
Derived(int x) : Base::xxx(x)
{ 
...
}
```
这是因为这时候，编译器可以十分肯定的断定到底是指的变量还是类型。
