# python 的多线程全局锁能被突破吗

我们知道，python多线程运行的时候，会有一个全局的锁，使得多线程本质上还是没有并行起来。

那么如果python 如果调用到用c写的一个库，库中如果起了多个线程，这多个线程会否受到该全局锁的影响呢？

经过试验，对于普通的 c/c++ lib，用 ctypes 调用它，lib中的多线程不会受到该全局锁的影响。至于按 python 规范做出的c/c++ 插件内部的多线程是否收到全局锁的影响，没有验证。

所参数的python调用 c/c++ lib 的例子代码见： http://blog.csdn.net/taiyang1987912/article/details/44779719 , 用 ctypes 方式调

我试验所写的c/c++ lib中的一个函数创建了一个执行死循环的新线程。然后python中多次调用该c函数后，top发现，该python进程所占用的cpu突破了单核限制了。

### 接下来，来点权威的资料看看。
据 https://docs.python.org/3/glossary.html#term-global-interpreter-lock ：
> **global interpreter lock**
> 
> The mechanism used by the CPython interpreter to assure that only one thread executes Python bytecode at a time. This simplifies the CPython implementation by making the object model (including critical built-in types such as dict) implicitly safe against concurrent access. Locking the entire interpreter makes it easier for the interpreter to be multi-threaded, at the expense of much of the parallelism afforded by multi-processor machines.
>
>
> However, some extension modules, either standard or third-party, are designed so as to release the GIL when doing computationally-intensive tasks such as compression or hashing. Also, the GIL is always released when doing I/O.
> 
> 
> Past efforts to create a “free-threaded” interpreter (one which locks shared data at a much finer granularity) have not been successful because performance suffered in the common single-processor case. It is believed that overcoming this performance issue would make the implementation much more complicated and therefore costlier to maintain.

也就是说，其实只有python bytecode，才会被此全局锁所锁。而bytecode是python代码编译后的产物。一些扩展模块——当然不能使用python写的模块，是可以避免该锁的。
