# C++ std::map 迭代器读与写同时问题

C++ std::map 迭代器读与写同时发生的时候，迭代器未必能读到最新写入的值：

```
std::map< int, int > m;
for ( int i = 0; i < 20; i++) {
             m.insert(std::make_pair(i, i));
      }
std::map< int, int>::iterator it = m.begin();
int i = 150;
       while (it != m.end() && i < 160)
      {
             printf("%d -> %d\n", it->first, it->second);
             it++;
             m.insert(std::make_pair(i, i));
             i++;
      }
```
以上，while中，并不保证把while内写入的也遍历出来。
