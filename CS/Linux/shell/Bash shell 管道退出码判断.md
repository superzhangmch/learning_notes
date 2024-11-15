# Bash shell 管道退出码判断

假设有一系列的管道命令系列，比如：
```
cat XXX.$RANDOM | grep xxx | wc -l
```
这时候要判断是否运行出错，从而决定是否往下执行。如果直接判断```$?```， 则判断的是最后的 wc 命令的退出码，这时候是0，会判为没错。而实际上cat已经错了。

run:
```
$ cat XXX.$RANDOM | grep xxx | wc -l 
```
output:
```
cat: XXX.12288: No such file or directory
0
```
run: 
```
$ echo $?
```
output: 
```
0
```

到底怎样判断呢？ 有两个办法：
### 1. 用set -o pipefail，具体 man bash 可以看到
```
$ set -o pipefail   
$ cat XXX.$RANDOM | grep xxx | wc -l 
cat: XXX.6296: No such file or directory
0
$ echo $?
1
```
### 2. 看PIPESTATUS系统内置变量
```
$ cat XXX.$RANDOM | grep xxx | wc -l 
cat: XXX.27700: No such file or directory
0
$ echo ${PIPESTATUS[*]}
1 1 0
```
