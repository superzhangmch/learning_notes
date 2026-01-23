### schema-less
microsoft-comos-db 的每条记录就是一个 JSON 文档, 它不是列存储的。这个意义上说，就是个 key=> val数据库。但是他的所有字段，甚至包括内部的嵌套字段，都会自动建索引（除非你显式禁止）。从而可以支持到各种复杂的操作（从而支持 sql 查询）。

所以说, 它其实是没有 schema 的. schema 是在代码中定义出的, cosmos本身无感. 

### 读写成本

假设一个记录是个大的 json. 你只是要做 `select tab.some_int_field from table where id=xxx`, 这时候, 引擎背后也是读取整个json, 然后抽取出这个int 字段. 如果是筛选出很多的 id 集合(`select tab.some_int_field from table where id in ...`), 那么背后的数据读取特别大.

cosmos 的计费标准是 RU/s, 也就是从磁盘等存储设备的 io 吞吐. 这样, 对于上面的情况, 一次操作, 其实成本很大. 所以, 这时候表的单记录数据不能太大. (但是cosmos db 的 container——也就是一个表, 计费时有最低收费, 所以并不是因此就建但记录很小的表就行)

Cosmos 的 RU ≠ 返回数据大小(即不是占用的网络带宽大小), RU ≈ 读 + 反序列化 + 索引命中 + 执行路径

### 读写速度

它的速度还是很快的, 足以用于大流量的线上服务(也就是用 redis 的地方, 好多时候也可以用它). 

### 分区存储

它是分区存储的. 读写优化, 需要用到这点.

