# python PIL 图片处理库使用小结

### 怎样安装PIL
下载PIL包，解压后，```python setup.py install```

### 怎样打开图片
```
from PIL import Image
img_obj = Image.open(src) # 打开文件
img_obj = Image.new("RGB", (width, height), "white") # 建立新文件。 黑白图则"RGB" => "L",  \
                                                     # 见 http://effbot.org/imagingbook/concepts.htm#mode 。第三个参数是初始化颜色
```

### 怎样保存图片
```
img_obj.save(file_name)
```

### 怎样得到图片的长与宽
```
width, height = img_obj.size
```

### 怎样把图片按像素转为数组表示
```
list(img_obj.getdata())
```
返回数组。单色图，则元素是数字，彩色图比如RGBA， 则元素是 [R,G,B,A], 
用list转化为python数组才可读
```
np.array(list(img_obj.getdata())) => .shape == 单色：(width* height, 1)；png彩图：(width* height, 4)
```

### 怎样放缩图片
```
img_obj = img_obj.resize((resize_width_size, resize_height_size), Image.BILINEAR)
```

### 怎样图片转灰度
```
img_obj = img_obj.convert("L")
```
其中 L = R * 299/1000 + G * 587/1000 + B * 114/1000 而得到。

### 怎样得到图片的单个像素取值
```
ret = img_obj.getpixel((i, j)) # i, j 是行列取值
```
若 image.mode == 'RGBA'，  ret = (R, G, B, A), A 表示透明度

若图片已经是灰度图，则ret是一维数。

或者.getdata() 整体读到一个数组里，然后取颜色值

### 怎样得到彩色图片的多个颜色图层
```
img_obj.split()
```
返回的是不同图层的数组，每个数组save后就得到图层的图了。

### 怎样对图片取反色 (参见)
```
from PIL import Image
import PIL.ImageOps   
image = Image.open('your_image.png')
if image.mode == 'RGBA':
    r,g,b,a = image.split()
    rgb_image = Image.merge('RGB', (r,g,b))
    inverted_image = PIL.ImageOps.invert(rgb_image)
    r2,g2,b2 = inverted_image.split()
    final_transparent_image = Image.merge('RGBA', (r2,g2,b2,a))
else:
    inverted_image = PIL.ImageOps.invert(image)
```

### 怎样塞数据以生成图片
```
img_obj.putpixel((i,j),(R, G, B))
```
或
```
img_obj.putdata(..)
```
, putdata 参数应该是 ```data[width*height][3]``` 这样的数组。

参见：http://effbot.org/imagingbook/image.htm
