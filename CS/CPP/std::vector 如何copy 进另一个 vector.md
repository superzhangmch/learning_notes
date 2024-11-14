# std::vector 如何copy 进另一个 vector

假设已经有一个std::vector  aaa, 现在又有一个std::vector bbb，如果把aaa中的所有元素插入到bbb的适当位置呢？

一个方法是就是用 vector 的 insert方法，还有一个方法则是用std::copy。vector 的 insert方法的效率不清楚。但是std::copy的话，则是大有讲究了。

首先要说明，这里所述的vector中的类型是简单类型，或者说是不是复杂的类型（什么SPO来着？），复杂情形，没有研究。

----

std::copy 的话，用法有大概：两种
- std::copy(aaa.begin(), aaa.end(), std::back_inserter(bbb));
- std::copy(aaa.begin(), aaa.end(), bbb.begin());

第一种，等于是循环调用bbb的push_back 或者说insert插入，循环n多遍，过程中 bbb的size是逐渐增加。这时候，copy操作比较慢。

第二种呢，其实等于是执行memcpy，会特别快。
