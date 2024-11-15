# python twisted 库之 Deferred 嵌套

关于twisted Deferred 的嵌套：

假如有Deferred1 与 Deferred2， 每个都添加了一系列回调。如果希望Deferred1 在运行到某个地方的时候停止执行，开始等待执行Deferred2，那么必须是Deferred1 的某个回调函数返回Deferred2。而不是只是把Deferred2作为参数传给Deferred1的某个回调。因为，否则的话，就等于是两个独立的Deferred，谁也不影响谁。Deferred2最后返回的时候，最后一个回调的返回值，（如果不是Deferred的话）会返回给Deferred1的下一个回调。

例子：
```
from twisted.internet.defer import Deferred

def callback_1(res):
   print 'callback_1 got', res
   return 1
def callback_2(res):
   print 'callback_2 got', res
   return 2
def callback_3(res):
   print 'callback_3 got', res
   return 3
def callback_4(res):
   print 'callback_4 got', res
   return 4

deferred_2 = Deferred()
deferred_2.addCallback(callback_4)
def callback_2_async(res, deferred_2):
   print 'callback_2 got', res
   return deferred_2  # 如果return 4444，则等于两个独立的 Deferred，只有返回deferred，才会起到想要达到的效果。 

d = Deferred()

d.addCallback(callback_1)
d.addCallback(callback_2_async, deferred_2) # deferred_2 最后一个回调的返回值，返回给callback_3
d.addCallback(callback_3)

d.callback(0)
deferred_2.callback(22)
```

参见：
- http://krondo.com/deferred-all-the-way-down/
- https://github.com/jdavisp3/twisted-intro/blob/master/twisted-deferred/defer-10.py
