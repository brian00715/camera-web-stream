"""集成client和server，即可主动连接服务端发送图片吗，也可等待接入后发送
"""

import enum
import socket
import cv2
import time
import base64
import json
import struct
import threading

WAN_IP = ("112.126.73.178", 8000)
LAN_IP = ("10.128.199.198", 8000)
LOCAL_IP = ("", 8000)


class TransMode(enum.Enum):
    ACTIVE = 0,  # 主动模式,向服务器发起TCP连接
    PASSIVE = 1  # 被动模式，等待服务器发起TCP连接


class ImageTrans():
    def __init__(self, resolution=(640, 480, 30), trans_mode=TransMode.ACTIVE, host=("", 9002)):
        self.resolution = resolution
        self.trans_mode = trans_mode
        self.host = host
        self.socket = None
        self.camera = None
        self.use_manual_fps_limit = False  # 使用手动帧率限制
        self.img_quality = 50
        self.start_trans_img = True
        self._set_socket()

    def _set_socket(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def trans_img_to_remote(self,current_tunnel,addr=""):
        self.camera = cv2.VideoCapture(0)
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.img_quality]

        start_time = time.time()
        while True:
            (grabbed, self.img) = self.camera.read()
            if self.use_manual_fps_limit and time.time() - start_time > 1./self.resolution[2]:
                start_time = time.time()
                self.start_trans_img = True
            if self.start_trans_img or self.use_manual_fps_limit == False:
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
                    current_tunnel.send(payload_header+payload_bytes)
                    self.start_trans_img = False
                except:
                    print("error!")
                    self.camera.release()
                    return

    def run(self):
        if self.trans_mode == TransMode.ACTIVE:  # 主动模式
            self.socket.connect(self.host)
            self.trans_img_to_remote(self.socket)
            pass
        elif self.trans_mode == TransMode.PASSIVE:  # 被动模式
            self.socket.bind(self.host)
            self.socket.listen(5)
            print("Running on port: %d" % self.host[1])
            while True:  # 保证随时可以接收请求
                try:
                    client, addr = self.socket.accept()
                    clientThread = threading.Thread(target=self.trans_img_to_remote,
                                                    args=(client, addr, ))  # 有客户端连接时产生新的线程进行处理
                    clientThread.start()
                except KeyboardInterrupt:
                    exit()
            pass


if __name__ == "__main__":
    img_trans = ImageTrans(trans_mode=TransMode.ACTIVE,host=LAN_IP)
    # img_trans = ImageTrans(trans_mode=TransMode.PASSIVE, host=LOCAL_IP)
    img_trans.run()
