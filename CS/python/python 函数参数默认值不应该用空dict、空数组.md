# python 函数参数默认值不应该用空dict、空数组

例子：

```
def f(d, a={}, b=[], c=1 ):
  a[d]=d
  b.append(d)
  c = c+ d
  return [a, b, c]
print f(1)
print f(2)
print f(3)
```

运行结果竟然是：
```
({1: 1}, [1], 2) 
({1: 1, 2: 2}, [1, 2], 3) 
({1: 1, 2: 2, 3: 3}, [1, 2, 3], 4)
```
本来预期三次结果一样。且 python2, python3 下皆如此。


从这个分析，一个函数的参数如果是[]或{}等复杂类型会在第一次调用函数的时候做初始化，以后再次遇到的时候，就直接用上一次已经变成的值。而对于简单类型参数，比如上面的c，则不会这样。

参考： http://www.toptal.com/python/top-10-mistakes-that-python-programmers-make 

