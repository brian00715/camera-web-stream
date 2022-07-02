# WebCam

Author: Simon Kenneth

[中文文档](./README_CN.md)

This project realizes the remote image transmission of USB camera based on three methods, all of which use opencv-python as the original image reading interface.

Tested Plarform：
> Client：Raspberry Pi 4B - Rasbian buster 64bit
> 
> Server：Windows 10 64bit，Ubuntu 18.04 LTS 64bit
Note：Because different systems have different length definitions for data types , such as int and long, there may be some bugs running on the other platforms. 

## Project Structure
```
|-- mq 
|  |-- client.py
|  |-- server.py
|-- web 
|  |-- static     // page statics files
|  |-- tempalates // HTML files
|  |  |-- index.html
|  |-- server.py
|-- socket 
|  |-- client.py
|  |-- server.py
|-- readme.md
```

## Use
Select a streaming method, such as socket. Launch a terminal under socket, and launch this for server:
```python
python3 server.py
```
Launch this for client:
```python
python3 client.py
```

## Note
1. The MQ directory is based on Alibaba cloud MQTT, and the measured delay is large. The advantage is that it can be broadcast and asynchronous. Please replace your accessKey, accessSecret and other parameters when using。
2. The web directory realizes the image streaming to the local flask server, and the client accesses the page to get the image transmission, so all image processing tasks should be completed on the server as far as possible. The delay is moderate.
   > There is a small problem that every time you visit the page, the program redeclares the `VideoCapture` object, which will cause an exception to be thrown and the server code to exit. Therefore, please ensure that only one page is running at the same time。
3. The socket directory realizes image transmission based on socket UDP, with minimum delay and 720p resolution up to **ms level**. And the JPG frame transmitted by the client can be processed freely on the client. `client_web.py ` also realizes the display of the obtained video stream on the web page using the client flask server. Through FRP intranet penetration service, public network streaming can be realized. The disadvantage is that currently only one-to-one transmission is supported

## Appendix
+ You can also use ROS for streaming using `web_video_server`
   First install web_video_server：
   ```shell
    sudo apt install ros-<ros distro>-web-video-server
   ```
   Using method refers to [Official Instructions](http://wiki.ros.org/web_video_server). The toolkit only forwards video topics as HTTP stream. Therefore, a node should publish video topics at first. You can directly write a program to read camera frames with OpenCV and fill `sensor_msgs/Image` data type and then publish to a topic. You can also use `usb_cam` and other ROS packets read frames and use `theora_image_transport` package preliminarily compresses the video frame for lower transmission bandwidth.