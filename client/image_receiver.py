import socket
import threading
import numpy as np
import cv2

class ImageReceiver:
    def __init__(self, camera_cfg):
        self.raw_rgb = np.zeros((100, 100, 3), np.uint8)  # FIXME No Image Data等の画像に変える
        self.raw_d = np.zeros((100, 100), np.uint8)
        cv2.putText(self.raw_rgb, "No Image", (10, 50), 1, 1, (255, 255, 255), 1)
        cv2.putText(self.raw_d, "No Image", (10, 50), 1, 1, 255, 1)

        self.server_ip = camera_cfg["ip"]
        self.server_port = camera_cfg["port"]
        print(f"[ImageReceiver] Connect to CameraServer : {self.server_ip}, {self.server_port}")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.socket.settimeout(3)  # FIXME
        # thread run
        self.kill_flag = False
        self.thread = threading.Thread(target = self.__run__)
        self.thread.start()

    def __run__(self):
        ''' CameraServerに接続し、カメラ画像をゲットし続ける '''
        while not self.kill_flag:
            ''' connect the server '''
            try:
                self.socket.connect((self.server_ip, self.server_port))
                while not self.kill_flag:
                    try:
                        # FIXME データが分かれてやってきた場合に合成するようにする
                        data = self.socket.recv(100000)
                        img = np.frombuffer(data, dtype=np.uint8)
                        tmp = cv2.imdecode(img, cv2.IMREAD_UNCHANGED)
                        if type(tmp) != type(None):
                            self.raw_rgb = tmp
                    except:
                        # FIXME Scoketを閉じて再度connectする
                        break

            except socket.timeout:
                pass
            except:
                pass

    def stop_thread(self):
        self.kill_flag = True
        self.thread.join()
        self.socket.close()
        print(f"[ImageReceiver] thread is finished")

    def get_image(self):
        ''' CameraServerから送られてきた最新のRGB(-D)画像を返す '''
        return self.raw_rgb, self.raw_d

    def disconnect(self):
        ''' CameraServerから切断する '''
        pass