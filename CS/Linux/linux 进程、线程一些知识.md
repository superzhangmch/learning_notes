# linux 进程、线程一些知识

### 主线程退出，子线程是否一定马上被强制退出
答案，不是的。详细见： https://blog.csdn.net/hyp1977/article/details/51505744 。大概说来，如果主线程 pthread_exit()主动退出，子线程会继续执行

### 什么是协程

大概地说，一个进程可以由多个线程组成。而一个线程可能在用户态被组织成了协程(coroutine)的形式，协程乃用户自己（或编程语言比如python通过yield）实现的一种并发机制。

也就是说，在操作系统层面，是看不到协程这个概念的。

[reference]
- http://www.cnblogs.com/chgaowei/archive/2012/06/21/2557175.html
- https://zh.wikipedia.org/wiki/协程
