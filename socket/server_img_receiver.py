import base64
import json
import socket
import struct
import sys
import threading
import time

import cv2
import numpy


class ImageReceiver:
    def __init__(self, host=("0.0.0.0", 8000)):
        self.host = host
        self.socket = None
        self.mutex = threading.Lock()
        self.set_socket(self.host)

    def set_host(self, host):
        self.host = host

    def set_socket(self, host):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET,
                               socket.SO_REUSEADDR, 1)
        self.socket.bind(self.host)
        self.socket.listen(5)
        print("Server running on port:%d" % host[1])

    def _process_stream(self, client, addr):
        while True:
            try:
                # 注意！Linux平台和Windows平台对long类型的定义是不一样的！
                info = struct.unpack("I", client.recv(4))
                buffer_size = info[0]

                self.mutex.acquire()  # 线程锁
                payload_buffer = b''
                while buffer_size:  # 循环读取，此时是jpg的字节流
                    temp_buffer = client.recv(buffer_size)
                    buffer_size -= len(temp_buffer)
                    payload_buffer += temp_buffer
                self.jpg_buffer_ok = True
                payload_json = json.loads(payload_buffer)

                stream_jpg = base64.decodebytes(
                    bytes(payload_json['image'], encoding='utf-8'))
                data = numpy.frombuffer(
                    stream_jpg, dtype='uint8')  # 将字节流转为数字矩阵

                # 将jpg矩阵转为opecv numpy矩阵
                self.img = cv2.imdecode(data, 1)
                cv2.imshow("test", self.img)  # 显示帧

                if cv2.waitKey(1) == 27:  # ESC
                    self.socket.close()
                    cv2.destroyAllWindows()
                    print("放弃连接")
                    break

                # 从发送帧到解码完成的时间延迟/ms
                time_delay = int((time.time() - payload_json['time']) * 1000)

                self.mutex.release()

            except KeyboardInterrupt:
                self.socket.close()
                cv2.destroyAllWindows()
                raise

    def run(self):
        while True:  # 保证随时可以接收请求
            try:
                client, addr = self.socket.accept()
                clientThread = threading.Thread(target=self._process_stream,
                                                args=(client, addr, ))  # 有客户端连接时产生新的线程进行处理
                clientThread.start()
            except KeyboardInterrupt:
                exit()


if __name__ == "__main__":
    # 可以使用命令行填IP和端口
    IP = ""
    port = 8000
    if len(sys.argv) > 1:
        IP = sys.argv[1]
        port = int(sys.argv[2])
    webcam = ImageReceiver(host=(IP, port))
    webcam.run()
