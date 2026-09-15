from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from models.db_manager import DBManager
from utils.printer import print_assembly_label

class AssemblyPage(QWidget):
    def __init__(self):
        super().__init__()
        self.db = DBManager()
        self.current_ma_bo = ""
        self.current_ten_bo = ""
        layout = QVBoxLayout(self)
        
        header = QLabel("ĐÓNG GÓI (CHECKLIST)")
        header.setFont(QFont("Arial", 23, QFont.Bold))
        layout.addWidget(header)
        
        scan_layout = QHBoxLayout()
        self.txt_scan = QLineEdit()
        self.txt_scan.setPlaceholderText("Quét mã bộ (VD: BO-BKR)...")
        self.txt_scan.returnPressed.connect(self.load_checklist)
        self.btn_load = QPushButton("Kiểm tra")
        self.btn_load.clicked.connect(self.load_checklist)
        scan_layout.addWidget(QLabel("Mã bộ:"))
        scan_layout.addWidget(self.txt_scan)
        scan_layout.addWidget(self.btn_load)
        layout.addLayout(scan_layout)
        
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Mã DC", "Tên DC", "SL Chuẩn", "Đóng gói"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        layout.addWidget(self.table)
        
        btn_pack = QPushButton("📦 Đóng Gói & In Tem (Barcode)")
        btn_pack.setObjectName("SuccessButton")
        btn_pack.clicked.connect(self.do_pack)
        layout.addWidget(btn_pack)

    def load_checklist(self):
        ma_bo = self.txt_scan.text().strip()
        if not ma_bo: return
        self.current_ma_bo = ma_bo
        items = self.db.get_chi_tiet_bo(ma_bo)
        if not items:
            QMessageBox.warning(self, "Lỗi", "Không tìm thấy danh mục bộ này.")
            return
            
        # Get ten_bo
        try:
            bo = self.db.fetch_one("SELECT ten_bo FROM danh_muc_bo_dung_cu WHERE ma_bo=%s", (ma_bo,))
            self.current_ten_bo = bo['ten_bo'] if bo else "Không rõ"
        except:
            self.current_ten_bo = "Không rõ"
            
        self.table.setRowCount(len(items))
        for row, item in enumerate(items):
            self.table.setItem(row, 0, QTableWidgetItem(item['ma_dc']))
            self.table.setItem(row, 1, QTableWidgetItem(item['ten_dc']))
            self.table.setItem(row, 2, QTableWidgetItem(str(item['so_luong'])))
            self.table.setItem(row, 3, QTableWidgetItem(str(item['so_luong'])))

    def do_pack(self):
        if self.current_ma_bo:
            # Show Print Dialog FIRST
            # Pass parent=self so it centers on window
            success = print_assembly_label(self, self.current_ma_bo, self.current_ten_bo, "NV KSNK")
            
            if success:
                self.db.track_set_status(self.current_ma_bo, "Unknown", "Khoa GMHS", "ASSEMBLED (Đã đóng gói)")
                QMessageBox.information(self, "Thành công", f"Đã đóng gói và in tem cho bộ {self.current_ma_bo}")
                self.table.setRowCount(0)
                self.txt_scan.clear()
            else:
                QMessageBox.warning(self, "Hủy", "Đã hủy in tem. Bộ dụng cụ chưa được đánh dấu là Đã Đóng Gói.")
