import socket, os, sys, time, yaml, threading, cv2, numpy as np
is_available_rs = True
is_available_depth = True
try:
    import pyrealsense2.pyrealsense2 as rs
except:
    print(f"[Warning] pyrealsense2.pyrealsense2 is not installed")
    is_available_rs = False
    is_available_depth = False


class MyRealSenseCamera():
    def __init__(self, is_use_depth):
        self.is_use_depth = is_use_depth
        print(f"[RealSense] created the instance (Depth : {self.is_use_depth})")
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        pipeline_wrapper = rs.pipeline_wrapper(self.pipeline)
        pipeline_profile = self.config.resolve(pipeline_wrapper)
        device = pipeline_profile.get_device()
        print(f"[RealSense] connected device : {device}")
        # device_product_line = str(device.get_info(rs.camera_info.product_line))
        self.config.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 30)
        if self.is_use_depth:
            self.config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        # raw_rgb-d_image
        self.raw_rgb = np.zeros((1280, 720, 3), np.uint8)
        if self.is_use_depth:
            self.raw_d = np.zeros((640, 480), np.float16)
        # Start streaming
        self.kill_flag = False
        self.camera_capture_flag = False
        self.pipeline.start(self.config)
        self.thread = threading.Thread(target = self.__run__)
        self.thread.start()

    def __run__(self):
        
        while not self.kill_flag:

            if self.camera_capture_flag:
                # Wait for a coherent pair of frames: depth and color
                frames = self.pipeline.wait_for_frames()

                color_image = self.__get_color_image__(frames)
                if self.is_use_depth:
                    depth_image = self.__get_depth_image__(frames)
        
                if np.all(color_image == 0) or (self.is_use_depth and np.all(depth_image == 0)):
                    continue

                self.raw_rgb = color_image
                if self.is_use_depth:
                    self.raw_d = depth_image
                continue
            
    def read(self):
        if self.is_use_depth:
            return self.raw_rgb, self.raw_d
        else:
            return self.raw_rgb, None

    def start_camera_capture(self):
        self.camera_capture_flag = True

    def stop_camera_capture(self):
        self.camera_capture_flag = False

    def stop_thread(self):
        self.kill_flag = True
        self.thread.join()
        print(f"[CameraServer, RealSense] thread is finished")
    
    def __get_color_image__(self, frames):
        try:
            color_frame = frames.get_color_frame()
            color_image = np.asanyarray(color_frame.get_data())
        except Exception as e:
            print(f'[Warning] get_color_image : {e}')
        finally:
            return color_image

    def __get_depth_image__(self, frames):
        try:
            depth_frame = frames.get_depth_frame()
            depth_image = np.asanyarray(depth_frame.get_data())
            return depth_image
        except Exception as e:
            print(f"[Warning] get_depth_image : {e}")
        finally:
            return depth_image


class MyUSBCamera():
    def __init__(self, camera_id = 0):
        self.camera_id = camera_id
        self.camera = cv2.VideoCapture(self.camera_id)
        # raw_rgb image
        self.raw_rgb = np.zeros((100, 100, 3), np.uint8)
        # Start streaming
        self.kill_flag = False
        self.camera_capture_flag = False
        self.thread = threading.Thread(target = self.__run__)
        self.thread.start()

    def __run__(self):
        while not self.kill_flag:
            if self.camera_capture_flag:
                ret, frame = self.camera.read()
                if ret:
                    self.raw_rgb = frame

    def read(self):
        return self.raw_rgb, None

    def start_camera_capture(self):
        self.camera_capture_flag = True

    def stop_camera_capture(self):
        self.camera_capture_flag = False

    def stop_thread(self):
        self.kill_flag = True
        self.thread.join()
        print("[CameraServer, MyUSBCamera] stop_thread is finished")


class CameraServer():
    def __init__(self, camera_cfg):
        # カメラの起動
        self.is_use_depth = camera_cfg["is_use_depth"]
        self.camera_instance = None
        if camera_cfg["device"] == "REALSENS":
            if not is_available_rs:
                print(f"[Error] RealSense is not available...")
                sys.exit(-1)
            self.camera_instance = MyRealSenseCamera(self.is_use_depth)
        else:
            if self.is_use_depth:
                print(f"[Warning] Web camera does not have a depth camera...")
                self.is_use_depth = False
            self.camera_instance = MyUSBCamera(camera_cfg["device_id"])
        if not self.camera_instance:
            print(f"[Error] camera_instance is something wrong...")
            sys.exit(-1)

        # 送信する画像のフォーマット   # FIXME モノクロオプションを追加する
        self.image_width = camera_cfg["image_width"]
        self.image_height = camera_cfg["image_height"]
        self.image_quality = camera_cfg["image_quality"]
        self.fps = camera_cfg["fps"]

        # 送信サーバーの立ち上げ
        self.ip = camera_cfg["ip"]
        self.port = camera_cfg["port"]
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.ip, self.port))
        self.socket.listen(1)   
        self.socket.settimeout(3)   # FIXME  いい感じにする  
        self.kill_flag = False
        self.thread = threading.Thread(target = self.__run__)
        self.thread.start()   # FIXME start methodとstop methodを別途作りたい


    def __run__(self):

        while not self.kill_flag:

            try:
                soc, addr = self.socket.accept()  # FIXME
                
                while not self.kill_flag:

                    loop_start_time = time.time()

                    ###### 画像の取得と画像の送信 ######
                    # 画像の取得
                    rgb, depth = self.camera_instance.read()
                    # 画像の加工
                    resized_img = cv2.resize(rgb, (self.image_width, self.image_height))
                    if self.is_use_depth:   # depthはAチャンネルに埋め込む
                        resized_img = cv2.cvtColor(resized_img, cv2.COLOR_BGR2BGRA)
                        resized_img[:,:,3] = depth
                    (status, encoded_img) = cv2.imencode('.jpg', resized_img, [int(cv2.IMWRITE_JPEG_QUALITY), self.image_quality])
                    # パケット構築   # FIXME プロトコルをしっかりさせる
                    packet_body = encoded_img.tobytes()
                    # packet_header = len(packet_header).to_bytes(self.header_size, 'big')
                    # packet = packet_header + packet_body
                    packet = packet_body
                    # print(f"[INFO] {len(packet_body)}")   # Debug
                    # パケット送信
                    try:
                        soc.sendall(packet)
                    except socket.error as e:
                        print(f'[Error] Connection was lost...')
                        break   # FIXME
                    ###### 画像の取得と画像の送信 ######

                    # FPS制御
                    time.sleep(max(0, 1 / self.fps - (time.time() - loop_start_time)))

            except socket.timeout:
                # print(f"[CameraServer] Wait a client...")
                pass
            except:
                print("something wrong...")
                pass


    def start_camera_capture(self):
        self.camera_instance.start_camera_capture()

    def stop_camera_capture(self):
        self.camera_instance.stop_camera_capture()
    
    def stop_thread(self):
        self.camera_instance.stop_thread()
        self.kill_flag = True
        self.thread.join()
        self.socket.close()
        print("[CameraServer] thread is finished")


if __name__ == "__main__":

    from utils import get_conf
    from utils import MonitorMainThread

    cfg = get_conf()

    # Main Threadが強制終了した時にモジュールのThreadを止めるため
    monitor = MonitorMainThread(timeout_time=3)

    camera_module = CameraServer(cfg["camera"])
    monitor.append_module(camera_module)
    camera_module.start_camera_capture()

    disp_time = time.time()   # 動いていることをコンソールに表示する用

    while True:   # 終了はctrl+Cを想定

        # 動いていることをコンソールに表示する用
        if time.time() - disp_time > 300:
            print("[CameraServer] running...")
            disp_time = time.time()

        # 生存報告
        monitor.main_thread_is_alive()

        time.sleep(1)

    camera_module.stop_thread()
    print(f"camera_server.py is finished")
