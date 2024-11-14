# Linux setsockopt 的 TCP_DEFER_ACCEPT，TCP_NODELAY，SO_LINGER 等选项的说明

getsockopt 的函数原型如下：
```int getsockopt(int s, int level, int optname, void *optval, socklen_t *optlen);```
可以用它来改变socket操作的一些行为。下面列出一些的用法与含义：

### 1.  level= IPPROTO_TCP, optname=TCP_DEFER_ACCEPT 
tcp连接建立需要三次握手，第三次是 client 往 server 发送一个确认包。如果没有设置 TCP_DEFER_ACCEPT, 那么三次握手一结束，server 上的 accept(fd) 就会返回了。而实际上三次握手后，往往是 client 先发数据包，因此可以让client 在第一次收到数据后才从 accept 返回，而要达到这点，只需要设置  TCP_DEFER_ACCEPT 。好处就是减少系统调用，从而提高性能。

参考：
- http://www.cnblogs.com/napoleon_liu/archive/2011/02/24/1964118.html
- http://blog.chinaunix.net/uid-23766031-id-3309049.html

### 2. level=IPPROTO_TCP，optname=TCP_NODELAY
 tcp 发送数据的时候，会尽量把连续的几个send小包打包成一个大包后才发送，所用到的算法叫做 Nagle算法。这样可能会出现问题就是，如果故意分多次发送，那么会导致第一个包的延迟太大。这时候只需要设置TCP_NODELAY。

参考：
- http://blog.csdn.net/dog250/article/details/5941637
- http://blog.csdn.net/shaobingj126/article/details/6758707

### 3. level=IPPROTO_TCP，optname=TCP_CORK
没有设置 TCP_NODELAY 时， Nagle算法会生效，也就是小包整合成打包。但是该算法整合的时候的一个标准就是它只允许一个未被ack的包存在于网络(可见如果不用它，那么可能会有多个)。这样如果ack返回的非常迅速，那么必定的发送包未必能保证会打包的太大。那么能不能令这个包整合的足够大后才发送呢？能。这就是指定 TCP_CORK 选项。

参考：
- http://blog.csdn.net/dog250/article/details/5941637

### 4. level=SOL_SOCKET， optname=SO_LINGER, optval=struct{ int l_onoff, int l_linger}
默认情况下，调用 close(tcp sock) 时，会立即返回，但是之前发送的数据有可能还没有发送完，但是内核仍然会把他们发送出去。但是可以通过指定SO_LINGER，来改变close时候的行为：

l_onoff=0, 则是默认行为；否则，close内部会最长等待l_linger指定的时间，然后close才返回。在等待期间，尚未发送完的数据会继续发送。如果时间到仍然没有发送完，那么余下的未发送数据会被丢弃（注意如果 l_linger=0，那么会close立即返回，且未发送数据马上丢弃，这时候会发送一个RST通知对方 ）。

参考：
- http://blog.csdn.net/factor2000/article/details/3929816

