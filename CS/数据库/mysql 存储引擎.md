# mysql 存储引擎


|Engine	|Support	|Comment	|Transactions|	XA	|Savepoints|
|:----|:----|:----|:----|:----|:----|
MRG_MYISAM|	YES|	Collection of identical MyISAM tables	|NO	|NO	|NO
CSV|	YES|	CSV storage engine|	NO|	NO|	NO
MyISAM|	YES|	Default engine as of MySQL 3.23 with great performance|	NO|	NO|	NO
InnoDB|	DEFAULT|	Supports transactions, rowlevel locking（行锁）, and foreign keys|	YES|	YES|	YES
MEMORY|	YES|	Hash based, stored in memory, useful for temporary tables|	NO|	NO|	NO

以上XA指的是分布式事务。可见，InnoDb支持的最广。但是性能上也比MyISAM稍微弱些。

另外， InnoDb下，```select（*）``` 会做全表扫描，而MyISAM下不会。

1. InnoDb：TEXT格式字段，如果较小，一般直接存在行内。较大的时候才行外存储。见 https://dev.mysql.com/doc/refman/8.0/en/innodb-row-format.html
2. 
