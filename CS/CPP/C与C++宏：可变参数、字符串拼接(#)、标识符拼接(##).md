# C/C++宏：可变参数、字符串拼接(#)、标识符拼接(##)

### 1. 可变参数：例子
```
#define debug(cond, format, ...) \
    do {\
       if (cond) { \
           fprintf (stderr, format, ## __VA_ARGS__); \
       } \
    } while (0)
```
参：https://blog.csdn.net/Windgs_YF/article/details/80660592

### 2. 字符串拼接(#)
 若：  
```
#define str_cat(xx) printf("xxx" # xx);
```
则： 
```
str_cat(11); => xxx11
str_cat("11"); => xxx"11"
```

若：
```
#define str_cat(xx) print (#xx)
```
则 ```str_cat(xx)``` 相当于 ```print("xx")```

### 4. 标识符拼接(##)
```
#define keyword_var_cat(xx) pri##xx("xxx");
```
则：```keyword_var_cat(ntf) ```等于执行``` printf("xxx"); ```

若：
```
#define do_concat(middle) pre##middle##suffix;
```
则 
```int do_concat(_a_) = 1``` 相当于 ```int pre_a_suffix = 1;```
