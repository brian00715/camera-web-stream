import socket
import threading
import struct
import cv2
import time
import os
import numpy
import hmac
import base64
from hashlib import sha1
from types import SimpleNamespace
from paho.mqtt.client import MQTT_LOG_INFO, MQTT_LOG_NOTICE, MQTT_LOG_WARNING, MQTT_LOG_ERR, MQTT_LOG_DEBUG
from paho.mqtt import client as mqtt
import sys
import uuid
import time

exit_flag = 0

# >>>Aliyun MQTT Configs
instanceId = '******'  # Please use yours
accessKey = '******'  # Please use yours
secretKey = '******'  # Please use yours
groupId = 'GID_RPi_4B'
client_uuid = '00002'
client_id = groupId+'@@@'+client_uuid
mq_topic = 'pi_camera'
brokerUrl = '******'# Please use yours
use_p2p_flag = 0
server_uuid = None


class WebCamera:
    def __init__(self, resolution=(640, 480, 30)):
        # server_id = groupId+'@@@'+server_uuid

        self.client = mqtt.Client(
            client_id, protocol=mqtt.MQTTv311, clean_session=True)
        # self.client.on_log = self.on_log
        self.client.on_message = self.on_message
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        userName = 'Signature'+'|'+accessKey+'|'+instanceId
        password = base64.b64encode(
            hmac.new(secretKey.encode(), client_id.encode(), sha1).digest()).decode()
        self.client.username_pw_set(userName, password)
        # ssl设置，并且port=8883
        # client.tls_set(ca_certs=None, certfile=None, keyfile=None, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS, ciphers=None)
        self.client.connect(brokerUrl, 1883, 60)
        self.client.loop_start()

        self.resolution = resolution
        self.img_quality = 15

    def setImageResolution(self, resolution):
        self.resolution = resolution

    def _processConnection(self):
        camera = cv2.VideoCapture(0)
        # camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        camera.set(cv2.CAP_PROP_FPS, self.resolution[2])
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.img_quality]
        f = open("video_info.txt", 'a+')
        print("像素为:%d * %d FPS:%d" %
              (self.resolution[0], self.resolution[1], self.resolution[2]), file=f)
        print("打开摄像头成功", file=f)
        print("连接开始时间:%s" % time.strftime("%Y-%m-%d %H:%M:%S",
                                          time.localtime(time.time())), file=f)
        f.close()
        while(1):
            _, frame = camera.read()
            # Encoding the Frame
            _, buffer = cv2.imencode('.jpg', frame)
            # Converting into encoded bytes
            jpg_as_text = base64.b64encode(buffer)
            # Publishig the Frame on the Topic home/server
            try:
                self.client.publish(mq_topic, jpg_as_text)
            except:
                camera.release()
                f.close()
                return

    def run(self):
        clientThread = threading.Thread(
            target=self._processConnection)  # 有客户端连接时产生新的线程进行处理
        clientThread.start()

    def on_connect(self, client, userdata, flags, rc):
        print('Connected with result code ' + str(rc))
        client.subscribe('pi_camera', qos=0)
        pass

    def on_message(self, client, userdata, msg):
        pass

    def on_disconnect(self, client, userdata, rc):
        if rc != 0:
            print('连接错误！错误码: %s' % rc)
            pass

    def on_log(self, client, userdata, level, buf):
        if level == MQTT_LOG_INFO:
            head = 'INFO'
        elif level == MQTT_LOG_NOTICE:
            head = 'NOTICE'
        elif level == MQTT_LOG_WARNING:
            head = 'WARN'
        elif level == MQTT_LOG_ERR:
            head = 'ERR'
        elif level == MQTT_LOG_DEBUG:
            head = 'DEBUG'
        else:
            head = level
        print('%s: %s' % (head, buf))


def main():
    cam = WebCamera()
    cam.run()


if __name__ == "__main__":
    main()
