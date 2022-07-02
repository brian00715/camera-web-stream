import socket
import threading
import struct
import cv2
import time
import os
import numpy
import base64
import json


class webCamera:
    def __init__(self, resolution=(640, 480, 30), host=("", 9002)):
        self.resolution = resolution
        self.host = host
        self.socket = None
        self.camera = None
        self.use_manual_fps_limit = False  # 使用手动帧率限制
        self.img_quality = 50
        self.start_process_img = True
        self.set_socket(self.host)

    def set_image_resolution(self, resolution):
        self.resolution = resolution

    def set_host(self, host):
        self.host = host

    def set_socket(self, host):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET,
                               socket.SO_REUSEADDR, 1)
        self.socket.bind(self.host)
        self.socket.listen(5)
        print("Server running on port:%d" % host[1])

    def recv_config(self, client):
        """从客户端接收相机配置参数

        Args:
            client (object): 客户端的socket对象

        Returns:
            int: 如果参数正确就返回1
        """
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

    def _process_connection(self, client, addr):
        # if(self.recv_config(client) == 0):
        #     return

        # 设置相机参数
        self.camera = cv2.VideoCapture(0)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
        self.camera.set(cv2.CAP_PROP_FPS, self.resolution[2])
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.img_quality]
        real_cam_props = [self.camera.get(cv2.CAP_PROP_FRAME_WIDTH), self.camera.get(
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
              (real_cam_props[0], real_cam_props[1], real_cam_props[2]))

        if self.resolution[2] != real_cam_props[2]:  # 设置失效，相机不支持此帧率，采用手动方法
            self.use_manual_fps_limit = True
            start_time = time.time()
        else:
            self.use_manual_fps_limit = False

        while True:
            (grabbed, self.img) = self.camera.read()
            if self.use_manual_fps_limit and time.time() - start_time > 1./self.resolution[2]:
                start_time = time.time()
                self.start_process_img = True
            if self.start_process_img or self.use_manual_fps_limit == False:
                result, self.jpg_array = cv2.imencode(
                    '.jpg', self.img, encode_param)  # 将ndarray矩阵编码为jpg矩阵
                stream_jpg = self.jpg_array.tobytes()  # 编码为jpg字节流
                stream_base64 = base64.encodebytes(stream_jpg)  # 编码为base64字节流
                now_time = time.time()  # 每帧都打上时间戳
                payload_dic = {
                    "time": now_time,
                    "resolution": self.resolution,
                    "location": "none",
                    "image": str(stream_base64, encoding='utf-8')
                }

                json.dumps(payload_dic)
                payload_bytes = bytes(json.dumps(
                    payload_dic), encoding='utf-8')  # 转为json后再变成字节流
                payload_header = struct.pack(
                    "I", len(payload_bytes))  # 标记负载大小，防止粘包
                try:
                    client.send(payload_header+payload_bytes)
                    print(payload_header+payload_bytes)
                    exit(0)
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
        while True:  # 保证随时可以接收请求
            try:
                client, addr = self.socket.accept()
                clientThread = threading.Thread(target=self._process_connection,
                                                args=(client, addr, ))  # 有客户端连接时产生新的线程进行处理
                clientThread.start()
            except KeyboardInterrupt:
                exit()


def main():
    cam = webCamera()
    cam.run()


if __name__ == "__main__":
    main()
