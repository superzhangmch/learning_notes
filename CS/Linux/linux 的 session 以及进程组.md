# linux 的 session以及进程组

linux 下的 session 是与终端登录相关的一个东西，一般一次登录，会建立一个新的session。如果登录后，以setsid方式运行命令，则会开启另一个session。

一个session由多个进程组构成。其中第一个进程组的第一个进程会成为session leader。实际中，这个sesion leader 往往就是登录后的bash shell进程（setsid 启动的session leader则是setsid启动的进程）。

一般的shell 下运行（非setsid 方式运行）一个命令后，该命令进程会发起一个独立的线程组。如果是管道命令串，则这一串进程会成为一个进程组。程序fork出来的进程一般和原进程属于同一个进程组。

<br>

一个shell窗口，只对应一套输入输出设备，因此，一个session只能有一个进程组成为前台进程组，其他的只能是后台进程组。
关于进程，进程组，前台进程，以及 session 等可以用 ps axj 查看：
```
 PPID   PID  PGID  SID TTY     TPGID STAT   UID   TIME COMMAND
   0     1     0    0 ?          -1 S       0   0:18 init [3]  
   1     2     0    0 ?          -1 S       0   0:45 [migration/0]
   1     3     0    0 ?          -1 SN       0   0:01 [ksoftirqd/0]
   1     4     0    0 ?          -1 S       0   0:42 [migration/1]
   1     5     0    0 ?          -1 SN       0   0:01 [ksoftirqd/1]
   1     6     0    0 ?          -1 S       0   0:41 [migration/2]
   1     7     0    0 ?          -1 SN       0   0:01 [ksoftirqd/2]
   1     8     0    0 ?          -1 S       0   0:36 [migration/3]
   1     9     0    0 ?          -1 SN       0   0:01 [ksoftirqd/3]
```
如上是一次 ps axj 的部分结果。 TPGID表示当前session的前台进程组号，从而可以决定出前台进程组是哪个。 TTY 表示每个进程的terminal 使用情况。SID 就是session Id，等于 session leader的pid。

因此，从sid 就可以断定出本次登录后启动了那些进程（setsid 进程除外，以下默认都是非setsid进程）。

<br>

因为登录终端后看到的shell会成为一个session leader，且接下来的工作全在这个session 里进行，下面对这种情况做一些说明：
- ssh client 连接上了远程的sshd，然后sshd 启动了一个shell（如果是本地登录，则是由getty来启动），这个shell 进程成为了session leader。
- 如果终端被直接关闭（直接点关闭按钮），或者网络直接断开，则内核的终端驱动（而不是 sshd，开始以为是它） 会探测到网络断开，然后内核的终端驱动会向 shell 发送 SIGHUP 信号， shell 会给该 session 里的所有进程（但不包括在该session里，但是父进程不在该session里的进程）也发送SIGHUP（经过试验，发现只能是shell 自己发的，而不是内核看到这种情况发的），命令这些进程（无论是前台进程还是后台进程）退出。这时候如果某个进程屏蔽了 SIGHUP 信号（比如用nohup 启动，或者用了disown shell内置命令屏蔽了SIGHUP），该进程就可以在shell 退出后仍然继续执行了。
直接给 shell 进程发送 SIGHUP信号后的效果也是一样的，会同以上表现。
- 如果不是发生了网络断开，而是终端 shell 被杀，比如kill -9，则会把shell 杀掉外，还会给所有前台进程发送SIGHUP（也是内核驱动发的）；但是对于后台进程，因为变成了孤儿进程，会被init 收养，从而会继续执行下去，哪怕终端界面以及消失。
- 下面情况下，虽然没有用nohup/disown 或者 setsid,终端shell中启动的命令在终端退出后仍然会继续执行：
  这种情况就是给进程变成了孤儿进程从而init收养的进程。这时候该进程就会摆脱本session的限制。

造成孤儿进程的原因，除了C程序中fork的进程没有wait这种程序层面外，在shell 命令与脚本层面看：就是后台命令没有执行完就脚本退出或shell退出。比如“(cmd &)”启动子进程但是没有wait，shell脚本中&后台命令没有wait就退出， shell 中执行了后台命令然后还执行exit退出shell(但是直接关闭shell不会出现这种情况，因为会受到sighup信号，另外，shell中如果开起了exit时对所有子进程发送sighup的开关，这里说的这个也会失效)。

另外需要注意的一点是：如果有后台进程没有等待执行完就exit退出，往往会导致终端界面hang住，这时候解决办法就是在运行后台进程的时候要把标准输入（错误）输出都重定向。

-------------------------

关于 SIGHUP 信号到底是谁发的，找到了如下的网页，说明了是内核发的：
- http://bbs.csdn.net/topics/360135067
- http://stackoverflow.com/questions/5546223/signals-received-by-bash-when-terminal-is-closed
- 好文： http://blog.csdn.net/wlh_flame/article/details/6302646
- http://stackoverflow.com/questions/5527405/where-is-sighup-from-sshd-forks-a-child-to-create-a-new-session-kill-this-chil
  
直接摘抄一些吧：

> ssh (along with terminal emulators, screen, tmux, script, and some other programs) uses a thing called a "pseudo-tty" (or "pty"), which behaves like a dialup modem connection. I describe it that way because that's the historical origin of this behavior: if you lost your modem connection for some reason, the tty (or pty) driver detected the loss of carrier and sent SIGHUP ("Hangup") to your session. This enables programs to save their state (for example, vi/vim will save any files you had modified but not saved for recovery) and shut down cleanly. Similarly, if the network connection goes away for some reason (someone tripped over the power or network cable? ...or sssh dumped core for some odd reason), the pty sends SIGHUP to your session so it gets a chance to save any unsaved data.
>
> 
> Technically, the tty/pty driver sends the signal to every process in the process group attached to the terminal (process groups are also related to shell job control, but this was their original purpose). Some other terminal signals are handled the same way, for example Ctrl + C sends SIGINT and Ctrl +\ sends SIGQUIT (and Ctrl + Z sends SIGTSTP, and programs that don't handle SIGTSTP by suspending themselves are sent SIGSTOP; this double signal allows vim to set the terminal back from editing mode to normal mode and in many terminal emulators swap to the pre-editing screen buffer).

- 内核驱动发现终端（或伪终端）关闭，给对应终端的控制进程（bash）发 SIGHUP  
- bash收到SIGHUP后，会给各个作业（包括前后台）发送SIGHUP，然后自己退出
- 前后台的各个任务，收到来自 bash 的SIGHUP，退出（如果程序会处理SIGHUP，就不会退出）
