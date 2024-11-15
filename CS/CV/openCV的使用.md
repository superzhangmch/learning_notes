# openCV的使用

这里所说是c++版本的opencv

### 1. 读取不到视频文件怎么办
opencv按照好后，用 VideoCapture 来打开视频时，可能什么错也不报，就是读取不到。这时候应该用isOpened()方法来判断是否打开成功。当然往往返回false。

原因出在opencv依赖的ffmpeg没安装好或者没联编进opencv。为此，cmake 安装时，需要把 -D WITH_FFMPEG=ON 参数打开，例子：
```
cmake -D WITH_CUDA=OFF \
           -D CMAKE_BUILD_TYPE=Release \
           -D CMAKE_INSTALL_PREFIX=/home/XXXX/XXXXX/ \
           -D WITH_FFMPEG=ON  \
           -D WITH_IPP=OFF  \
           -D BUILD_TESTS=OFF \
           -D BUILD_PERF_TESTS=OFF \
           -D INSTALL_PYTHON_EXAMPLES=OFF \
           -D INSTALL_C_EXAMPLES=OFF \
           -D BUILD_EXAMPLES=OFF ../opencv-3.4.9
```

但是这不会保证ffmpeg就绪。cmake 的输出结果中，需要扫描下 FFMPEG 是否满足：
```
--   Video I/O:
--    DC1394:                  NO  
--    FFMPEG:                   YES # 这里必须时YES才行
--      avcodec:                YES (58.134.100)
--      avformat:               YES (58.76.100)
--      avutil:                 YES (56.70.100)
--      swscale:                YES (5.9.100)
--      avresample:              YES (4.0.0)
--    GStreamer:               NO  
--    v4l/v4l2:                 YES (linux/videodev2.h)
```

如果对应位置不是YES，从cmake文件中查找遇到啥异常了，对应修复即可。

(实际中，还有其他细节，不过当时操作时没记下来。比如FFMPEG=NO时的那个报错，好不容易消除的。怎么消除的忘记了。好像时版本问题。总之opencv-4.5.5 与 ffmpeg-4.4.1，经测试，是配合的)

### 2. 与python版接口的区别
c++版与python版，函数名一模一样，参数也几乎一模一样（我所看到的唯一差别是，如果设计到输出，python是直接作为函数的返回值，而c++版作为其中一个参数）

### 3. 保存成视频
```
VideoWriter video_out(out_file_name, fourcc, out_fps, 长宽);  video_out << frame;
```
特别注意: 
- (1). 没有参数来控制输出文件的比特率。想来内部会不怎么压缩，以留给其他工具比如ffmpg来作进一步处理。
- (2). out_fps 控制给它的这些帧当作怎样的fps来处理。如果本来fps=60，这里按30，则最终得到的是慢镜头视频。

### 4. 怎样拿到视频/图片帧
用VideoCapture实例的read(frame)可以把帧读入frame，或者imread读到图片内容。

### 5. 怎样修改帧内容
尽量用opencv的内置函数来处理，速度会很快。如果自己来for循环做处理，往往性能大打折扣。
假设要自己亲自逐像素修读写，则方法是：
- 方法一：对RGB（好像opencv其实用的是BGR）三通道，可以 ```auto pixel = frame.at(行号, 列号); pixel.val[idx]``` 来拿到每个channel的值。修改后 ```frame.at(行idx，列idx) = pixel```来完成改写。
- 方法二： frame.data 是内部数据的指针。所以也可以直接操作这里。

可以自定义如下一个类型，然后把frame.data 强转化为该类型后，就可以直接frame_data[行][列]来直接访问了：
```
typedef unsigned char uint_8_IMG_ROW_COL_CHANNEL3_t[总行数][总列数][通道数比如3];
```
（note：数据存储格式是先行，再列，再通道数据）

### 6. 怎样拿到视频的高与宽，以及通道数
```
image_frame.rows;  // 高
image_frame.cols; // 宽
image_frame.channels(); // 通道数
```
或者 frame.type() 也能拿到通道信息。但是需要看对照表，或者用type的定义拿到具体信息。

有透明层的图片，是可能通道数为4的。

### 7. 对于RGBA四通道的图片，怎么拿到图片的四个通道？
imread必须指定 IMREAD_UNCHANGED 参数，才能拿到所有通道。

拿到后通道拆分（split):
```
std::vector《Mat》 arr_channels;
split(ori_image_frame, arr_channels);
```

然后把RGB部分重新组装：
```
std::vector《Mat》 arr_channels_bgr； 
arr_channels_bgr.push_back(xx); // xx = 0, 1, 2
merge(arr_channels_bgr, bgr_output_frame); 
```

### 8. 类型转换
```
in_frame.convertTo(out_frame, 转化到的类型比如CV_32FC3);
```
在比如前后背景图片合成时，alpha时float类型的，于是需要先把frame 数据转为float。

10. 得到空frame
==========
Mat::zeros(长宽, 类型);

