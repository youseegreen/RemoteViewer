import time
from utils import get_conf
from utils import MonitorMainThread
from pan_tilt_controller import PanTiltController
from camera_server import CameraServer


def main():

    # args = parse_args()
    cfg = get_conf()

    # Main Threadが強制終了した時にモジュールのThreadを止めるため
    monitor = MonitorMainThread(timeout_time=3)

    if cfg["pantilt"]["is_use"]:
        pantilt_module = PanTiltController(cfg["pantilt"])
        monitor.append_module(pantilt_module)
        pantilt_module.start_motor_control()

    if cfg["camera"]["is_use"]:
        camera_module = CameraServer(cfg["camera"])
        monitor.append_module(camera_module)
        camera_module.start_camera_capture()

    disp_time = time.time()   # 動いていることをコンソールに表示する用

    while True:   # 終了はctrl+Cを想定

        # 動いていることをコンソールに表示する用
        if time.time() - disp_time > 300:
            print("[RemoteServer, main] running...")
            disp_time = time.time()

        # 生存報告
        monitor.main_thread_is_alive()

        time.sleep(1)

    print(f"[RemoteServer] remote_server.py is finished")


if __name__ == "__main__":

    main()
