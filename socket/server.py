import socket
import threading
import struct
import cv2
import time
import os
import numpy


class webCamera:
    def __init__(self, resolution=(640, 480, 30), host=("", 7999)):
        self.resolution = resolution
        self.host = host
        self.socket = None
        self.camera = None
        self.use_manual_fps_limit = False  # 使用手动帧率限制
        self.img_quality = 50
        self.start_process_img = True
        self.setSocket(self.host)

    def setImageResolution(self, resolution):
        self.resolution = resolution

    def setHost(self, host):
        self.host = host

    def setSocket(self, host):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET,
                               socket.SO_REUSEADDR, 1)
        self.socket.bind(self.host)
        self.socket.listen(5)
        print("Server running on port:%d" % host[1])

    def recv_config(self, client):
        info = struct.unpack("qhhh", client.recv(14))
        self.img_quality = int(info[0])
        if not(self.img_quality > 1 and self.img_quality <= 100):
            return 0
        self.resolution = list(self.resolution)
        self.resolution[0] = info[1]
        self.resolution[1] = info[2]
        self.resolution[2] = info[3]
        if sum(self.resolution) < 1:
            return 0
        self.resolution = tuple(self.resolution)
        return 1

    def _processConnection(self, client, addr):
        if(self.recv_config(client) == 0):
            return
        self.camera = cv2.VideoCapture(0)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
        self.camera.set(cv2.CAP_PROP_FPS, self.resolution[2])
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.img_quality]
        real_props = [self.camera.get(cv2.CAP_PROP_FRAME_WIDTH), self.camera.get(
            cv2.CAP_PROP_FRAME_HEIGHT), self.camera.get(cv2.CAP_PROP_FPS)]  # 读取相机的真实配置，检查是否设置成功

        f = open("video_info.txt", 'a+')
        print("Got connection from %s:%d" % (addr[0], addr[1]), file=f)
        print("像素为:%d * %d FPS:%d" %
              (self.resolution[0], self.resolution[1], self.resolution[2]), file=f)
        print("打开摄像头成功", file=f)
        print("连接开始时间:%s" % time.strftime("%Y-%m-%d %H:%M:%S",
                                          time.localtime(time.time())), file=f)
        f.close()
        print("相机重置成功...")
        print("-- %dx%d FPS:%d" %
              (real_props[0], real_props[1], real_props[2]))

        if self.resolution[2] != real_props[2]:  # 设置失效，相机不支持此帧率，采用手动方法
            self.use_manual_fps_limit = True
            start_time = time.time()
        else:
            self.use_manual_fps_limit = False

        while(1):
            (grabbed, self.img) = self.camera.read()
            if self.use_manual_fps_limit and time.time() - start_time > 1./self.resolution[2]:
                start_time = time.time()
                self.start_process_img = True
            if self.start_process_img or self.use_manual_fps_limit == False:
                result, self.jpg_frame = cv2.imencode(
                    '.jpg', self.img, encode_param)  # 编码为jpg帧
                self.imgdata = self.jpg_frame.tostring()  # 十六进制字节流
                now_time = str("%14.3f" % time.time()).encode()  # 每帧都打上时间戳
                self.frame_header = struct.pack("qhhh14s", len(self.imgdata),
                                                self.resolution[0], self.resolution[1], self.resolution[2], now_time)
                try:
                    # 发送图片信息(图片长度, 分辨率, 图片内容)
                    client.send(self.frame_header+self.imgdata)
                    self.start_process_img = False
                except:
                    f = open("video_info.txt", 'a+')
                    print("%s:%d disconnected!" % (addr[0], addr[1]), file=f)
                    print("连接结束时间:%s" % time.strftime("%Y-%m-%d %H:%M:%S",
                                                      time.localtime(time.time())), file=f)
                    print("****************************************", file=f)
                    self.camera.release()
                    f.close()
                    return

    def run(self):
        while(1):  # 保证随时可以接收请求
            client, addr = self.socket.accept()
            clientThread = threading.Thread(target=self._processConnection,
                                            args=(client, addr, ))  # 有客户端连接时产生新的线程进行处理
            clientThread.start()


def main():
    cam = webCamera()
    cam.run()


if __name__ == "__main__":
    main()
