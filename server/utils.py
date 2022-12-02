import os
import time
import threading
import yaml


def get_conf(dir = "./", filename = "config.yaml"):
    with open(dir + os.sep + filename, "r") as f:
        cfg = yaml.safe_load(f)
    return cfg


class MonitorMainThread:
    def __init__(self, timeout_time = 10, sub_thread_modules = []):
        self.sub_thread_modules = sub_thread_modules[:]
        self.timeout_time = timeout_time
        self.last_called_time_by_main_thread = time.time()
        self.kill_flag = False
        self.thread = threading.Thread(target = self.__run__)
        self.thread.start()
    
    def __run__(self):
        while not self.kill_flag:
            if time.time() - self.last_called_time_by_main_thread > self.timeout_time:
                print(f"[Warning] [MonitorMainThread] MainThread is probably finished...")
                self.terminate_sub_thread_modules()
                self.kill_flag = True
    
    def append_module(self, module):
        self.sub_thread_modules.append(module)

    def main_thread_is_alive(self):
        self.last_called_time_by_main_thread = time.time()

    def terminate_sub_thread_modules(self):
        for module in self.sub_thread_modules:
            module.stop_thread()

    def stop_this_thread(self):
        self.kill_flag = True
        self.thread.join()

    def stop_all_threads(self):
        self.terminate_sub_thread_modules()
        self.kill_flag = True
        self.thread.join()
