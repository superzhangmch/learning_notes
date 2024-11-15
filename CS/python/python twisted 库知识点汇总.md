# python twisted 库知识点汇总

### 关于Deferred 与回调：
1. Deferred 的callback 或 errorback 中抛出的异常都不会导致整个程序崩溃。如果回调链下层还有errback，则由下层处理。如果已经没有了，按 http://krondo.com/a-second-interlude-deferred/ 所说，会抛出异常，测试发现最新版twisted，无异常抛出。总之，callback/errorback 中抛出的异常不影响整个程序继续执行。
2. callback 与 errorback 总是成对添加的。大概说，分别对应 try except 中要执行的代码。添加回调对的方式有4种: addCallbacks, addBoth,  addCallBack, addErrback。前两个把callback 与 errorback都是显式添加。addCallBack则会隐式添加一个把异常往下传的errback，addErrback会隐式添加一个把结果往下传的callback。
3. callback 与 errorback 都可以返回正常结果或异常。
4. Deferred 被触发后，会沿着添加的< callback , errback >链条往下执行，根据上一步是传来正常结果还是异常而决定是执行 callback 还是errback。callback 执行可能导致下一步执行errback， errback执行也可能导致下一步执行callback。
5. Deferred 只能被触发一次。
6. 回调返回 Deferred：callback也可以返回一个新的Deferred。这时候，必须等新的Deferred被触发并被执行完后，才会执行本 Deferred 的下一个 < callback, errback >。本 Deferred 的下一个 < callback, errback >被执行的时候，是被传入正常结果，还是异常，根据新Deferred的最后一次 < callback, errback >执行结果而定。
7. 回调链执行的时候，假设没有返回子Deferred的情况。那么从 twisted 源代码上表现出来的是：会一口气执行完所有的回调。而不会中途切换走执行其他的与此不相干Deferred。
8. deferred 被触发后，仍然可以继续添加回调函数。

### 关于defer.inlineCallbacks 函数修饰符：
如果一个函数有若干语句，某些语句会有延迟动作，那么可以令该语句以Deferred的形式返回结果，并用yield 把该 Deferred yield出来。这样整体上，分明是异步代码，却像同步代码一样。举个例子：
```
@defer.inlineCallbacks 
def func():
    aa = yield func1()
    bb = yield func2(aa)
    cc = func3(bb)
    return cc
```
func1, func2 都会返回deferred。用 defer.inlineCallbacks 后，会保证在某处会有一个与yield相对应的 next-next 代码块。该代码块会等待func1执行完毕后，把 deferred 最后返回的结果send到上述函数中，使得下一语句继续执行。

### 关于多线程：
1. callInThread 与 callFromThread 分别用于主线程与非主线程。前者用于主线程往非主线程发起任务，后者用于非主线程往主线程的事件循环提交任务。callFromThread 往主线程提交任务的时候，是通过往一个[] 中append的方式做到的。在python中[]是线程安全的，所以可以这样，而不会引起线程安全问题。
2. callInThread 与 callFromThread 只是发起任务，并不会当下hang住原来的本线程。因此可以说不用担心线程切换过频的问题。
