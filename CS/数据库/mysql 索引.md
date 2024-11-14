# mysql 索引

数据库索引并不是作为搜索或连接条件的时候加了就一定好。

如果索引中平均每个key，差不多都会对应比较多的记录条数，那么这样的索引基本还是不加的好。因为这样的索引在启用到的时候，假如由key=K得到了对应的记录集合{r1, r2,r3,...,rn}，记录集中的这n条记录在索引中的存储顺序是不能确定的，也就是很有可能与数据库表中的相应记录存储次序不一样。这样在遍历索引方式访问数据库记录的时候，就出现了大量的随机IO，从而影响到了整体查询性能。

如果索引字段的取值个数本身非常少，那么这个字段上就不适合建立索引。

可以参看《mysql性能调优与架构设计》相关章节。

1. 非唯一索引的实现：
  - key对应的value有多个。实现上，有两种办法：一种是value按数组存；另一种是key和value set中的值作拼接，拼成唯一索引（《design data-intensive applications》）
  - mysql Innodb用第二种（ https://dba.stackexchange.com/questions/280530/how-does-mysqlinnodb-update-secondary-non-unique-index ）
  - 再参见： https://dev.mysql.com/doc/refman/5.6/en/index-extensions.html ：“InnoDB automatically extends each secondary index by appending the primary key columns to it.”，所以主键别太长。
2. 为什么mysql InnoDb下，推荐用自增ID作主索引？因为这样insert会是追加操作，对insert性能更优。另外非主索引的value存的是主键值，用自增id数字占用空间也小。
