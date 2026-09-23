from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QLabel, QStackedWidget, QFrame)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont
import qtawesome as qta

class MainWindow(QWidget):
    logout_requested = Signal()

    def __init__(self):
        super().__init__()
        # Controller will call setup_ui

    def setup_ui(self, user_data):
        self.user_data = user_data
        self.role = self.user_data.get('role', 'ADMIN')
        
        self.setWindowTitle("Hệ thống Quản lý CSSD")
        self.setMinimumSize(1200, 700)
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. Sidebar
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(250)
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setStyleSheet("""
            QFrame#Sidebar {
                background-color: #2c3e50;
            }
            QPushButton {
                background-color: transparent;
                color: white;
                text-align: left;
                padding: 15px 20px;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
            QPushButton:checked {
                background-color: #2980b9;
                font-weight: bold;
                border-left: 4px solid #3498db;
            }
            QLabel#logoLabel {
                color: white;
                font-size: 20px;
                font-weight: bold;
                padding: 20px;
            }
        """)
        
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        # Logo/Title
        full_name = self.user_data.get('full_name', 'Unknown')
        logo_label = QLabel(f"CSSD MASTER\\n{full_name}")
        logo_label.setObjectName("logoLabel")
        logo_label.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(logo_label)
        
        # Buttons
        self.nav_buttons = []
        
        self.btn_dashboard = self.create_nav_button("Tổng quan", qta.icon('fa5s.chart-pie', color='#5c6a79'))
        
        self.btn_receive = self.create_nav_button("Giao Nhận", qta.icon('fa5s.hand-holding', color='#5c6a79'))
        
        self.btn_decon = None
        self.btn_assembly = None
        self.btn_sterilize = None
        
        if self.role in ["ADMIN", "STAFF", "NV_KSNK", "LANH_DAO"]:
            self.btn_decon = self.create_nav_button("Khử nhiễm", qta.icon('fa5s.sink', color='#5c6a79'))
            self.btn_assembly = self.create_nav_button("Đóng gói", qta.icon('fa5s.box-open', color='#5c6a79'))
            self.btn_sterilize = self.create_nav_button("Tiệt khuẩn", qta.icon('fa5s.fire', color='#5c6a79'))
            
        self.btn_issue = self.create_nav_button("Cấp Phát", qta.icon('fa5s.truck', color='#5c6a79'))
        
        self.btn_reports = None
        self.btn_inventory = None
        self.btn_masterdata = None
        
        if self.role != "KHOA_LAM_SANG":
            self.btn_reports = self.create_nav_button("Báo cáo", qta.icon('fa5s.chart-bar', color='#5c6a79'))
            self.btn_inventory = self.create_nav_button("Kho & Nhập", qta.icon('fa5s.boxes', color='#5c6a79'))
            if self.role == "ADMIN":
                self.btn_masterdata = self.create_nav_button("Danh Mục", qta.icon('fa5s.cogs', color='#5c6a79'))
                
        self.btn_management = self.create_nav_button("Quản lý", qta.icon('fa5s.users-cog', color='#5c6a79'))
        self.btn_settings = self.create_nav_button("Cài đặt", qta.icon('fa5s.sliders-h', color='#5c6a79'))
            
        sidebar_layout.addStretch()
        
        self.btn_logout = self.create_nav_button("Đăng xuất", qta.icon('fa5s.sign-out-alt', color='#e74c3c'))
        self.btn_logout.setStyleSheet("color: #e74c3c;")
        self.btn_logout.clicked.connect(self.logout_requested.emit)
        
        # 2. Content Area (Stacked Widget)
        self.content_area = QStackedWidget()
        
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.content_area)

    def create_nav_button(self, text, icon=None):
        btn = QPushButton(f"  {text}")
        if icon:
            btn.setIcon(icon)
            btn.setIconSize(QSize(20, 20))
        btn.setObjectName("NavButton")
        btn.setCheckable(True)
        self.sidebar.layout().addWidget(btn)
        self.nav_buttons.append(btn)
        return btn
        
    def switch_page(self, index, button):
        if index >= 0:
            self.content_area.setCurrentIndex(index)
        for btn in self.nav_buttons:
            btn.setChecked(btn == button)

    def add_page(self, widget):
        self.content_area.addWidget(widget)
