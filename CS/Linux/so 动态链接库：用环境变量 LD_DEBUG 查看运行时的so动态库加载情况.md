# so 动态链接库：用环境变量 LD_DEBUG 查看运行时的so动态库加载情况

LD_DEBUG用来查看so动态库的加载情况时，其实只是作为一个环境变量来发挥作用的。LD_DEBUG是由glibc提供出来的，所以程序用了glibc的时候，只能能把LD_DEBUG的取值截获下来，并作出不同的反应。

LD_DEBUG的使用是 ```export LD_DEBUG=XXX```，然后运行命令就行了，就把这个命令相关的so加载信息显示出来了。XXX 可以取好多值，其中一个是 help。

可以直接 ```LD_DEBUG=help ls``` （随便选了一个命令）来查看下LD_DEBUG的帮助：

run:
```
$ LD_DEBUG=help ls
```
output:
```
Valid options for the LD_DEBUG environment variable are:

  libs       display library search paths
  reloc       display relocation processing
  files       display progress for input file
  symbols     display symbol table processing
  bindings    display information about symbol binding
  versions    display version dependencies
  all        all previous options combined
 statistics  display relocation statistics
  unused      determined unused DSOs
  help       display this help message and exit

To direct the debugging output into a file instead of standard output
a filename can be specified using the LD_DEBUG_OUTPUT environment variable.
```

因此要看so的搜索情况，可以用 LD_DEBUG=libs。
