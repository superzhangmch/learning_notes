# 分析型数据库 doris / palo查询优化

### JOIN

doris支持4中join（见 https://blog.csdn.net/pengzhouzhou/article/details/113532889 ）：broadcast join，hash partition join，colocate join，bucket shuffle join

- 【broadcast join】：将小表发送到大表所在的每台机器，然后进行hash join操作。 explain会看到join op=BROADCAST。小表会发往大表的每一个数据节点，会有流量放大。
- 【hash partition join，也叫shuffle join】：当两张表扫描出的数据都很大时，则把数据hash到第三者机器上作hash join。explain看到的join op=PARTITIONED，就指的它。
- colocate join：两个表的切分以及查询可以在一台机器上，则执行本地join
- bucket shuffle join：大体上就是根据分桶原则，直接把右表中按桶对应传到左表数据分桶中，而不用发往左表每个分桶。（见https://github.com/apache/incubator-doris/issues/4394） (那么应该左表已经分桶)

主要用的是broadcast join和 shuffle join。


### 怎样强制指定join方式：

https://www.bookstack.cn/read/ApacheDoris-0.12-zh/c405db38bcf953a4.md#bky4wy

select * from a join b on ...: 如果doris能判定出两个表大小差距较大，无论a join b 还是b join a，都会正确地用broadcast方式直接小表推到大表作join。
如果不能判定，会选用哪种没作研究。不过如果期望强行指定，则用 from a join [shuffle|broadcast] b on ... 的方式，也就是用方括号把shuffle或broadcast括起来。注意强行broadcast的时候，是吧右表往左表推。
如果左表或右表中有子查询，则doris并不能推断出子查询的实际大小。则自己推断出的join方式可能不符，是可以用上述方式强行指定的。不过注意把小表放在右边。

note: 上面所述指定，经试验，复杂查询中（含子查询，以及多表join），并不总生效。应该是这种指定只是建议。用explain select 。。。可知join方式。

另外，如果查询显示内存不足，除非多集群机器总资源占用有限制，否则一般指的是单台机器资源不足。往往因为join的时候发生了broadcast join：这时候某表的全部发送到了另一表的节点，该表如果足够大，显然必然报内存问题。所以这时候，应该强行改为 hash join 方式。如果是多个表连续 join，就容易发生这种情况，这时候可以写成多个子查询方式。如果不报内存问题，hash join肯定是更慢一些，但是终究能出结果。
