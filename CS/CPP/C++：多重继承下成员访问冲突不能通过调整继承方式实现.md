# C++：多重继承下成员访问冲突不能通过调整继承方式实现

如果是多层单继承，那么即使在每层都定义了同一个变量，那么在最外层不带范围(XXX::这样)访问该变量的时候，都是不会导致访问冲突的。
但如果在多重继承下，就有可能出现，也就是往往必须用::来指定好范围。比如：
```
class a{
       public: // 若private，并解决问题
              int aaa;
};
class aa
{      public:
              int aaa;
};
class bb :  public a  , public aa // 多重继承
{
       public:
              void f(){printf("%d\n", aaa);} // 对aaa访问冲突。必须指定范围，是a::aaa,还是aa::aaa
};
int main() 
{
       bb b;
       b.f();
       return 0;
}
```
会编译不过。如果把 print 一行中 aaa 引用换成a::aaa 或 aa::aaa，则就 ok 了。

这时候可能会想，如果把上面的class a 的 public 换成 private，那么printf 处的 aaa 是访问不了 a::aaa 的，但是能访问aa::aaa, 那么是不是应aaa 就代表了对 aa::aaa的访问呢？

一开始我感觉可以，经过试验，还是有冲突。也就是说**靠调整继承权限与定义的访问权限来消除访问冲突是不可能的。**

悲夫！

