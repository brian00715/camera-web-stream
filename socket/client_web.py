import socket
import struct
import time

from flask import Flask, render_template, Response

# flask部分===========================================================================

app = Flask(__name__)
WAN_IP = ["82.157.153.61", 6002]
LAN_IP = ["10.128.230.229", 7999]


class Receiver:
    def __init__(self, resolution=(640, 480, 30), remote_address=(LAN_IP[0], LAN_IP[1]), windows_name="video"):
        self.remote_address = remote_address
        self.resolution = resolution
        self.name = windows_name
        self.img_quality = 60  # 图片质量，并不是帧数 [0,95]
        self.connect()
        self.socket.send(struct.pack(
            "qhhh", self.img_quality, self.resolution[0], self.resolution[1], self.resolution[2]))

    def _set_socket(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def connect(self):
        self._set_socket()
        self.socket.connect(self.remote_address)

    def get_frame(self):
        # 注意！Linux平台和Windows平台对long类型的定义是不一样的！
        info = struct.unpack("qhhh14s", self.socket.recv(28))
        buffer_size = info[0]
        img_sent_time = float(info[4])
        if buffer_size:
            self.jpg_buffer = b''
            while buffer_size:  # 循环读取，此时是jpg的字节流
                tempBuf = self.socket.recv(buffer_size)
                buffer_size -= len(tempBuf)
                self.jpg_buffer += tempBuf
            time_delay = int((time.time() - img_sent_time) * 1000)  # 从服务器发送帧到解码完成的时间延迟/ms
            return self.jpg_buffer


def gen_frames(camera):  # generate frame by frame from camera
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: img/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result


@app.route('/video_feed')
def video_feed():
    # Video streaming route. Put this in the frame_check_header attribute of an img tag
    return Response(gen_frames(Receiver()), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')


# END flask部分===========================================================================


if __name__ == "__main__":
    app.run(debug=True)
