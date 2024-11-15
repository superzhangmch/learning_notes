# vim 一些设置

### 自定义语言的高亮显示
直接见：https://vim.fandom.com/wiki/Creating_your_own_syntax_files

简述下：靠三种语法实现：
1. syn keyword XXXX keyword1 keyword1  keyword1 ..
2. syn match XXXX 正则
3. syn region XXXX start='x' end='y'

