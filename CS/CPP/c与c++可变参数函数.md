# c/c++可变参数函数


关于用法，直接上例子：
```
#include < stdio.h >
#include < stdlib.h >
#include < string >
#include < stdarg.h >

void fun(int n, ...)
{
    int i;
    va_list arg;
    va_start(arg, n); 
    // 依次取参数，根据参数类型不同，可以按类型取
    { int temp = va_arg(arg, int); printf("%d\n", temp); }
    { char * temp = va_arg(arg, char*); printf("%s\n", temp); } 
    { double temp = va_arg(arg, double); printf("%f\n", temp); } // 传入的float，即使是显式的float, 也会内部转成double，需要按double取值
    { std::string* temp = va_arg(arg, std::string*); printf("%s\n", (*temp).c_str()); } // 按指针取
    va_end(arg);
}
int main() 
{
    std::string s= "hello";
    fun(4, 4444, "22222", 1.234, &s); // 除了基本类型外，其他必须传递指针
    return 0;
}
```
