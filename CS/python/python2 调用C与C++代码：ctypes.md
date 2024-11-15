# python2 调用C与C++代码：ctypes

有时想对python提速，有时想把一段C/C++代码加一个易用的python壳，这时候都需要python能调C/C++代码。
所知有以下几种方式：
1. 直接c/c++写python库扩展。
2. SWIG，先写swig模板，再由SWIG来自动生成python扩展。
3. ctypes
   
发现ctypes是真正简单好用。

加载
===
把c/c++代码封装成so动态链接库。如果是c++编译的so，暴露接口需用 extern "C"包装
```
from ctypes import cdll, CDLL
libc = CDLL("libc.so.6")  获 libc = cdll.LoadLibrary('libc.so.6')
```

使用
====
分为两部分。一部分是怎样准备传入参数，另一部分是怎样获取返回值。
1. 参数传入
用python ctypes.c_int, c_float 等对象代表C的参数，塞入函数调用即可。

比如```ctypes.c_int(5)```, ```c_float(1.2)```, ```c_char_p("123")```, 分别代表 ```int i=5``` 与 ```float f = 1.2```, ```char p[]="123"```等。

如果参数是数组，则是```(ctypes.c_int * 10)(*[1,2,3,..]) ```这样，1,2,3..表示传入的值, 整体表示```int a[10] = {1,2..}。而``` (c_int * 10)() ``` 则表示没有初始值的```int a[10]```.

如果c/c++ 中参数是指针类型，则需要用```ctypes.bref()```来指明。比如，```int * a``` ，如果当做int a 的指针，用```ctypes.bref(c_int())```。如果是当做数组，则是传入```(c_int*10)())```这样的，此时不必用byref。

举例：
```
void func(int a, float * b, int b_size, int *c);
```
python中应该写成
```
func(c_int(), byref((c_float * 10)()), c_int(10), byref(c_int())
```
更复杂的自定义参数，可以参考手册。

2. 获取返回值
函数运算结果可以通过指针形式在参数中获得。如果要通过函数返回值返回，如果返回的数字，可以直接拿到，否则需要 ```func.restype = c_char_p```这样子指定返回类型。具体可看手册。

返回的数组类型，可以用```list(..)```转化为python数组，其他类型可以试试```xxx.value```.

参考：
- https://www.zhihu.com/question/23003213
- https://docs.python.org/2.7/library/ctypes.html

2017-12-09
