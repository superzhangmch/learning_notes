# mysql的锁

只说InnoDb引擎下的锁。

lock tables可以给表显式加锁，但这个锁不是InnoDb存储引擎上的锁。

```select ... for update``` 会在select 出结果的同时，给相关记录加锁。但是该语句需要用到事务中。

一般的```update, delete``` 操作都会导致锁。涉及到的行锁往往与index有关，如果没有相关index，就会在整个表上加锁，因此添加适当的索引非常重要。

致于具体的sql语句怎样导致加什么锁，看这里：http://dev.mysql.com/doc/refman/5.0/en/innodb-locks-set.html

<br>

另外，为了能观察到各种锁，需要把sql语句放到事务中；或者设置 ```set autocommit=0```，这时候每运行一个sql后，都需要运行一下```commit```。```for update``` 只和锁有关，只是不在事务中，往往瞬间执行完，感觉不出和锁有啥关系，所以显得和事务很有关系。
