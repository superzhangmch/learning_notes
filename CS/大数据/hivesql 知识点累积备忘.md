# hivesql 知识点累积备忘

### 1. join条件
必须是等号，不能是不等号。因为难以翻译成map-reduce

### 2. 大表join小表
如果小表内的关联字段的取值在大表中分布不均匀，则会造成数据倾斜：reduce数据不均匀，速度极慢。这时候可以用select / * + mapjoin (s) * / aaa, bbb,... from big_table join small_table ... 方式。或者对于小表的特定值，分成两个sql查询
若是left outer join，则mapjoin不会生效
 
### 3. join的时候，如果两个表的字段类型不同：
一个是string，一个是int。则对于string会强制转成int，从而对于非数字，可能转化失败而统一当比如0处理，这时候也会引起数据倾斜问题。

### 4. join的时候，左表不存在的行也保留:
用 左表 left outer join （== left join）右表。outer 是默认的。

### 5. 自身join，注意点：
自身 left outer join 自身，"left outer join"不会发挥作用。因为，总能join成功。不会出现左边有值，右边无值的情况。这时候必须作为左表和右边的同一个表，先做数据过滤。

### 6. join的on条件和where条件的关系：
至少逻辑上是这样的：join的时候，先生成临时表，on是用来控制临时表生成的。生成后，用where再做过滤。

### 7. 如果需要扩展功能，可以自己写一个程序，接受stdin，输出stdout。然后用transform机制
“transform （input字段列表） using 自己程序 as（输出字段）”（可参看 https://blog.csdn.net/u013385925/article/details/78780798 ）

### 8. 按条件过滤后求总数
```
select count(distinct case when 条件 then XX else NULL end) as cnt
```
则会过滤出XX后，再去重，再计数

### 9. 按条件求总数
sum(when 条件 then XX else 0 end) as total

### 10. 引用自定义字段：MAP/TRANSFORM
```
MAP field1, field2, ... field_n  USING 'python aa.py' AS Field1, Field2, ... Field_m FROM ... WHERE ...
```

```field1, field2, ... field_n ```是 ```FROM ... WHERE ... ```的输出；会作为 ```python aa.py ```的sys.stdin的输入，而sys.stdout会传给```Field1, Field2, ... Field_m```

### 11.  semi join, anti join:
semi join （把一个表用另一个表作过滤，而不是作join，然后输出过滤后的该表的行）相当于：
```
select * from a semi join b on a.id = b.id
```
相当于
```
select a.* from a join (
select distinct a.id form a
) b on a.id = b.id
```

anti join (把一个表join另一个表后不存在的该表的行输出)相当于:
```
select a.* from a left outer join b on a.id = b.id where b.id is null
```
anti join 大体如此，实际和上面略有差别，用的时候对比下。

参考：

https://www.linkedin.com/pulse/quick-card-apache-hive-joins-kumar-chinnakali： hive各种join

