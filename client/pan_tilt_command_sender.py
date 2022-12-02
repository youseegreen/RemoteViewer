import socket
import time
import threading

class PanTiltCommandSender:
    def __init__(self, pantilt_cfg):
        self.server_ip = pantilt_cfg["ip"]
        self.server_port = pantilt_cfg["port"]
        self.interval_time = pantilt_cfg["interval_time"]
        self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.address = (self.server_ip, self.server_port)
        # thread run
        self.kill_flag = False
        self.thread = threading.Thread(target = self.__run__)
        self.thread.start()

    def __run__(self):
        ''' interval_timeごとに、PanTiltControllerにpan, tiltデータを送る '''
        while not self.kill_flag:

            loop_start_time = time.time()

            try:
                self.udp.sendto(f"{self.pan},{self.tilt}".encode(), self.address)
            except:
                pass

            elasped_time = time.time() - loop_start_time
            if self.interval_time - elasped_time > 0:
                time.sleep(self.interval_time - elasped_time)

    def set_pan_tilt(self, pan = None, tilt = None):
        ''' PanTiltControllerに送るpan, tiltの値（°）をセットする '''
        if pan:
            self.pan = pan
        if tilt:
            self.tilt = tilt

    def stop_thread(self):
        self.kill_flag = True
        self.thread.join()
        self.udp.close()
        print(f"[PanTiltCommandSender] thread is finished")

    def get_pan_tilt(self):
        print(f"[PanTiltCommandSender] pan : {self.pan}, tilt : {self.tilt}")

    def disconnect(self):
        ''' PanTiltControllerから切断する（ソケットを消す） '''
        pass