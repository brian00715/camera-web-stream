# WebCam

本项目基于三种方法实现了USB摄像头的远程图传，均使用opencv-python作为原始图像读取接口。
测试平台为：
> 服务端：树莓派4B Rasbian buster 64bit
> 
> 客户端：Windows 10 64bit，Ubuntu 18.04 LTS 64bit
注意：由于不同系统对int、long等数据类型的长度定义不同，其他平台运行时可能会有bug。

## 目录结构
```
|-- mq 
|  |-- client.py
|  |-- server.py
|-- web 
|  |-- static //网页静态文件
|  |-- tempalates //HTML文件
|  |  |-- index.html
|  |-- server.py
|-- socket 
|  |-- client.py
|  |-- server.py
|-- readme.md
```

## 使用方法
选择一种图传方法，例如socket，在socket下打开终端，服务端运行：
```python
python3 server.py
```
客户端运行:
```python
python3 client.py
```
即可。
## 说明
1. mq目录中是基于阿里云MQTT实现的图传，实测延迟较大。优点是可以广播。
2. web目录中实现了将图像推流到本机的flask服务器上，客户端访问页面取得图传，因此所有图像处理任务尽量在服务端完成。延迟适中。
   > 存在一个小问题，由于每次访问页面都会重新声明VideoCapture对象，会导致抛出异常，服务端代码退出，因此请保证同时只有一个页面在运行。
3. socket目录中实现了基于Socket UDP的图传，延迟最小，720p分辨率可达ms级。且客户端传输得到的是jpg帧，可以在客户端自由处理图像，`client_web.py`还实现了将获取到的视频流利用客户端flask服务器显示在网页上。通过FRP穿透内网服务可以实现公网图传。缺点是目前只支持一对一传输。

## 附录
+ 还可以使用ROS借助web_video_server进行图传。
   首先安装web_video_server：
   ```shell
    sudo apt install ros-<ros distro>-web-video-server
   ```
   使用方法参考[官方说明](http://wiki.ros.org/web_video_server)。该工具包只是转发视频话题为http流，因此首先要有一个节点发布视频话题，可以直接写一个程序用OpenCV读取摄像头帧，填充`sensor_msgs/Image`数据类型然后发布到某一个话题；也可以使用`usb_cam`等ros包读取帧，并使用`theora_image_transport`包对视频进行初步压缩。