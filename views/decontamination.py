from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QLabel, QTableWidget, QTableWidgetItem, QDateEdit, QComboBox, 
                               QTreeWidget, QTreeWidgetItem, QHeaderView)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont

class DecontaminationPage(QWidget):
    def __init__(self):
        super().__init__()
        # Controller will call setup_ui

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel("KHU VỰC KHỬ NHIỄM")
        header.setFont(QFont("Arial", 25, QFont.Bold))
        header.setStyleSheet("color: #2c3e50;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Top Bar
        top_layout = QHBoxLayout()
        
        lbl_date = QLabel("Ngày làm việc:")
        self.dt_date = QDateEdit()
        self.dt_date.setCalendarPopup(True)
        self.dt_date.setDate(QDate.currentDate())
        self.dt_date.setMinimumWidth(150)
        
        lbl_emp = QLabel("Người thực hiện:")
        self.cb_employee = QComboBox()
        self.cb_employee.setMinimumWidth(150)
        
        top_layout.addWidget(lbl_date)
        top_layout.addWidget(self.dt_date)
        top_layout.addSpacing(20)
        top_layout.addWidget(lbl_emp)
        top_layout.addWidget(self.cb_employee)
        top_layout.addStretch()
        
        layout.addLayout(top_layout)
        layout.addSpacing(10)
        
        # TreeView (Giỏ hàng - hiển thị toàn bộ đồ chờ)
        self.tree_cart = QTreeWidget()
        self.tree_cart.setHeaderLabels(["Phiên Giao Nhận / Mã đồ", "Tên đồ", "SL Chọn Khử Nhiễm"])
        self.tree_cart.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree_cart.header().setSectionResizeMode(1, QHeaderView.Stretch)
        layout.addWidget(self.tree_cart)
        
        # Bottom Actions
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        
        self.btn_manual_wash = QPushButton("Rửa thủ công")
        self.btn_manual_wash.setMinimumSize(150, 50)
        self.btn_manual_wash.setStyleSheet("background-color: #9b59b6; color: white; font-size: 16px; font-weight: bold; border-radius: 5px;")
        
        self.btn_machine_wash = QPushButton("Rửa máy 🔧")
        self.btn_machine_wash.setMinimumSize(150, 50)
        self.btn_machine_wash.setStyleSheet("background-color: #e67e22; color: white; font-size: 16px; font-weight: bold; border-radius: 5px;")
        
        bottom_layout.addWidget(self.btn_manual_wash)
        bottom_layout.addSpacing(20)
        bottom_layout.addWidget(self.btn_machine_wash)
        
        layout.addLayout(bottom_layout)
        
        # === Bảng trạng thái máy giặt ===
        layout.addSpacing(10)
        lbl_wash = QLabel("🔧 Trạng thái máy giặt:")
        lbl_wash.setStyleSheet("font-weight: bold; font-size: 14px; color: #e67e22;")
        layout.addWidget(lbl_wash)
        
        self.table_wash_machines = QTableWidget(0, 5)
        self.table_wash_machines.setHorizontalHeaderLabels(["Máy", "Chu trình", "Người vận hành", "Dự kiến xong", ""])
        self.table_wash_machines.horizontalHeader().setStretchLastSection(True)
        self.table_wash_machines.setMaximumHeight(180)
        layout.addWidget(self.table_wash_machines)
