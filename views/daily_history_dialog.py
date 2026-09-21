from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QInputDialog, QMessageBox
from PySide6.QtCore import Qt

class DailyHistoryDialog(QDialog):
    def __init__(self, parent_view, db, mode, date_str):
        super().__init__(parent_view)
        self.parent_view = parent_view
        self.db = db
        self.mode = mode # 'GUI', 'DUYET', hoặc 'CAP_PHAT'
        self.date_str = date_str
        
        if mode == 'GUI': title = "Lịch sử các Khoa Gửi đồ dơ"
        elif mode == 'DUYET': title = "Lịch sử KSNK Đã Duyệt đồ dơ"
        else: title = "Lịch sử KSNK Đã Cấp Phát đồ sạch"
            
        self.setWindowTitle(f"{title} - Ngày: {date_str}")
        self.resize(700, 500)
        
        layout = QVBoxLayout(self)
        
        lbl = QLabel(f"{title.upper()} ({date_str})")
        lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(lbl)
        
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Tên Khoa", "Tổng Số Món", "Giao Dịch Cuối", "Thao Tác"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        layout.addWidget(self.table)
        
        btn_close = QPushButton("ĐÓNG")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignRight)
        
        self.load_data()

    def load_data(self):
        self.table.setRowCount(0)
        try:
            if self.mode == 'GUI':
                sql = """SELECT khoa_giao as khoa, SUM(so_luong) as tong_sl, MAX(thoi_gian) as last_time 
                         FROM lich_su_giao_nhan WHERE DATE(thoi_gian) = %s GROUP BY khoa_giao ORDER BY last_time DESC"""
            elif self.mode == 'DUYET':
                sql = """SELECT khoa_giao as khoa, SUM(so_luong) as tong_sl, MAX(thoi_gian) as last_time 
                         FROM lich_su_giao_nhan WHERE DATE(thoi_gian) = %s AND trang_thai != 'CHO_TIEP_NHAN' 
                         GROUP BY khoa_giao ORDER BY last_time DESC"""
            else: # CAP_PHAT
                sql = """SELECT khoa_nhan as khoa, SUM(so_luong) as tong_sl, MAX(thoi_gian) as last_time 
                         FROM phieu_cap_phat WHERE DATE(thoi_gian) = %s GROUP BY khoa_nhan ORDER BY last_time DESC"""
                         
            rows = self.db.fetch_all(sql, (self.date_str,))
            if not rows: return
            
            self.table.setRowCount(len(rows))
            for r, row in enumerate(rows):
                self.table.setItem(r, 0, QTableWidgetItem(row['khoa']))
                self.table.setItem(r, 1, QTableWidgetItem(str(row['tong_sl'])))
                
                tg_str = row['last_time'].strftime('%H:%M:%S') if hasattr(row['last_time'], 'strftime') else str(row['last_time'])
                self.table.setItem(r, 2, QTableWidgetItem(tg_str))
                
                btn_view = QPushButton("Xem Chi Tiết")
                btn_view.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
                btn_view.clicked.connect(lambda ch, k=row['khoa']: self.open_detail(k))
                self.table.setCellWidget(r, 3, btn_view)
        except Exception as e:
            print("Lỗi load_data DailyHistoryDialog:", e)

    def open_detail(self, khoa):
        dlg = HistoryDetailDialog(self, self.db, self.mode, khoa, self.date_str)
        dlg.exec()
        self.load_data() 

class HistoryDetailDialog(QDialog):
    def __init__(self, parent, db, mode, khoa, date_str):
        super().__init__(parent)
        self.db = db
        self.mode = mode
        self.khoa = khoa
        self.date_str = date_str
        self.setWindowTitle(f"Chi Tiết - {khoa} ({date_str})")
        self.resize(900, 600)
        
        layout = QVBoxLayout(self)
        
        lbl = QLabel(f"DANH SÁCH CHI TIẾT - {khoa.upper()}")
        lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(lbl)
        
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["ID", "Thời Gian", "Mã Đồ", "Tên Đồ", "Số Lượng", "Trạng Thái", "Thao Tác"])
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        layout.addWidget(self.table)
        
        btn_layout = QHBoxLayout()
        btn_print = QPushButton("🖨️ IN LẠI PHIẾU (EXCEL)")
        btn_print.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 8px;")
        btn_print.clicked.connect(self.reprint_excel)
        
        btn_close = QPushButton("ĐÓNG")
        btn_close.clicked.connect(self.accept)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_print)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)
        
        self.load_details()

    def load_details(self):
        self.table.setRowCount(0)
        self.items_data = []
        if self.mode == 'GUI':
            rows = self.db.fetch_all("SELECT * FROM lich_su_giao_nhan WHERE khoa_giao=%s AND DATE(thoi_gian)=%s ORDER BY thoi_gian DESC", (self.khoa, self.date_str))
        elif self.mode == 'DUYET':
            rows = self.db.fetch_all("SELECT * FROM lich_su_giao_nhan WHERE khoa_giao=%s AND DATE(thoi_gian)=%s AND trang_thai != 'CHO_TIEP_NHAN' ORDER BY thoi_gian DESC", (self.khoa, self.date_str))
        else: # CAP_PHAT
            rows = self.db.fetch_all("SELECT * FROM phieu_cap_phat WHERE khoa_nhan=%s AND DATE(thoi_gian)=%s ORDER BY thoi_gian DESC", (self.khoa, self.date_str))
            
        if not rows: return
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            ma_do = row['ma_do']
            ten_do = ma_do
            b = self.db.fetch_one("SELECT ten_bo FROM danh_muc_bo_dung_cu WHERE ma_bo=%s", (ma_do,))
            if b: ten_do = b['ten_bo']
            else:
                v = self.db.fetch_one("SELECT ten_do_vai FROM danh_muc_do_vai WHERE ma_do_vai=%s", (ma_do,))
                if v: ten_do = v['ten_do_vai']
                else:
                    d = self.db.fetch_one("SELECT ten_dc FROM danh_muc_dung_cu WHERE ma_dc=%s", (ma_do,))
                    if d: ten_do = d['ten_dc']
                    
            row['ten_do'] = ten_do
            self.items_data.append(row)
            
            tg_str = row['thoi_gian'].strftime('%H:%M:%S') if hasattr(row['thoi_gian'], 'strftime') else str(row['thoi_gian'])
            
            self.table.setItem(r, 0, QTableWidgetItem(str(row['id'])))
            self.table.setItem(r, 1, QTableWidgetItem(tg_str))
            self.table.setItem(r, 2, QTableWidgetItem(ma_do))
            self.table.setItem(r, 3, QTableWidgetItem(ten_do))
            self.table.setItem(r, 4, QTableWidgetItem(str(row['so_luong'])))
            self.table.setItem(r, 5, QTableWidgetItem(row.get('trang_thai', 'Đã cấp')))
            
            btn_edit = QPushButton("Sửa SL")
            btn_edit.setStyleSheet("background-color: #f39c12; color: white;")
            btn_edit.clicked.connect(lambda ch, pid=row['id'], cur_sl=row['so_luong']: self.edit_qty(pid, cur_sl))
            self.table.setCellWidget(r, 6, btn_edit)

    def edit_qty(self, pid, current_sl):
        new_sl, ok = QInputDialog.getInt(self, "Sửa số lượng", "Nhập số lượng thực tế:", current_sl, 0, 9999)
        if ok and new_sl != current_sl:
            try:
                if self.mode in ('GUI', 'DUYET'):
                    self.db.execute("UPDATE lich_su_giao_nhan SET so_luong=%s WHERE id=%s", (new_sl, pid))
                    self.db.execute("INSERT INTO lich_su_bien_dong (thoi_gian, nguoi_thuc_hien, bang_du_lieu, ma_item, noi_dung) VALUES (NOW(), 'KSNK', 'lich_su_giao_nhan', %s, %s)", 
                                    (pid, f"Sửa số lượng: {current_sl} -> {new_sl}"))
                else:
                    old_rec = self.db.fetch_one("SELECT so_luong, ma_do FROM phieu_cap_phat WHERE id=%s", (pid,))
                    if old_rec:
                        self.db.execute("UPDATE phieu_cap_phat SET so_luong=%s WHERE id=%s", (new_sl, pid))
                        self.db.execute("INSERT INTO lich_su_bien_dong (thoi_gian, nguoi_thuc_hien, bang_du_lieu, ma_item, noi_dung) VALUES (NOW(), 'KSNK', 'phieu_cap_phat', %s, %s)", 
                                        (old_rec['ma_do'], f"Sửa số lượng: {current_sl} -> {new_sl}"))
                        diff = old_rec['so_luong'] - new_sl
                        if diff != 0:
                            self.db.execute("UPDATE danh_muc_do_vai SET cssd_ton_thuc_te = cssd_ton_thuc_te + %s WHERE ma_do_vai=%s", (diff, old_rec['ma_do']))
                
                QMessageBox.information(self, "Thành công", "Đã cập nhật số lượng và lưu vết!")
                self.load_details()
            except Exception as e:
                QMessageBox.warning(self, "Lỗi", str(e))

    def reprint_excel(self):
        from utils.excel_reporter import ExcelReporter
        reporter = ExcelReporter(parent_view=self)
        ma_phieu = f"REPRINT-{self.date_str.replace('-','')}"
        reporter.create_distribution_receipt(self.khoa, ma_phieu, f"{self.date_str} 23:59", self.items_data, "NV KSNK (In Lại)")
