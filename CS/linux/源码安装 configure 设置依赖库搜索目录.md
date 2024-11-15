# configure: 设置依赖库搜索目录

如果有某个依赖库XXX的版本不合，往往需要自己安装一个新的版本， 这时候往往可以用 
```
./configure --with-XXX=/path1/path2/.. 
```
这样的方式把新安装的库指定进去。

但是有的时候，```./configure --help``` 会发现，并没有对XXX 提供 ```--with-XXX``` 选项，这时候怎么办呢？

用下面的方式就可以解决，这时候会让configure在搜索的时候，多搜索相应的几个目录：
```
env CPPFLAGS="-I/include/path"  LDFLAGS="-L/lib/path"  ./configure --prefix=/... 
```
以上也可以把env省掉，直接写
```
CPPFLAGS="-I/include/path"  LDFLAGS="-L/lib/path"  ./configure --prefix=/...
```

【补充】
还有一个环境变量：LIBRARY_PATH 用于指定编译期间搜索lib库的路径（用“：”分割），会先搜索该变量指定的路径，找不到才去系统默认搜索路径搜索。
而 LD_LIBRARY_PATH 则用于指定程序运行期间查找so动态链接库的搜索路径。

### configure：怎么把 LD_LIBRARY_PATH 内容 build 进可执行文件
背后的 gcc 需要加上-rpath选项。configure 中，需要加上类似 --enable-rpath 这样的选项。
