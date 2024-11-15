# 执行 C 的bin程序时，怎样从shell 进入 main 函数的

c 程序入口点当然是main()函数，但是在执行main函数之前其实还会做一些别的事的，比如加载so等等，这个过程是怎样的呢？大概是这样的：

1. execve 开始执行
2. execve 内部会把bin程序加载后，就把.interp指定的 动态加载器加载
3. 动态加载器把需要加载的so都加载起来，特别的把 libc.so.6 加载
4. 调用到libc.so.6里的__libc_start_main函数，真正开始执行程序，
5. __libc_start_main做了一些事后，调用到main()函数

从这里也可以看出，为什么即使一个 ```int main(){return 0;}```这样的最简c程序，也会用到libc.so.6。就因为必然用到__libc_start_main，而__libc_start_main1在libc.so.6 里面呢。
