# mysql 使用零散知识

#### 1. 安装好后，需要
- 改 $DIR/etc/mysql/my.conf: basedir是mysql的安装base目录，datadir是mysql计划存数据的目录
- 初始化数据库：mysql_install_db  --datadir=XXX， 这里的datadir和上面的datadir一样。没有这部，启动不起来。然后可以mysqld启动了。如果说找不到：bin/my_print_defaults, 则回到bin所在的目录，执行mysql_install_db  
- 这时候外部机器访问，可能报错：is not allowed to connect to this MySQL serverConnection closed by foreign host，这时候需要用mysql给机器授权：```mysql -h $mysql_hostname -p 3306 -P```, （此时还没密码，直接回车进去）进入后，进行访问授权：```grant all privileges on *.* to 'root'@'%' identified by '密码';```上面还没给root设置密码, 用“```mysqladmin -u root password yourpassword```” 设置


#### 2. join操作。
```join ... where ... ```中：逻辑上等于是，先join，得到一个临时表，然后用where中的条件做过滤


#### 3. “mysql 的隐式类型换换”和“索引失效”
mysql的sql语句中，如果有大于小于等于比较符前后的操作数的类型不符合，mysql往往会做隐式的类型转换。转换规则比较复杂。

假如表结构的定义中，某字段是字符串类型，sql中明文指定了一个数字和它作匹配，则mysql会把数据库中内容转换为数字，然后再去和这个数字比较。这个过程显然需要扫描全表——如果有索引的话，就会索引失效。需要特别注意

#### 4. ```select * from tab where create_time > '20200202' limit 1```, create_time 上有索引。
本意是返回随便一条符合的即可。实际上并不会走索引。需要先order by 然后才limit 1
