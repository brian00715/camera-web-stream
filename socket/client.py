import os
import socket
import struct
import sys
import threading
import time

import cv2
import numpy

WAN_IP = ["82.157.153.61", 6002]
LAN_IP = ["10.128.230.229", 7999]
web_cam = None


class WebCamClient:
    def __init__(self, resolution=(640, 480, 30), remote_address=(LAN_IP[0], LAN_IP[1]), windows_name="video",
                 stream2web=False):
        self.remote_address = remote_address
        self.resolution = resolution
        self.name = windows_name
        self.mutex = threading.Lock()
        self.img_quality = 95  # 图片质量，并不是帧数 [1,95]
        self.interval = 0
        self.path = os.getcwd()
        self.jpg_buffer_ok = False
        self.jpg_buffer = None
        self._stream2web = stream2web
        self.connect()

    def _set_socket(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def connect(self):
        self._set_socket()
        self.socket.connect(self.remote_address)

    def _process_image(self):
        self.socket.send(struct.pack(
            "qhhh", self.img_quality, self.resolution[0], self.resolution[1], self.resolution[2]))
        while True:
            try:
                # 注意！Linux平台和Windows平台对long类型的定义是不一样的！
                info = struct.unpack("qhhh14s", self.socket.recv(28))
                buffer_size = info[0]
                img_sent_time = float(info[4])
                if buffer_size:
                    self.mutex.acquire()  # 线程锁
                    self.jpg_buffer = b''  #
                    while buffer_size:  # 循环读取，此时是jpg的字节流
                        tempBuf = self.socket.recv(buffer_size)
                        buffer_size -= len(tempBuf)
                        self.jpg_buffer += tempBuf
                    self.jpg_buffer_ok = True
                    if not self._stream2web:
                        data = numpy.frombuffer(
                            self.jpg_buffer, dtype='uint8')  # 将字节流转为数字矩阵
                        # 将jpg矩阵转为opecv numpy矩阵
                        self.img = cv2.imdecode(data, 1)
                        cv2.imshow(self.name, self.img)
                        if cv2.waitKey(1) == 27:  # ESC
                            self.socket.close()
                            cv2.destroyAllWindows()
                            print("放弃连接")
                            break
                    # 从服务器发送帧到解码完成的时间延迟/ms
                    time_delay = int((time.time() - img_sent_time) * 1000)
                    # print("delay: %d ms" % time_delay)
                    self.mutex.release()
            except KeyboardInterrupt:
                self.socket.close()
                cv2.destroyAllWindows()
                raise

    def start_get_img(self, interval=0):
        showThread = threading.Thread(target=self._process_image)
        showThread.start()
        if interval != 0:  # 非0则启动保存截图到本地的功能
            saveThread = threading.Thread(
                target=self._save_pic_to_local, args=(interval,))
            saveThread.setDaemon(1)
            saveThread.start()

    def ser_window_name(self, name):
        self.name = name

    def ser_remote_address(self, _remote_address):
        self.remote_address = _remote_address

    def _save_pic_to_local(self, interval):
        while True:
            try:
                self.mutex.acquire()
                path = os.getcwd() + "\\" + "savePic"
                if not os.path.exists(path):
                    os.mkdir(path)
                cv2.imwrite(path + "\\" + time.strftime("%Y%m%d-%H%M%S",
                                                        time.localtime(time.time())) + ".jpg", self.img)
            except:
                pass
            finally:
                self.mutex.release()
                time.sleep(interval)

    def check_config(self):
        path = os.getcwd()
        print(path)
        f = open("video_config.txt", 'w+')
        print("w = %d,h = %d,fps = %d" %
              (self.resolution[0], self.resolution[1], self.resolution[2]), file=f)
        print("IP is %s:%d" %
              (self.remote_address[0], self.remote_address[1]), file=f)
        print("Save pic flag:%d" % (self.interval), file=f)
        print("img's quality is:%d,range(0~95)" %
              (self.img_quality), file=f)
        f.close()


def main(argv):
    global web_cam
    print("创建连接...")
    if len(argv) >= 4:
        web_cam = WebCamClient(resolution=(int(float(argv[1])), int(
            float(argv[2])), int(float(argv[3]))))
    else:
        web_cam = WebCamClient()
    web_cam.check_config()
    print("像素为:%d * %d" % (web_cam.resolution[0], web_cam.resolution[1]))
    print("目标ip为%s:%d" %
          (web_cam.remote_address[0], web_cam.remote_address[1]))
    web_cam.start_get_img()


if __name__ == "__main__":
    main(sys.argv)
