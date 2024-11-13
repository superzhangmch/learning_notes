# C/C++ 中的 switch 语句

这里 http://en.wikipedia.org/wiki/Duff's_device 有这么一段 C 代码：

```
send(to, from, count)
register short *to, *from;
register count;
{
       register n = (count + 7) / 8;
       switch (count % 8) {
       case 0: do {    *to = *from++;
       case 7:              *to = *from++;
       case 6:              *to = *from++;
       case 5:              *to = *from++;
       case 4:              *to = *from++;
       case 3:              *to = *from++;
       case 2:              *to = *from++;
       case 1:              *to = *from++;
                   } while (--n > 0);
       }
}
```
第一次看到类似这样的，都以为是不是有问题。后来看资料，以及请教人等等，才知道是这么回事：
>  简单说，C 语言中的 switch(n) 语句就是一个goto 语句，不过是个条件goto而已。
  而 case n 语句呢，不过是个label而已。想想看能在 label 之间做什么，已经不能做什么。

这样看，就可以理解上面的代码了，从而也能够在必要的时候，精简代码。
