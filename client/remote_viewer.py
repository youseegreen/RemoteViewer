import argparse
import tkinter as tk
import cv2
from PIL import Image, ImageTk, ImageOps  # 画像データ用
from pan_tilt_command_sender import PanTiltCommandSender
from image_receiver import ImageReceiver


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', 
                        '--ip',
                        type=str,
                        default="127.26.16.1",
                        help='Server IP')
    parser.add_argument('-c', 
                        '--camera',
                        type=int,
                        default=50000,
                        help='port number of CameraServer')
    parser.add_argument('-p', 
                        '--pantilt',
                        type=int,
                        default=50001,
                        help='port number of PanTiltController')
    args = parser.parse_args()
    return args


class RemoteViewer(tk.Frame):
    def __init__(self, image_instance, pantilt_instance, 
                 window_width = 800, window_height = 520):
        self.viewer = tk.Tk()
        super().__init__(self.viewer)

        self.image_instance = image_instance
        self.pantilt_instance = pantilt_instance

        # 基本設定
        self.window_width = window_width
        self.window_height = window_height
        self.viewer.geometry(f'{self.window_width}x{self.window_height}')
        self.viewer.title("RemoteViewer")
        self.viewer.protocol("WM_DELETE_WINDOW", self.delete_window)

        # RGB(-D)画像表示用
        H = 20
        self.canvas_width = self.window_width
        self.canvas_height = self.window_height - H
        self.canvas_centor_x = (int)(self.window_width / 2)
        self.canvas_centor_y = (int)(self.window_height / 2) + H
        self.canvas = tk.Canvas(self.viewer)
        self.canvas.pack(expand = True, fill = tk.BOTH)
        self.disp_image()

        # パンモータ制御スライダー
        self.pan_slider = tk.DoubleVar()
        pan_slider = tk.Scale(self.viewer, 
                    variable = self.pan_slider, 
                    command = self.pan_slider_scroll,
                    orient=tk.HORIZONTAL,   
                    length = (int)(self.window_width / 2),           # 全体の長さ
                    width = H,             # 全体の太さ
                    sliderlength = H,      # スライダー（つまみ）の幅
                    from_ = 0,            # 最小値（開始の値）
                    to = 90,               # 最大値（終了の値）
                    resolution=1,         # 変化の分解能(初期値:1)
                    tickinterval=10         # 目盛りの分解能(初期値0で表示なし)
                    )
        pan_slider.place(x=0, y=0)  # 左上の座標
        # チルトモータ制御スライダー
        self.tilt_slider = tk.DoubleVar()
        tilt_slider = tk.Scale(self.viewer, 
                    variable = self.tilt_slider, 
                    command = self.tilt_slider_scroll,
                    orient=tk.HORIZONTAL,   
                    length = (int)(self.window_width / 2),           # 全体の長さ
                    width = H,             # 全体の太さ
                    sliderlength = H,      # スライダー（つまみ）の幅
                    from_ = 0,            # 最小値（開始の値）
                    to = 90,               # 最大値（終了の値）
                    resolution=1,         # 変化の分解能(初期値:1)
                    tickinterval=10         # 目盛りの分解能(初期値0で表示なし)
                    )
        tilt_slider.place(x=(int)(self.window_width / 2), y=0)

    def pan_slider_scroll(self, event=None):
        self.pantilt_instance.set_pan_tilt(self.pan_slider.get(), None)

    def tilt_slider_scroll(self, event=None):
        self.pantilt_instance.set_pan_tilt(None, self.tilt_slider.get())

    def disp_image(self):
        # 画像の取得
        rgb, d = self.image_instance.get_image()

        # BGR→RGB変換
        cv_image = cv2.cvtColor(rgb, cv2.COLOR_BGR2RGB)
        # NumPyのndarrayからPillowのImageへ変換
        pil_image = Image.fromarray(cv_image)

        # 画像のアスペクト比（縦横比）を崩さずに指定したサイズ（キャンバスのサイズ）全体に画像をリサイズする
        pil_image = ImageOps.pad(pil_image, (self.canvas_width, self.canvas_height))

        # PIL.ImageからPhotoImageへ変換する
        self.photo_image = ImageTk.PhotoImage(image=pil_image)

        # 画像の描画
        self.canvas.create_image(
                self.canvas_centor_x,    # 画像表示位置(Canvasの中心)
                self.canvas_centor_y,                   
                image=self.photo_image  # 表示画像データ
                )

        # disp_image()を10msec後に実行する
        self.disp_id = self.after(10, self.disp_image)

    def delete_window(self):
        self.image_instance.stop_thread()
        self.pantilt_instance.stop_thread()
        self.viewer.destroy()

def main():

    cfg = parse_args()
    camera_cfg = {"ip":cfg.ip, "port":cfg.camera}
    pantilt_cfg = {"ip":cfg.ip, "port":cfg.pantilt, "interval_time":0.05}
    
    image_receiver = ImageReceiver(camera_cfg)
    pantilt_cmdsender = PanTiltCommandSender(pantilt_cfg)

    viewer = RemoteViewer(image_receiver, pantilt_cmdsender)
    viewer.mainloop()


if __name__ == "__main__":
    main()
