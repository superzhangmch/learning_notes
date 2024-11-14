# std::sort 用法小结

std::sort 的第三个参数应该是个比较函数或者仿函数（下全称为比较函数）。

我们知道无论什么排序，都是需要一个比较函数的。一般比较函数返回值是三类， > 0, = 0, < 0。然后也容易知道可以从此来做排序。

对于 std::sort 它需要的比较函数的返回值却是一个 bool， 只能是 true 或是 false， 不能是别的。因此这个比较函数才有了讲究起来，否则不能正常排序。
这个讲究就是，它的返回值就看是不是true！如果返回true，那么说明在排序结束后，比较函数的第一个参数对应的元素会排在第二个参数对应元素后。如果返回false，注意了！！不代表第一个参数会排第二个参数后！！
实际上是，这个比较函数是应该满足一个叫做严格若排序的。具体这里不说了。

参考：
http://blog.csdn.net/rekrad/article/details/7960864

另外，如果要用std::sort 来排序一个container， 那么这个container 是有一些要求的， 要求其有一个Random-access iterators。

参考如下：
http://www.cplusplus.com/reference/algorithm/sort/
