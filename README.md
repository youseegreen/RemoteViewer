# Remote Viewer
RealSenseとKeigan Motorでリモートの環境を広範囲に観測するプログラム

### 準備
```config_dummy.yaml```にIPアドレス、KeiganMotorのMACアドレスを書き込んで```config.yaml```として保存

### Remote側（観測したい環境側）
```RemoteViewer/server$ python remote_server.py```

### Local側（ユーザ側）
```RemoteViewer/client$ python remote_viewer.py```
