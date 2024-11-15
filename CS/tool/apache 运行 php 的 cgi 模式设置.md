# apache 运行 php 的 cgi 模式设置

apache 运行 php，大概三种模式：
1. cgi；
2. fastcgi；
3. 作为apache的一个模块。
但是我是独爱cgi模式的。

基本设置思路是：

```
<IfModule alias_module>
    ScriptAlias /php/ /home/..../php/bin/
    AddType application/x-httpd-php .php
    Action application/x-httpd-php /php/php-cgi
<Directory "/home/....../php/bin/">
    AllowOverride None
    Options None
    Order allow,deny
    Allow from all
</Directory>
```

2014-12-30
