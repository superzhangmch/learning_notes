# C++: 一些奇怪的关键字来由


C++ 中命名变量的时候，变量名当然肯定不能与关键字冲突。所以“int for =1;”肯定是通不过的。
 
实际上，除了一般所知道的那些关键词，你会发现还有一些词，也不能被用作变量名，比如“int and =1；”也不行。
这些词大概有这些：


|C++本来用|	也可以用|
|:-------|:--------|
&&	|and
&= |	and_eq
&	|bitand
\|	|bitor
~	|compl
!	|not
!=	|not_eq
\|\|	| or
\|=	|or_eq
^	|xor
^=	|xor_eq

实际上，它们也是算作C++关键词的，```if(a != b)``` 可以写作 ```if(a not_eq b)```。

那么为什么要引入这些东西呢？这与编码集有关。
一般的 C++ 程序是在 ascii 编码内的(不考虑字符串内的字母)。但是在早期，有些字符集甚至都没有"[]"等字符，这你让C/C++程序怎么写？于是只好对于这些字符来做转义，方法是如下表用两个字母或三个字母来表示第一列的字母:

|Primary |	Digraph	| Trigraph |
|:-------|:--------|:--------|
{	|<% |	??<
} |	%>	| ??>
[ |	<:	| ??(
]	| :>	| ??)
\#	| %:	| ??=
\ |  | ??/	

上面列出一些。这些转义与这些不寻常的关键字可以直接用在 c++ 代码中的：
```
%:include< stdio.h >  // 注意 %: 即 #
int main()
<%    // 即 {
       int and1 =1;
       printf("hello world, %d \n", 12 and 21);
       return 0;
%>    // 即 }
```
运行结果：
```
hello world, 1 
```

鉴于 “ ??/ ” 就是 “ \ ”， 那么一个副作用是， 如果一个注释行以"??/" 结尾，那么下一行也自动变成注释行了，因为被解读成“\”，表示续行了。

参考：
- http://en.cppreference.com/w/cpp/keyword
- http://en.cppreference.com/w/cpp/language/operator_alternative
- http://en.wikipedia.org/wiki/C_trigraph#C
