# C++ 成员函数自动是本类的友元函数

C++ 类的成员函数自动就是本类的友元函数。这点很重要。比如：

```
class a{
  private:
    int data;
 public:
    a * f(int i )
    {
        a * p = new a;
       p->data = 123;
        return p;
    }
};
```

本来 data 是 a 的private成员。所以在外部不可以直接访问。在成员函数 f 内，当然可以直接访问的，但都是通过this指针来访问的。而这里，通过p指针也可以访问到本类的另外一个实例的data。就是因为上面说的那点。
