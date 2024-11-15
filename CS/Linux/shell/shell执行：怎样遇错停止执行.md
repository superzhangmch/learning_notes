# shell执行：怎样遇错停止执行 

以往用 jenkins 等CI工具的时候，把一段shell贴过去，其中某一行有错，自动就报错退出了。很是好。

但是直接 shell 执行脚本，则是on error 除非代码主动 exit, 否则会执行到尾。且整个脚本的返回值，是最后一句命令的返回值。这容易遮盖整个脚本内部的错误，追查起问题半天没头绪。

其实shell（准确说是 Bash shell，其他的没试），有机制作保证的。这就是 ```-e``` 运行选项。

用 ```sh -e XXX.sh``` 方式运行 XXX.sh, 那么 XXX.sh 内任一条命令执行出错，都会当下退出。

另外 ```set -e```/```set +e``` 命令，也可以辅助完成这样的事, 前者是打开，后者是关闭。因此，如果不想```sh -e``` 方式指定，可以在脚本内需要的地方```set -e```/```set +e``` 把需要严格检查的代码块包起来。

上面方式虽然遇错停止执行了，但错误地点还是不可知。其实加个 ```-x```选项：``` sh -ex XXX.sh```即可。

参考：https://stackoverflow.com/questions/2870992/automatic-exit-from-bash-shell-script-on-error
