# Bash shell 运行命令的时候怎样传递环境变量

假设 a.sh 中有内容如下：
```
echo $aa
```

a.sh 中的 $aa 是从环境变量中获得的。如果想在运行 a.sh 的时候给 $aa 赋值，一种方式是把环境变量export出去，从而实现命令获得环境变量：
```
export aa=111
./a.sh
``` 
这样的问题是，运行下一个命令的时候，也能得到这个环境变量，这样当然是不好的。

其实有更好的一个方式，该方式就是把环境变量的赋值写到命令前面，如下所示：
```
aa=111 ./a.sh 
```

如果是多个就这样写：
```
aa=111 bb=222 ./a.sh 
```
