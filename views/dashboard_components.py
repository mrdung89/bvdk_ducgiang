import math
from datetime import datetime
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout, QWidget
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QColor, QPalette, QCursor

class KPICard(QFrame):
    clicked = Signal()

    def __init__(self, title, subtitle, color, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 10px;
            }}
            QFrame:hover {{
                background-color: {self.lighten_color(color)};
            }}
        """)
        self.setMinimumHeight(120)

        layout = QVBoxLayout(self)
        
        self.lbl_subtitle = QLabel(subtitle)
        self.lbl_subtitle.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-size: 14px;")
        
        self.lbl_value = QLabel("...")
        self.lbl_value.setStyleSheet("color: white; font-size: 36px; font-weight: bold;")
        self.lbl_value.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(self.lbl_subtitle)
        layout.addWidget(self.lbl_value)
        layout.setAlignment(self.lbl_subtitle, Qt.AlignTop)

    def set_value(self, value):
        self.lbl_value.setText(str(value))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def lighten_color(self, hex_color):
        color = QColor(hex_color)
        return color.lighter(110).name()

class DashboardMachineCard(QFrame):
    clicked = Signal(str) # emits machine_name

    def __init__(self, machine_data, parent=None):
        super().__init__(parent)
        self.machine_data = machine_data
        self.machine_name = machine_data.get('ten_may', 'Unknown')
        self.machine_type = machine_data.get('loai_may', 'Unknown')
        self.status = machine_data.get('trang_thai', 'READY')
        self.start_time = machine_data.get('thoi_gian_bat_dau')
        self.duration = machine_data.get('thoi_gian_du_kien', 0)
        
        self.setFrameShape(QFrame.StyledPanel)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setFixedSize(180, 120)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(5)

        self.lbl_name = QLabel(self.machine_name)
        self.lbl_name.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        self.lbl_name.setAlignment(Qt.AlignCenter)

        self.lbl_type = QLabel(f"({self.machine_type})")
        self.lbl_type.setStyleSheet("font-size: 12px; color: rgba(255, 255, 255, 0.8);")
        self.lbl_type.setAlignment(Qt.AlignCenter)

        self.lbl_status = QLabel()
        self.lbl_status.setStyleSheet("font-size: 12px; font-weight: bold; color: white;")
        self.lbl_status.setAlignment(Qt.AlignCenter)

        self.lbl_timer = QLabel("")
        self.lbl_timer.setStyleSheet("font-size: 20px; font-weight: bold; color: yellow;")
        self.lbl_timer.setAlignment(Qt.AlignCenter)

        self.layout.addWidget(self.lbl_name)
        self.layout.addWidget(self.lbl_type)
        self.layout.addWidget(self.lbl_status)
        self.layout.addWidget(self.lbl_timer)

        self.blinking = False
        self.blink_state = True

        self.update_colors()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        if self.status == 'RUNNING' and self.start_time and self.duration:
            self.timer.start(1000)
        self.update_timer()

    def update_colors(self):
        if self.status == 'READY':
            color = "#27ae60" # green
            self.lbl_status.setText("SẴN SÀNG")
            self.lbl_timer.hide()
        elif self.status == 'RUNNING':
            color = "#e74c3c" # red
            self.lbl_status.setText("ĐANG CHẠY")
            self.lbl_timer.show()
        else:
            color = "#95a5a6" # gray
            self.lbl_status.setText("BẢO TRÌ/HỎNG")
            self.lbl_timer.hide()
            
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 10px;
            }}
            QFrame:hover {{
                background-color: {QColor(color).lighter(110).name()};
            }}
        """)

    def update_timer(self):
        if not self.start_time or not self.duration or self.status != 'RUNNING':
            return
            
        try:
            if isinstance(self.start_time, str):
                start_dt = datetime.strptime(self.start_time, '%Y-%m-%d %H:%M:%S')
            else:
                start_dt = self.start_time
                
            elapsed = (datetime.now() - start_dt).total_seconds()
            rem = (self.duration * 60) - elapsed
            
            if rem > 0:
                mins = int(rem // 60)
                secs = int(rem % 60)
                self.lbl_timer.setText(f"{mins:02d}:{secs:02d}")
                self.blinking = False
                self.lbl_timer.setStyleSheet("font-size: 20px; font-weight: bold; color: yellow;")
            else:
                self.lbl_timer.setText("00:00")
                self.blinking = True
                self.lbl_status.setText("ĐÃ HOÀN THÀNH")
                
                # Blinking effect
                if self.blink_state:
                    self.lbl_timer.setStyleSheet("font-size: 20px; font-weight: bold; color: yellow;")
                else:
                    self.lbl_timer.setStyleSheet("font-size: 20px; font-weight: bold; color: transparent;")
                self.blink_state = not self.blink_state
                
        except Exception as e:
            print("Timer error:", e)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.machine_name)
        super().mousePressEvent(event)
