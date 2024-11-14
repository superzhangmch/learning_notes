# mysql 怎样批量导出数据

mysqldump 或者 ```select into outfile``` 导出，并不那么好用，有各种限制。特别是对于线上 mysql server，是不能随便让你导出的。

- 要想安全导出，得分成多个select 结合 limit 分批次导出。
- 如果是静态表， ```select count(*)``` 估计出条数，然后多次limit 就导出了。
- 如果是数据一直在动态变的，就不能简单地limit了——有可能忽然删除了数据，于是下一次select limit的时候，可能会跳过某些数据，或者添加了数据，又会导致数据重复。
  这时候，正确做法是，```select * from table where``` 你的过滤条件 and 主键 >= 上一次的最大主键值  order by 主键 limit x, x
  如此导出的数据，不一定是任何时刻的镜像，但对于本次新改动的行，能保证下一次被导出来。否则，容易出现某些行，总是导不出来。

考虑有3列的一个表： id, update_time, data。如果每天增量导出，会按update_time = 'today' 过滤条件导出。如果不按以上方法，可能某条记录最后一次更新时间是今天，正好被跳过，于是再也导不出了。
