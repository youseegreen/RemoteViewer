import time, threading, sys, socket
is_available_motors = True
try:
    from pykeigan import blecontroller
    from pykeigan import utils
    # from pykeigan import controller
except:
    print(f"[Error] pykeigan is not installed")
    is_available_motors = False
    # sys.exit(-1)


class UdpReceiver():

    def __init__(self, hostname, port, buff_size = 100):
        self.pan = 0
        self.tilt = 0
        self.buff_size = buff_size
        self.address = (hostname, port)
        # bind
        self.udp_host = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_host.bind(self.address)        
        self.udp_host.settimeout(10)
        # run
        self.kill_flag = False
        self.thread = threading.Thread(target=self.__run__)
        self.thread.start()


    def __run__(self):

        while not self.kill_flag:

            try:
                data, self.addr = self.udp_host.recvfrom(self.buff_size)
                pan, tilt = str(data.decode()).split(',')
                self.pan = (int)(pan)
                self.tilt = (int)(tilt)
            except socket.timeout:
                # print(f"[PanTiltController] udp_host.recvfrom : timeout")
                pass
            except:
                pass


    def stop_thread(self):
        self.kill_flag = True
        self.thread.join()
        self.udp_host.close()
        print("[PanTiltController, UDP] thread is finished")


    def get_data(self):
        return self.pan, self.tilt

    
class PanTiltController():
    def __init__(self, pantilt_cfg):
        self.ip = pantilt_cfg["ip"]
        self.port = pantilt_cfg["port"]
        print(f"[PanTiltController] Creating a UDP Socket : ({self.ip}, {self.port})")
        self.udp = UdpReceiver(self.ip, self.port, 100)

        # 制御を行う間隔
        self.interval_time = pantilt_cfg["interval_time"]
        # 1秒間に動かせる最大の角度
        self.maxangle_per_sec = pantilt_cfg["maxangle_per_sec"]
        # 1制御あたり動かせる最大の角度
        self.maxangle_per_control = self.interval_time * self.maxangle_per_sec
        # Pan & Tilt Motor Max Address
        self.pan_mac = pantilt_cfg["pan_motor_mac_address"]
        self.tilt_mac = pantilt_cfg["tilt_motor_mac_address"]
        if is_available_motors:   # FIXME Try catchにも対応させる
            # パンチルトモータの取得
            print(f"[PanTiltController] Exploring the motors...")
            self.pan_motor = blecontroller.BLEController(self.pan_mac)
            self.tilt_motor = blecontroller.BLEController(self.tilt_mac)        
            print(f"[PanTiltController] Found the motors")   # FIXME
            # 安全装置
            self.pan_motor.enable_action()
            self.tilt_motor.enable_action()
            # 動作速度（1秒間に何rad動くか）
            self.pan_motor.set_speed(self.maxangle_per_sec * 3.141592 / 180.0)
            self.tilt_motor.set_speed(self.maxangle_per_sec * 3.141592 / 180.0)
            # 現在位置の座標を0に設定 # FIXME
            self.pan_motor.preset_position(0)
            self.tilt_motor.preset_position(0)
        else:
            print(f"[Warning] PanTilt Motors are not available...")
        # 目標の角度
        self.target_tilt = 0.0
        self.target_pan = 0.0
        # self.target_panとself.target_tiltに追従スタート
        self.kill_flag = False
        self.motor_control_flag = False
        self.thread = threading.Thread(target=self.__run__)
        self.thread.start()


    # self.pan, self.tiltに追従させる
    def __run__(self):

        while not self.kill_flag:

            loop_start_time = time.time()
            
            # get the target pan & tilt angles from the udp
            pan, tilt = self.udp.get_data()
            if pan is not None and pan != self.target_pan:
                self.target_pan = pan  # 目標の更新
                if self.motor_control_flag:
                    self.pan_motor.stop_doing_taskset()  # 現在のタスクを取り消し
                    self.pan_motor.move_to_pos(utils.deg2rad(self.target_pan))  # 再度指令を出す
            if tilt is not None and tilt != self.target_tilt:
                self.target_tilt = tilt  # 目標の更新
                if self.motor_control_flag:
                    self.tilt_motor.stop_doing_taskset()  # 現在のタスクを取り消し
                    self.tilt_motor.move_to_pos(utils.deg2rad(self.target_tilt))  # 再度指令を出す

            # 制御する時間になるまで待機
            time.sleep(max(0, self.interval_time - (time.time() - loop_start_time)))


    def start_motor_control(self):
        self.motor_control_flag = True
        if not is_available_motors:
            print(f"[Warning] PanTilt Motors are not available...")
            self.motor_control_flag = False


    def stop_motor_control(self):
        self.motor_control_flag = False


    def stop_thread(self):
        self.udp.stop_thread()
        self.kill_flag = True
        self.thread.join()
        print(f"[PanTiltController] Finished the thread")


if __name__ == "__main__":


    from utils import get_conf
    from utils import MonitorMainThread

    cfg = get_conf()

    # Main Threadが強制終了した時にモジュールのThreadを止めるため
    monitor = MonitorMainThread(timeout_time=3)

    pantilt_module = PanTiltController(cfg["pantilt"])
    monitor.append_module(pantilt_module)
    pantilt_module.start_motor_control()

    disp_time = time.time()   # 動いていることをコンソールに表示する用

    while True:   # 終了はctrl+Cを想定

        # 動いていることをコンソールに表示する用
        if time.time() - disp_time > 300:
            print("[PanTiltController] running...")
            disp_time = time.time()

        # 生存報告
        monitor.main_thread_is_alive()

        time.sleep(1)

    pantilt_module.stop_thread()
    print(f"pan_tilt_controller.py is finished")
