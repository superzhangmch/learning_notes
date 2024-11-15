# POSTFIX 邮件收发使用小记

发送邮件实现起来其实很简单的。只要按照SMTP协议规定，若干个socket 读写操作，就能把邮件发送出去；这时候你会发现，发一个伪造发件人的邮件真是太easy了。
但是虽然简单，总不能凡事都亲自造一遍车轮，况且，实现容易，做稳定难。

因此，现在需要一个能发送邮件的功能，就货比三家（其实只是大概看了下，看起来这个更主流），打算选用 postfix 看看。况且postfix还能提供收邮件功能(不是outlook那种收，而是可以别人直接发到这里！)

我也不打算说的详细与那么精准。就是把一路波折记录下吧，以利下一次再使用时少走些弯路。

Apt-get 安装的，全是默认选项。想来源码安装也是差不多，不过没有试。安装好后，“telnet 127.0.0.1 25”，发现已经是可以连上了。说明全启动ok了。

### 然后试试收发邮件。
- 首先是不知道怎么添加用户。上网查说，**postfix 就用的是linux系统账户系统 【后补：后来知道，postfix支持两种账号系统，linux账户系统与虚拟用户系统，后者可以在一个linux账户下支持好多个邮箱用户。全部是靠配置的】**。然后似乎有postfixadmin的东西（或类似一些别的），可以扩展出不依赖于系统账号的用户系统【后补：确实。后来才知道，postfixadmin只是用来管理postfix的虚拟域名与虚拟用户的，不干别的，早知道就不折腾它了。因为我也不需要支持那么多用户】；可惜postfixadmin真心下载不到，因为它是sourceforge上的东西，被和谐掉了。反正主要是要发邮件，用系统账号也可以，就这样吧。
- 然后当然还是一路网查。看到一个叫做dovecot的东西，好像别人搭一个可以实用的支持多用户的邮件系统都是联合用了 postfix/dovecot/mysql/postfixadmin 这好几个东西。对于用mysql/postfixadmin还好理解，应该是为了存邮件内容与账户系统内，以及提供web界面。为什么还postfix/dovecot都用呢？**难道 postfix不能提供完整收发邮件功能？这很使我怀疑**。看官网什么的，分明可以啊。而且从看到的资料，感觉postfix 和 dovecot 的功能差不多啊！带着疑惑，直到收发邮件全完成后，虽然疑问还在，但是终于确信：**postfix 就是个完整的邮件服务器，可以收可以发**。至于为啥别人还要用到dovecot，我也不想深究了。（这段话，有点啰嗦，但很有必要）【后补：后来知道，原来dovecot是用来做pop3 server 供outlook等下载邮件用的。我还以为它也用于server端的接收邮件呢。而postfix只做server端的收发邮件，所有只要处理好smtp就可以了。mysql呢，当然是存储虚拟用户的。】

### 下面说下收发邮件的一些曲折。

安装 postfix 后，会顺便安装一个 sendmail 命令（或者说如果有，就取代系统已有的），可以发邮件，不过似乎这个用起来很麻烦。

还可以用另外一个命令 mail（gnu mail utilis工具中一个）。中间发的过程我不清楚，也不想搞清楚，总之，用mail命令发的时候，会经过postfix最终发到目的地址：
```
echo "ttttttt tttttttt这里是邮件内容" | mail -s "texxxxxst这里是标题" username@163.com
```
注意这里没有指定发件人地址。当然我知道，我已经配置好 postfix 了， 它会自动根据 \`whoami\` 与 \`hostname\`  以及我配置的一切，生成发件人的。发送后mailq可以查看发送情况。

但是却发现，当我这样做的时候（当然是从网上学来的应该这样做），总是失败。用mailq 发现，就全因为这个发件人地址问题。它一直用的是\`whoami\`@\`hostname\` ，而不是`whoami`@domain。

这是个简单又头疼问题。一方面从网上看到，sendmail 命令可以指定收件人的，另外看到mail 也可以这样子指定发件人：
```
echo "ttttttt tttttttt这里是邮件内容" | mail -s "texxxxxst这里是标题" username@163.com -- -f src@src_domain -F 发件人名字
```
注意是两个“-”后跟-f。但我总是用-f失败。

无奈之余，去外网邮箱试试postfix的“收邮件”吧，结果居然一次就成了。直接给你配置出的邮箱账户发邮件，然后去机器敲入mail命令回车，提示接到了新邮件。
但这更加令人无奈了。因为分明发邮件本来很简单嘛。

### 后来查呀查，发现原因是这样的：
postfix内部维护有一个表，这个表是一个映射表，会把发送人地址作映射。像我一直看到它发的是username@hostname，那么可以在表中配置key=username@hostnmame，然后令value=你想要的地址，就可以了。
这个是参看 http://bbs.chinaunix.net/forum.php?mod=viewthread&tid=4153959 ，然后作修改最后生效的。

这里就再复述下吧：
```/etc/postfix/main.cf 中修改或添加
smtp_generic_maps = hash:/etc/postfix/my_generic_maps
my_generic_maps 中添加映射关系：
aa@localhost  aa@bb.com
bb@localhost  bb@bb.com
然后执行：postmap /etc/postfix/my_generic_maps， 更新映射表。
```
然后重启，ok。能发送邮件了。

### 【附】
启动/停止命令： postfix start ；postfix stop
reload 配置： postfix reload
清空 mailq 里的消息：postsuper -d ALL
mail 命令发邮件指定发件人地址： 
1. 用 -r sender@sender_domain. mail 内部调用的sendmail 命令。
2. 或者用 -a "From : 'nickname' "
   

后补：初次使用，理解肤浅。后看到，postfix 也可以配置成不适用本地系统账号。后面再补记吧。

2014-11-07
