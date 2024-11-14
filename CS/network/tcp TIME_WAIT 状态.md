# tcp TIME_WAIT 状态

TCP 关闭连接是用的四步分手方式。**首先提出关闭的那端(不管是 client 还是 server 端!!)，在最后会最终进入TIME_WAIT状态**。这个状态会持续较长一段时间（ｎ多秒以上）。持续期间，netstat 还能看到这条连接。

处于 TIME_WAIT 状态的连接不影响新连接建立。
