# C++ 显式类型转换

C++显式类型转换有下面这么5种：

- "(int)1.222" 这样的纯C式：
  
需要注意的是，(T)val，等价写法是T(val), 于是这样的转化，可以说本质上是调用类型 T 的适当的构造函数。如果不是基本类型，那么会新创建一个新对象，从而占据一份内存。这样如果val类型本来是 const T, 那么用(T)val来去const 是行不通的。想去掉const，只能取地址后再转。

- static_cast

- dynamic_cast

- const_cast：
const_cast的时候，T只能是引用或者指针。

- reinterpret_cast
