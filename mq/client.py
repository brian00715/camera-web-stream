import base64
import hmac
import os
import sys
import threading
from hashlib import sha1

import cv2
import numpy
from paho.mqtt import client as mqtt
from paho.mqtt.client import MQTT_LOG_INFO, MQTT_LOG_NOTICE, MQTT_LOG_WARNING, MQTT_LOG_ERR, MQTT_LOG_DEBUG

exit_flag = 0

instanceId = '******'  # Please use yours
accessKey = '******'  # Please use yours
secretKey = '******'  # Please use yours
groupId = 'GID_RPi_4B'
client_uuid = '00005'
client_id = groupId + '@@@' + client_uuid
mq_topic = 'pi_camera'
brokerUrl = '******'# Please use yours
use_p2p_flag = 0
server_uuid = None


class WebCamClient_MQ:
    def __init__(self, resolution=(640, 480, 24), windowName="video"):
        self.resolution = resolution
        self.name = windowName
        self.mutex = threading.Lock()
        self.img_quality = 80
        self.src = 911 + self.img_quality
        self.interval = 0
        self.path = os.getcwd()
        self.client = mqtt.Client(
            client_id, protocol=mqtt.MQTTv311, clean_session=True)
        # self.client.on_log = self.on_log
        self.client.on_message = self.on_message
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        userName = 'Signature' + '|' + accessKey + '|' + instanceId
        password = base64.b64encode(
            hmac.new(secretKey.encode(), client_id.encode(), sha1).digest()).decode()
        self.client.username_pw_set(userName, password)
        # ssl设置，并且port=8883
        # client.tls_set(ca_certs=None, certfile=None, keyfile=None, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS, ciphers=None)
        self.client.connect(brokerUrl, 1883, 60)

    def ser_window_name(self, name):
        self.name = name

    def ser_remote_address(self, remoteAddress):
        self.remoteAddress = remoteAddress

    def check_config(self):
        path = os.getcwd()
        print(path)
        f = open("video_config.txt", 'w+')
        print("w = %d,h = %d" %
              (self.resolution[0], self.resolution[1]), file=f)
        print("IP is %s:%d" %
              (self.remoteAddress[0], self.remoteAddress[1]), file=f)
        print("Save pic flag:%d" % (self.interval), file=f)
        print("img's quality is:%d,range(0~95)" %
              (self.img_quality), file=f)
        f.close()

    def on_connect(self, client, userdata, flags, rc):
        print('Connected with result code ' + str(rc))
        client.subscribe('pi_camera', qos=0)
        pass

    def on_message(self, client, userdata, msg):
        # print(msg.payload)
        img = base64.b64decode(msg.payload)
        # converting into numpy array from buffer
        npimg = numpy.frombuffer(img, dtype=numpy.uint8)
        # Decode to Original Frame
        frame = cv2.imdecode(npimg, 1)
        cv2.imshow(self.name, frame)
        if cv2.waitKey(1) == 27:  # ESC
            cv2.destroyAllWindows()
            print("放弃连接")

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


def main(argv):
    print("创建连接...")
    if len(argv) >= 4:
        cam = WebCamClient_MQ(resolution=[int(float(argv[1])), int(
            float(argv[2])), int(float(argv[3]))])
    else:
        cam = WebCamClient_MQ()
    cam.client.loop_forever()


if __name__ == "__main__":
    main(sys.argv)
