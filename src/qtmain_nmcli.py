import sys, time, subprocess, threading, argparse, os

from printColor import Color
from functools import partial

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel

class NetController(QWidget):
    def __init__(self):
        super().__init__()
        self.wifi_state = self.get_network_status('wlan0')
        self.eth0_state = self.get_network_status('eth0')
        self.dongle_state = self.get_network_status('usb0')
        self.ping_failures = {'wlan0': 0, 'eth0': 0, 'usb0': 0}

        self.initUI()

        self.ping_thread = threading.Thread(target=self.ping_loop)
        self.ping_thread.daemon = True
        self.ping_thread.start()
    
    # 擷取網路狀態
    def get_network_status(self, interface:str):
        try:
            result = subprocess.run(["nmcli", "device", "show", interface], capture_output=True, text=True, check=True)
            lines = result.stdout.splitlines()
            status_info = {}
            for line in lines:
                if "GENERAL.STATE" in line:
                    state = line.split(":")[1].strip()
                    status_info["State"] = state[state.find("(") + 1:state.find(")")]
                elif "IP4.ADDRESS" in line:
                    status_info["IP Address"] = line.split(":")[1].strip()
                elif "GENERAL.CONNECTION" in line:
                    status_info["Connection"] = line.split(":")[1].strip()
            return status_info
        except subprocess.CalledProcessError as e:
            return {"Error": str(e)}
    
    # 乙太網路控制
    def cable_control(self, interface, action):
        if action not in ["connect", "disconnect"]:
            raise ValueError("Invalid action. Use 'connect' or 'disconnect'.")
        try:
            subprocess.run(["sudo", "nmcli", "device", action, interface], check=True)
            return f"'Eth0' {action}ed successfully."
        except subprocess.CalledProcessError as e:
            return f"Failed to {action} Eth0. Error: {e}"
    
    # WiFi 控制
    def wlan0_control(self, action):
        if action not in ["on", "off"]:
            raise ValueError("Invalid action. Use 'connect' or 'disconnect'.")
        try:
            subprocess.run(["sudo", "nmcli", "radio", 'wifi', action], check=True)
            self.wifi_state = self.get_network_status('wlan0')
            print(f"State: {self.wifi_state['State']}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to {action} wlan0. Error: {e}")
    
    def update_status(self):
        self.wifi_state = self.get_network_status('wlan0')
        self.eth0_state = self.get_network_status('eth0')
        self.dongle_state = self.get_network_status('usb0')

        self.wifi_label.setText(f"Wifi: {self.wifi_state['State']}")
        self.eth0_label.setText(f"Eth: {self.eth0_state['State']}")
        self.dongle_label.setText(f"Dongle: {self.dongle_state['State']}")

        # 改變 Wi-Fi 狀態顏色
        if self.wifi_state.get('State') == '已連線':
            self.wifi_label.setStyleSheet("color: green;")
        else:
            self.wifi_label.setStyleSheet("color: red;")

        # 改變 Ethernet 狀態顏色
        if self.eth0_state.get('State') == '已連線':
            self.eth0_label.setStyleSheet("color: green;")
        else:
            self.eth0_label.setStyleSheet("color: red;")

        # 改變 Dongle 狀態顏色
        if self.dongle_state.get('State') == '已連線':
            self.dongle_label.setStyleSheet("color: green;")
        else:
            self.dongle_label.setStyleSheet("color: red;")

    def ping_DNS(self, interface, DNS="8.8.8.8", timeout=1):
        try:
            result = subprocess.run(["ping", "-c", "1", "-I", interface, "-w", str(timeout), DNS], capture_output=True, text=True)
            if result.returncode != 0:
                self.ping_failures[interface] += 1
                msg = f"{Color.RED}[{interface}]{Color.RED} Ping to {DNS} failed."
            else:
                msg = f"{Color.GREEN}[{interface}]{Color.GREEN} Ping to {DNS} successful."
                self.ping_failures[interface] = 0
            print(msg)
            sys.stdout.flush()
        except Exception as e:
            self.ping_failures[interface] += 1
            print(f"An error occurred while pinging via {interface}: {e}")
            sys.stdout.flush()

    def initUI(self):
        self.layout = QVBoxLayout()

        # ----------- Wifi --------------
        self.wifi_label = QLabel("Wifi: ")
        self.layout.addWidget(self.wifi_label)
        
        ## 計算wifi ping 失敗的次數
        self.wifi_ping_fail = QLabel("Ping Failures:")
        self.layout.addWidget(self.wifi_ping_fail)

        ## wifi 控制按鈕
        wifi_buttons_layout = QHBoxLayout()
        self.on_wifi_btn = QPushButton("Wifi On")
        self.on_wifi_btn.clicked.connect(partial(self.wlan0_control, 'on'))
        wifi_buttons_layout.addWidget(self.on_wifi_btn)

        self.off_wifi_btn = QPushButton("Wifi Off")
        self.off_wifi_btn.clicked.connect(partial(self.wlan0_control, 'off'))
        wifi_buttons_layout.addWidget(self.off_wifi_btn)
        
        self.layout.addLayout(wifi_buttons_layout)

        # ----------- Eth --------------
        self.eth0_label = QLabel("Eth0: ")
        self.layout.addWidget(self.eth0_label)

        ## 計算eth ping 失敗的次數
        self.eth_ping_fail = QLabel("Ping Failures:")
        self.layout.addWidget(self.eth_ping_fail)

        ## eth 控制按鈕
        eth_buttons_layout = QHBoxLayout()
        self.on_eth_btn = QPushButton("RJ45 On")
        self.on_eth_btn.clicked.connect(partial(self.cable_control, 'eth0', 'connect'))
        eth_buttons_layout.addWidget(self.on_eth_btn)

        self.off_eth_btn = QPushButton("RJ45 Off")
        self.off_eth_btn.clicked.connect(partial(self.cable_control, 'eth0', 'disconnect'))
        eth_buttons_layout.addWidget(self.off_eth_btn)
        
        self.layout.addLayout(eth_buttons_layout)

        # ----------- Dongle --------------
        self.dongle_label = QLabel("Dongle: ")
        self.layout.addWidget(self.dongle_label)

        ## 計算 Dongle ping 失敗的次數
        self.dongle_ping_fail = QLabel("Ping Failures:")
        self.layout.addWidget(self.dongle_ping_fail)

        ## Dongle 控制按鈕
        dongle_buttons_layout = QHBoxLayout()
        self.on_dongle_btn = QPushButton("Dongle On")
        self.on_dongle_btn.clicked.connect(partial(self.cable_control, 'usb0', 'connect'))
        dongle_buttons_layout.addWidget(self.on_dongle_btn)

        self.off_dongle_btn = QPushButton("Dongle Off")
        self.off_dongle_btn.clicked.connect(partial(self.cable_control, 'usb0', 'disconnect'))
        dongle_buttons_layout.addWidget(self.off_dongle_btn)

        self.layout.addLayout(dongle_buttons_layout)

        self.setLayout(self.layout)
        self.setWindowTitle('Qt Net Control')
        self.setGeometry(100, 100, 300, 200)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_status)
        self.timer.start(1000)
    
    def ping_loop(self):
        while True:
            self.ping_DNS('wlan0')
            self.ping_DNS('eth0')
            self.ping_DNS('usb0')

            print("------------------------------")
            self.update_ping_failures()
            time.sleep(1)
    
    def update_ping_failures(self):
        self.wifi_ping_fail.setText(f"Wifi ping failures: {self.ping_failures['wlan0']}")
        self.eth_ping_fail.setText(f"Eth ping failures: {self.ping_failures['eth0']}")
        self.dongle_ping_fail.setText(f"Dongle ping failures: {self.ping_failures['usb0']}")
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Network Control Application")
    parser.add_argument('--log', action='store_true', help='Show console window')
    args = parser.parse_args()

    if not args.log:
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')

    app = QApplication(sys.argv)
    ex = NetController()
    ex.show()
    sys.exit(app.exec_())