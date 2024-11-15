# javascript：一些总结

1. 变量名都可以用中文。所以jquery中的```$```也就无足为怪了。
2. 局部变量一定要用```var```来修饰下，否则就变成全局变量了。
3. ```[,,]```或```{'':,'':,'':}```作为函数参数传递的时候，都是引用传递的。所以修改内部元素的值，会反映在函数调用的后面。
4. 函数也是数据类型，都可以alert出函数定义来。从而也可以作为函数参数（可以以匿名函数方式直接作为参数）。
5. ```{'':,'':,'':}```这样的关联数组其实是js的对象的一种表示方式，所以类型是object。js中定义对象也基本是这样的方式。而prototype用于做继承等高级的面向对象操作。
6. js 执行是单线程的。
7. js 的回调执行, 也就是这样执行 ```func(function(){。。。});```的时候，回调函数的执行有的时候是在func执行退出后才执行，但这往往是 ajax 之类操作导致的。自己所作出来这种形式的回调，都会在内部回调函数执行完后，才退出 func.

### 冷知识
今天才从这里 http://www.lupaworld.com/article-237669-1.html 看到的一些前端冷知识. 摘录一些吧:
1.  浏览器栏运行js:
```
alert('hello world');
```
2. 浏览器端运行html:  http://www.lupaworld.com/article-237669-1.html
3. 令html标签可以编辑: 加 contenteditable 属性:
4. css 动态编辑:
```
<!DOCTYPE html><html> <body> <style style="display:block" contentEditable > body { color: blue } </style> xxxx yyy </body> </html>
```
5. JS 不区分整数与浮点数,且实数也是浮点数:
```
alert(1.toString());  //出错, 因为当做了1.xxx 这个小数,但是 发现解析小数失败
alert(1..toString()); //OK
```
