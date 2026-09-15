import sys

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\views\assembly.py', 'w', encoding='utf-8') as f:
    f.write('''from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import subprocess
import os

class AssemblyPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        header = QLabel("MÀN HÌNH ĐÓNG GÓI & IN TEM")
        header.setFont(QFont("Arial", 25, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        desc = QLabel("Hệ thống In tem được quản lý bởi công cụ chuyên dụng.\\nVui lòng bấm nút bên dưới để mở phần mềm thiết kế và in tem.")
        desc.setFont(QFont("Arial", 14))
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)
        
        btn_pack = QPushButton("🚀 MỞ PHẦN MỀM IN TEM")
        btn_pack.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold; font-size: 20px; padding: 20px; border-radius: 10px;")
        btn_pack.clicked.connect(self.open_intem_app)
        
        layout.addSpacing(50)
        layout.addWidget(btn_pack, alignment=Qt.AlignCenter)
        layout.addStretch()

    def open_intem_app(self):
        # Mở màn hình In Tem bằng Tkinter dưới dạng subscreen
        script_path = os.path.join(os.path.dirname(__file__), "intem_bvdk_ducgiang.py")
        subprocess.Popen(["python", script_path, "--subscreen"])
''')
