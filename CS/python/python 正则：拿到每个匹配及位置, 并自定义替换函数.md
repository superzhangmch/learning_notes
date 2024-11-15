# python 正则：拿到每个匹配及位置, 并自定义替换函数

拿到匹配的子串，经过某函数处理后，返回处理后的字符串

### 方法一：自己获取match项的起始位置，然后自己处理

解析出匹配项：
```
   pat = re.compile("([a-zA-Z0-9]{6,})") # 按该模式扣除词
   arr= [] 
   for match in re.finditer(pat, input):
       s = match.start()
       e = match.end()
       arr.append([s, e, input[s:e]])
```
作替换：        
```
       for i in xrange(len(arr) - 1, -1, -1):
          start, end, match_word= arr[i]
          input = input[:start] + match_word + str(len(match_world))+ input[end:] # 对于扣出的词，作替换
```

### 方法二：用re.sub的回调替换函数
```
pat = re.compile("([0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9] [0-9][0-9]:[0-9][0-9]:[0-9][0-9])") # 匹配一个0000-00-00 00:00:00这样的时间
def call_back_func(match):
       match_arr = match.groups()   # 正则的括号中的东西
       match_txt = match.group() # 匹配到的文本片段
       sec = date2unix_sec(match_arr[0]) # date2unix_sec: 日期转时间戳
       return str(sec)
pat.sub(call_back_func, "now is 2019-09-09 09:09:09 ")
```
