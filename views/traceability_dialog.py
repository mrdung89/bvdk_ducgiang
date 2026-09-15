from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
                               QFrame, QScrollArea, QWidget)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor

class TraceabilityDialog(QDialog):
    def __init__(self, title, items, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(900, 600)
        self.items = items
        
        layout = QVBoxLayout(self)
        
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(lbl_title)
        
        # Table to list items
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Tên / Mã", "SL", "Nhận", "Hấp", "Cấp Phát"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        
        layout.addWidget(self.table)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_close = QPushButton("ĐÓNG")
        btn_close.setMinimumWidth(100)
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)
        
        layout.addLayout(btn_layout)
        
        self.populate_table()

    def populate_table(self):
        self.table.setRowCount(len(self.items))
        for r, item in enumerate(self.items):
            # item_name
            name = f"[{item.get('loai_goc', '')}] {item.get('ten', '')}"
            self.table.setItem(r, 0, QTableWidgetItem(name))
            
            # SL
            self.table.setItem(r, 1, QTableWidgetItem(str(item.get('so_luong', 1))))
            
            trace = item.get('trace', {})
            
            # Nhận
            nhan = trace.get('nhan')
            if nhan:
                txt = f"{nhan.get('thoi_gian', '')} - {nhan.get('khoa', '')}\nNV: {nhan.get('nhan_vien', '')}"
                it = QTableWidgetItem(txt)
                it.setForeground(QColor("#27ae60"))
            else:
                it = QTableWidgetItem("Chưa nhận")
                it.setForeground(QColor("#7f8c8d"))
            self.table.setItem(r, 2, it)
            
            # Hấp
            hap = trace.get('hap')
            if hap:
                txt = f"{hap.get('thoi_gian', '')} - {hap.get('ten_may', '')}\nNV: {hap.get('nhan_vien', '')}"
                it = QTableWidgetItem(txt)
                it.setForeground(QColor("#c0392b"))
            else:
                it = QTableWidgetItem("Chưa hấp")
                it.setForeground(QColor("#7f8c8d"))
            self.table.setItem(r, 3, it)
            
            # Cấp
            cap = trace.get('cap')
            if cap:
                txt = f"{cap.get('thoi_gian', '')} - {cap.get('khoa', '')}\nNV: {cap.get('nhan_vien', '')}"
                it = QTableWidgetItem(txt)
                it.setForeground(QColor("#2980b9"))
            else:
                it = QTableWidgetItem("Chưa cấp")
                it.setForeground(QColor("#7f8c8d"))
            self.table.setItem(r, 4, it)
        
        self.table.resizeRowsToContents()
