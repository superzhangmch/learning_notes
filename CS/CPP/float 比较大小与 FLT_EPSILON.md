# float 比较大小与 FLT_EPSILON

先说明，说的都是 IEEE 754 32bit 浮点数，64 位 double 相应类似。

我们一般知道float 比较大小的时候，一般会用一个比较小的数（一般命名为EPSILON）来卡一下，差绝对值在这个数内，那么就认为是相等：
```
#define EPSILON 0.000001
if (fabs(a - b) < EPSILON) {
   // equal
} else {
   // not equal
}
```
那么这个 EPSILON 值怎么选取呢？有一个系统宏 FLT_EPSILON(在 float.h中定义)，看起来用 FLT_EPSILON 就是了，毕竟这个是最精准的。

于是从此，每当浮点数比较的时候，如果随便写，就是简单定义为 0.000001 等，如果认真点，就是用 FLT_EPSILON。从来没有怀疑过这点。直到今天遇到一个坑，终于把这一点，算是弄清楚了。

先说结论：**float 比较大小的时候，确实需要用一个 EPSILON 来卡，但是具体取值，需要根据实际情况来定，而不是简单用 FLT_EPSILON。** 实际上，大部分时候用 FLT_EPSILON 是错误的。

实际上，FLT_EPSILON 表示最小的浮点数使得 1 + FLT_EPSILON != 1。如果不是1，而是2,3， 或者 0.5， 0.1 那么所对应的 FLT_EPSILON 的具体取值是不一样的。一般 n + flt_epsilon != n的n越大，flt_epsilon 取值也越大，n越小（比如是小数，很小的小数），flt_epsilon 取值也越小。

另外，从浮点数二进制内存表示角度看，假设有 float a =1 + FLT_EPSILON ， b = 1.0;  那么 a- b == FLT_EPSILON , 这时候是不存在一个float c， c的取值在 a 与 b 之间的。这样卡 FLT_EPSILON 也是没有啥意义的。

实际上，需要比较的时候，需要你内心清楚实际误差情况，然后自己定出 EPSILON 来卡的。

下面附上一个坑所在：
```
struct xx_t { int i; float f; };
class Cmp {
   bool operator(xx_t left, xx_t right)
   {
      // 先按 float 排序，如果相同，则按 int 排序
      if (fabs(left.f - right.f) >= EPSILON) { // 比较相等的时候，卡 EPSILON
         return left.f > right.f;
      } else {
         return left.i > right i;
      }
   }
};
std::sort(begin, end, Cmp());
```
上面是有坑的（撞上后 sort就崩溃，出core了）。就因为不同的具体float值，其实对应不同的EPSILON，实际上，不能用卡EPSILON方式来简单这样排序：你不知道具体的这个float取值是多少，那么怎么也卡不出来。
