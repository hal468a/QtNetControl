# 網路切換系統 QT 版本教學 (for armv8)
此程式已成功將QT包成container，並可回傳畫面至實體電腦

### 啟動容器
```bash=
cd qtnetcontrol/
xhost +local:docker # 允許容器存取X11 server
docker-compose up
```
### 介面示意圖
![](/image/ui.png)