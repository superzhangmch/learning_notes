# linux 登录与密码

遇到了才知道，是可能发生这样的情况的：ssh 没法登录，总提示 “Permission denied, please try again.”，但是不用 ssh 而用本地登录(就是通过键盘与显示器直连主机登录)却密码都完好。

最后查清原因是 sshd 的相关文件遭到了破坏。重装了下 sshd 完美解决。

顺便厘厘登录有关的一些事：关于登录密码验证这块，内核是不管的（问了下相关人得知），所以ssh没法登录，很大可能就是 sshd 故障。登录密码验证通过看 /etc/shadow 文件，而这里面的密码是加密的。而且，经过试验确认，同一个密码，得到的加密串是不一样的，这样不可能通过直接改shadow文件来重置密码。

附：怎样找回密码
- 一个方法是用应急盘启动系统，然后 mount root 分区并把/etc/shadow里的密码那个域置为空。reboot，用户名写root，然后回车，就直接进入系统了；然后就可以用passwd来设置密码了。以上方法试验通过。顺便通过与另外机器的对比确认：不同机器上，同一个密码对应的密码加密串是不一样的。
- 另一个方式是，进入单用户模式，然后就可以改密码了。可以在 grub 中进入编辑模式，然后添加内核参数 single，然后就进入单用户模式了，然后passwd改密码。【可以参看 http://wenku.baidu.com/link?url=P0poEEEbpqix9f4IKJb1d72OzrOb6UgSBtrSafENPpZO-pz-uGnDYxHd8QMcWbUvtPLBS6aorsNFq4FhDnQhdj1aUCw-8facSmsHJ0RPAle 。】

2014-02-26 
