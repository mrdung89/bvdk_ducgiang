from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QHeaderView, QPushButton
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

class AlertsDialog(QDialog):
    def __init__(self, expiries, min_stocks, parent=None):
        super().__init__(parent)
        self.expiries = expiries
        self.min_stocks = min_stocks
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Cảnh Báo Hệ Thống")
        self.setMinimumSize(800, 600)
        layout = QVBoxLayout(self)
        
        # 1. Expiry alerts
        lbl_exp = QLabel(f"ĐỒ SẮP HẾT HẠN VÔ KHUẨN ({len(self.expiries)})")
        lbl_exp.setStyleSheet("font-size: 14px; font-weight: bold; color: #c0392b;")
        layout.addWidget(lbl_exp)
        
        self.tbl_exp = QTableWidget(len(self.expiries), 5)
        self.tbl_exp.setHorizontalHeaderLabels(["Khoa", "Tên Đồ", "Trạng Thái", "Ngày Hấp", "Cảnh Báo Hạn"])
        self.tbl_exp.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_exp.setEditTriggers(QTableWidget.NoEditTriggers)
        
        for r, it in enumerate(self.expiries):
            self.tbl_exp.setItem(r, 0, QTableWidgetItem(it.get('khoa', '')))
            self.tbl_exp.setItem(r, 1, QTableWidgetItem(it.get('ten', '')))
            self.tbl_exp.setItem(r, 2, QTableWidgetItem(it.get('trang_thai', '')))
            self.tbl_exp.setItem(r, 3, QTableWidgetItem(str(it.get('ngay_hap', ''))[:16]))
            
            days_left = it.get('days_left', 0)
            status_txt = f"Còn {days_left} ngày" if days_left >= 0 else f"Quá hạn {-days_left} ngày!"
            item_status = QTableWidgetItem(status_txt)
            if days_left < 0:
                item_status.setForeground(QColor("red"))
            elif days_left <= 3:
                item_status.setForeground(QColor("#d35400"))
            self.tbl_exp.setItem(r, 4, item_status)
            
        layout.addWidget(self.tbl_exp)
        
        # 2. Min stock alerts
        lbl_stk = QLabel(f"CẢNH BÁO TỒN KHO TỐI THIỂU ({len(self.min_stocks)})")
        lbl_stk.setStyleSheet("font-size: 14px; font-weight: bold; color: #d35400;")
        layout.addWidget(lbl_stk)
        
        self.tbl_stk = QTableWidget(len(self.min_stocks), 4)
        self.tbl_stk.setHorizontalHeaderLabels(["Mã Đồ", "Tên Vật Tư", "Tồn Hiện Tại", "Mức Tối Thiểu"])
        self.tbl_stk.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_stk.setEditTriggers(QTableWidget.NoEditTriggers)
        
        for r, stk in enumerate(self.min_stocks):
            self.tbl_stk.setItem(r, 0, QTableWidgetItem(stk.get('ma_do_vai', '')))
            self.tbl_stk.setItem(r, 1, QTableWidgetItem(stk.get('ten_do_vai', '')))
            
            it_cur = QTableWidgetItem(str(stk.get('cssd_ton_thuc_te', 0)))
            it_cur.setForeground(QColor("red"))
            self.tbl_stk.setItem(r, 2, it_cur)
            
            self.tbl_stk.setItem(r, 3, QTableWidgetItem(str(stk.get('cssd_ton_toi_thieu', 0))))
            
        layout.addWidget(self.tbl_stk)
        
        btn_close = QPushButton("Đóng")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)
