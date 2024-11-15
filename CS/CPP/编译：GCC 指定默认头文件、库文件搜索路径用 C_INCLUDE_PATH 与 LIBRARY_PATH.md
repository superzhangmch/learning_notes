# 编译：GCC 指定默认头文件、库文件搜索路径用 C_INCLUDE_PATH 与 LIBRARY_PATH

gcc -I 或者 gcc -L 用于命令行方式指定头文件、库文件的搜索路径。如果是源码安装一些东西，发生了找不到头文件、库文件的时候，用的makefile直接编译还好；如果是用的configure，甚至其他的来生成makefile，或者有的时候，甚至都不知道怎么编译出来的。这时候就傻了。

这时候，可以用C_INCLUDE_PATH、CPLUS_INCLUDE_PATH（for c++）、LIBRARY_PATH作为环境变量来指定GCC的相应搜索路径。

另外，环境变量CPPFLAGS、LDFLAGS等用于makefile。
