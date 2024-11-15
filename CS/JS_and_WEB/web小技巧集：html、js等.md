# web小技巧集：html、js等

以下都就 jquery 而言。

### 如果要频繁加载一个视频中的不同图片，作浏览，怎么办？
一个方法是抽图，并存放图；加载的时候直接加载图片。

另一个方式是，这时候可以直接加载视频。然后指定播放到指定的图片。仿佛展示了图片。
具体做法是（chrome下有效）：
```
var video_obj = $("video").get(0); video_obj .currentTime = XXX
```
则显示XXX秒除的图片，另外也可以用video_obj.currentTime获知当前播放到了多少秒了。跳到制定帧后，可以用video元素的oncanplay史剑来获知已经真正加载成功。

另外，```video_obj.play()``` 则开始播放，```video_obj.pause()``` 则停止播放。

假设帧率是每秒30帧，则每次 ```video_obj.currentTime``` 累加1/30,则是推进1帧。

video标签的相关control属性去掉后，则没有播放控件，仿佛就是图片

### 视频抽帧：如果要把视频中的任一图片抽取出来怎么处理 
```
var canvas = $('canvas').get(0);
var video = $('video').get(0);
canvas.height = ...; canvas.width = ...;
canvas.getContext('2d').drawImage(video, ... 其他参数 ...);
```
其他参数指定了从原始视频帧的什么地方开始扣取，以及扣取多大的图片，在canvas什么地方开始绘制。具体看中drawImage怎么用。

### html的video中视频帧的分辨率 
```
$("video").get(0).videoWidth, $("video").get(0).videoHeight
```

### html的radio/checkbox 标签怎样用jquery控制选中，反选？怎么知道选了哪个？ 
反选或者选中具体的radio：

选中name=radio0的radio组的第j个radio:
```
$("input:radio[name=radio0]").get(j).checked = true;
```
反选name=radio0的radio组的第j个radio:
```
$("input:radio[name=radio0]").get(j).checked = false;
```

反选所有radio group的所有radio：
```
$("input:radio[name=radio0]").attr('checked', false); // 无论有多少个，一次全反选
```

怎样知道选中了哪一个？
```
var choosed_val = $("input:radio[name=radio0]:checked").val();
```
假设每个radio都已经赋value属性。则用以上可以获得备选radio的value


点选了radio后，再移动方向键，则方向键老绕着这组 radio转。怎么别这样？
可以在radio上加click事件：```onclick='this.blur()'``` 即可

checkbox 是否被选中：
```
$(checkbox_obj).is(':checked')
```

### 怎样禁用input 标签怎样启用 
置为不可用：
```
$("input[type=radio]").attr("disabled",true);
```
置为可用：
```
$("input[type=checkbox]").attr("disabled",true);
```

### 数组作排序，删除元素 
排序：
```
function sort_func(a,b){ var a1 = parseInt(a); var b1 = parseInt(b); if (a1 大于 b1) { return 1; }else if(a1 小于 b1){ return -1 }else{ return 0; } }
```
然后: ```arr.sort(sequence); ```, 则arr就会排好序了

数组删除第一个元素：
```
Array.prototype.remove = function(val) { var index = this.indexOf(val); if (index 大于 -1) { this.splice(index, 1); } };
```
然后数组自动有remove方法

### 字符串作trim 
```
String.prototype.trim = function() {return this.replace(/(^\s*)|(\s*$)/g, "");}
```
然后数组自动有trim方法

### css 控制让鼠标变手的形状 
```
cursor:pointer;font-weight:bold
```

### 定时器 
```
var timer = null;
function stop_play() {
   if (timer) {
      window.clearInterval(timer);
       timer = null;
   }
}
function do_play() {
     // do something 
     timer = setTimeout('do_some_func()', 多少毫秒后执行);
}
```

### 按键控制某些事 
```
$(function () {
      $(document).keydown(function(e){
          var code=e.which;
           switch (code) {  
               case 37: // 上方向键
         // do something
                  break;  
               case 39: // 下方向键
     // do something
                  break;  
               case 32: // 空格
                   // do something
                  break;  
              default:  
                 return;  
          }
       });
   });  
```

### ajax 极简例子 
```
// 不能操作()
$.ajax({
        type: 'POST',
        url: "URL",
        data: req_JSON_data,
        dataType: 'json',
        success : function(result) {
          var o = eval_r(result);
          if (o.status != 0) {
             ;
             // 能操作();
          } else {
             edited = 0;
             // 能操作();
             // do some thing
          }
        },
        error:function(msg){
          alert('提交失败：' + msg.responseText);
          // 能操作();(
        }
       });
```

### 窗口有变，自适应某些东西 
```
$(document).ready(function(){
$(window).resize(function() {
     // 做你要做的事
  });
  });
```

### 令一个div内的内容，超高后，变得可滚动 
```
<div style='position:relative;' >
  <div style='height:滚动框高度;overflow:auto;' id='tab_content'>
    这里是内部内容
  </div>
</div>
```
自适应窗口高度：
```$("#tab_content").css("height", (document.body.clientHeight - 50)+"px");```
代码控制滚动到内部内容得pos=x得位置：
```
$("#tab_content").scrollTop(x);
```

### 跨域的解决 
被跨域访问的web url，提供特殊的http header即可。这时候访问方会发送两次请求，第一次作试探，如果返回允许跨域，则第二次发起请求。

具体的header是（php代码形式）：
```
  header('Access-Control-Allow-Origin:http://a.b.c.d:8822'); // 需要http://和端口都有
   header('Access-Control-Allow-Credentials: true');
    // header('Access-Control-Allow-Methods:POST');
   header('Access-Control-Max-Age:1800');
   header('Access-Control-Allow-Headers:x-requested-with,content-type');
   header('Content-Type:application/json;charset=utf-8');
```

### php下怎么获取post的json数据 
```
$pssted_json_str = file_get_contents('php://input');
```

### 获取浏览器窗口的高度 
用：```window.innerHeight```，这样可以用来自适应显示

### 超链接anchor 怎样令不可点 
不可点：
```
$(...).css('pointer-events','none');
```
可点：
```
$(...).css('pointer-events','auto');
```

### js怎样保存文件为excel(csv) 
特别地对于UTF8:
```
var data ="CSV文件内容"; 
var encodedUri = "data:text/csv;charset=utf-8, 百分号 EF 百分号 BB 百分号 BF" + encodeURI(data);
var link = document。createElement_x_x（"a");
link.setAttribute("href", encodedUri);
link.setAttribute("download", name + ".csv");
link.click();
```
注意：EFBBBF 是BOM头，表示是utf8，这样打开后不会乱码

### 怎样定位到右上角 
```
css: position=fixed；right=0px; top=0px;
```

### 当前焦点所在的元素： 
```
$(document.activeElement).get(0).tagName
```

### 背景透明，内容不透明 
https://blog.csdn.net/tyleraxin/article/details/44488579
```
style='background-color:rgba(0,0,0,0.8);'
```

### 怎样作复制 
https://www.zhihu.com/question/448395679/answer/1771019846
```
const input = document.createElement_x_x_x('input')
document.body.a(input); 
input.value = 'hello world'; // 复制到剪切板的内容 
input.select(); 
if (document.execCommand) {
document.execCommand('copy'); 
      document.body.removeChild(input); alert('复制成功'); }
else { console.error('当前浏览器不支持copy'); 
 document.body.removeChild(input); }
```

### form怎样做判断，再决定是否submit 
input button的type=submit，同时form 添加onsubmit事件函数。

不过onsubmit='xxxx'的代码中，必须有```return：onsubmit='return submit_check()'```. 返回true或false。否则不生效

### 怎样判断一个变量、函数等是否已经有定义 
```
typeof aaaa == "undefined"
```

### a标签怎样通过js获得this对象。
应该用 ```href='' ``` 的方法，而不能只用```href ```。

### 怎样判断dict 元素个数
jquery:  
```
$.isEmptyObject(var_dict)
```
否则就是```for (in) ``` 循环数出来

### 怎样判断dict是否有某个key 
```
dict[key] == undefined
```
