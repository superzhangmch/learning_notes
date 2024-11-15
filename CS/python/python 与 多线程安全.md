# python 与 多线程安全

一句话说，python的所有原生数据类型，比如 dict， list, set 等的基本操作都是线程安全的（这是由python的全局锁GIL保证的）。也就是说对一个list append的时候，不用担心另一个线程可能在删除一个元素。twisted 的 callFromThread 往主线程提交任务的时候，其实就是往一个list append一个回调函数。

但是据 http://stackoverflow.com/questions/6319207/are-lists-thread-safe ， ```L[0] += 1```, 这样的是非线程安全的（L[0] = L[0] + 1 的缘故吧？）。一些细节见：http://effbot.org/pyfaq/what-kinds-of-global-value-mutation-are-thread-safe.htm 。

另外， 据 https://docs.python.org/3/library/collections.html#deque-objects ， collections.deque 的 append 与 pop操作都是线程安全的，也就是说，可以用作无锁队列了。

最后补充一句，python有多个实现，上面所说是一般的python实现，也就是cPython。
