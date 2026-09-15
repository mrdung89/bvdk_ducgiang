from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget, 
                               QMessageBox, QInputDialog, QDialog, QFormLayout, QLineEdit)
from models.db_manager import DBManager
from PySide6.QtGui import QFont
from datetime import datetime
from utils.ui_helpers import get_autocomplete_input

class InventoryExtraPage(QWidget):
    def __init__(self):
        super().__init__()
        self.db = DBManager()
        self.db.setup_dovai_advanced()
        
        # Ensure tu_truc_khoa exists
        self.db.execute('''CREATE TABLE IF NOT EXISTS tu_truc_khoa (
            id INT AUTO_INCREMENT PRIMARY KEY,
            khoa VARCHAR(100),
            ma_do VARCHAR(100),
            so_luong INT DEFAULT 0,
            UNIQUE KEY (khoa, ma_do)
        )''')
        
        layout = QVBoxLayout(self)
        
        lbl = QLabel("CSSD MASTER: QUẢN LÝ DANH MỤC & TỒN KHO")
        lbl.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(lbl)
        
        self.tabs = QTabWidget()
        
        self.tab_dung_cu = QWidget()
        self.setup_dung_cu_tab()
        self.tabs.addTab(self.tab_dung_cu, "Danh mục Dụng cụ")
        
        self.tab_do_vai = QWidget()
        self.setup_do_vai_tab()
        self.tabs.addTab(self.tab_do_vai, "Danh mục Đồ vải (Nâng cao)")
        
        self.tab_bo = QWidget()
        self.setup_bo_tab()
        self.tabs.addTab(self.tab_bo, "Danh mục Bộ dụng cụ")
        
        layout.addWidget(self.tabs)
        
        self.setup_audit_table()
        self.load_all_data()
        
    def setup_audit_table(self):
        self.db.execute('''CREATE TABLE IF NOT EXISTS lich_su_bien_dong (
            id INT AUTO_INCREMENT PRIMARY KEY,
            thoi_gian DATETIME DEFAULT CURRENT_TIMESTAMP,
            nguoi_thuc_hien VARCHAR(100),
            bang_du_lieu VARCHAR(100),
            ma_item VARCHAR(100),
            noi_dung TEXT
        )''')

    def log_audit(self, bang, ma_item, noi_dung):
        self.db.execute("INSERT INTO lich_su_bien_dong (nguoi_thuc_hien, bang_du_lieu, ma_item, noi_dung) VALUES (%s, %s, %s, %s)", 
                        ("ADMIN", bang, ma_item, noi_dung))

    def setup_dung_cu_tab(self):
        layout = QVBoxLayout(self.tab_dung_cu)
        hl = QHBoxLayout()
        btn_add = QPushButton("➕ Thêm mới Dụng cụ")
        btn_add.clicked.connect(lambda: self.add_item('dung_cu'))
        hl.addWidget(btn_add)
        hl.addStretch()
        layout.addLayout(hl)
        
        self.table_dc = QTableWidget(0, 5)
        self.table_dc.setHorizontalHeaderLabels(["Mã DC", "Tên DC", "Tổng Nhập", "Lưu Hành", "Tồn KSNK"])
        self.table_dc.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_dc.itemDoubleClicked.connect(lambda item: self.edit_cell(item, 'danh_muc_dung_cu', ["ma_dc", "ten_dc", "tong_nhap", "luu_hanh", "ton_ksnk"]))
        layout.addWidget(self.table_dc)

    def setup_do_vai_tab(self):
        layout = QVBoxLayout(self.tab_do_vai)
        hl = QHBoxLayout()
        btn_add = QPushButton("➕ Thêm mới Đồ vải")
        btn_add.clicked.connect(lambda: self.add_item('do_vai'))
        hl.addWidget(btn_add)
        
        btn_nhap = QPushButton("📦 Nhập NCC (Kho Mua)")
        btn_nhap.clicked.connect(self.nhap_kho_ncc)
        hl.addWidget(btn_nhap)
        
        btn_xuat = QPushButton("🚚 Xuất Kho Mua -> KSNK")
        btn_xuat.clicked.connect(self.xuat_luu_hanh)
        hl.addWidget(btn_xuat)
        
        btn_chuyen = QPushButton("🔄 Chuyển Loại (VD: VIP -> Thường)")
        btn_chuyen.clicked.connect(self.chuyen_loai)
        hl.addWidget(btn_chuyen)
        
        btn_scrap = QPushButton("🗑️ Thanh Lý")
        btn_scrap.setObjectName("DangerButton")
        btn_scrap.clicked.connect(self.thanh_ly)
        hl.addWidget(btn_scrap)
        
        hl.addStretch()
        layout.addLayout(hl)
        
        self.table_dv = QTableWidget(0, 6)
        self.table_dv.setHorizontalHeaderLabels(["Mã ĐV", "Tên Đồ Vải", "Tồn KHO-MUA", "Tồn KSNK (Sạch)", "Tủ Trực Các Khoa", "TỔNG LƯU HÀNH"])
        self.table_dv.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        layout.addWidget(self.table_dv)

    def setup_bo_tab(self):
        layout = QVBoxLayout(self.tab_bo)
        hl = QHBoxLayout()
        btn_add = QPushButton("➕ Thêm mới Bộ dụng cụ")
        btn_add.clicked.connect(lambda: self.add_item('bo'))
        hl.addWidget(btn_add)
        hl.addStretch()
        layout.addLayout(hl)
        
        self.table_bo = QTableWidget(0, 4)
        self.table_bo.setHorizontalHeaderLabels(["Mã Bộ", "Tên Bộ", "Khoa Sử Dụng", "Tổng Số Bộ"])
        self.table_bo.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_bo.itemDoubleClicked.connect(lambda item: self.edit_cell(item, 'danh_muc_bo_dung_cu', ["ma_bo", "ten_bo", "khoa_su_dung", "tong_so_bo"]))
        layout.addWidget(self.table_bo)

    def nhap_kho_ncc(self):
        ma, ok1 = get_autocomplete_input(self, "Nhập Kho Mua", "Chọn mã đồ vải:", "do_vai")
        if ok1:
            sl, ok2 = QInputDialog.getInt(self, "Số lượng", "Nhập số lượng từ NCC:")
            if ok2:
                self.db.nhap_kho_mua(ma, sl)
                self.log_audit('danh_muc_do_vai', ma, f"Nhập từ NCC: +{sl} vào KHO-MUA")
                QMessageBox.information(self, "OK", f"Đã nhập {sl} {ma} vào KHO-MUA.")
                self.load_all_data()
                
    def xuat_luu_hanh(self):
        ma, ok1 = get_autocomplete_input(self, "Xuất Kho KSNK", "Chọn mã đồ vải:", "do_vai")
        if ok1:
            sl, ok2 = QInputDialog.getInt(self, "Số lượng", "Nhập số lượng xuất sang KHO KSNK:")
            if ok2:
                self.db.xuat_kho_mua_sang_lh(ma, sl)
                self.log_audit('danh_muc_do_vai', ma, f"Xuất kho mua sang KSNK: {sl} cái")
                QMessageBox.information(self, "OK", f"Đã xuất {sl} {ma} sang KHO KSNK.")
                self.load_all_data()
                
    def chuyen_loai(self):
        ma_cu, ok1 = get_autocomplete_input(self, "Chuyển Loại - BƯỚC 1", "Chọn mã Đồ vải CŨ (Bị trừ đi):", "do_vai")
        if ok1:
            sl, ok2 = QInputDialog.getInt(self, "Số lượng", "Số lượng cần chuyển loại:")
            if ok2:
                ma_moi, ok3 = get_autocomplete_input(self, "Chuyển Loại - BƯỚC 2", "Chọn mã Đồ vải MỚI (Được cộng vào):", "do_vai")
                if ok3:
                    self.db.chuyen_loai_do_vai(ma_cu, ma_moi, sl)
                    self.log_audit('danh_muc_do_vai', ma_cu, f"Chuyển loại {sl} cái thành {ma_moi}")
                    QMessageBox.information(self, "OK", f"Đã chuyển {sl} {ma_cu} thành {ma_moi}.")
                    self.load_all_data()

    def thanh_ly(self):
        ma, ok1 = get_autocomplete_input(self, "Thanh Lý", "Chọn mã đồ vải:", "do_vai")
        if ok1:
            sl, ok2 = QInputDialog.getInt(self, "Thanh Lý", "Số lượng thanh lý (Trừ từ Kho KSNK):")
            if ok2:
                self.db.thanh_ly_do_vai(ma, sl)
                self.log_audit('danh_muc_do_vai', ma, f"Thanh lý xuất bỏ {sl} cái")
                QMessageBox.information(self, "OK", f"Đã thanh lý {sl} món {ma}.")
                self.load_all_data()

    def load_all_data(self):
        # Load Dung cu
        try:
            dcs = self.db.fetch_all("SELECT ma_dc, ten_dc, tong_nhap, luu_hanh, ton_ksnk FROM danh_muc_dung_cu")
            self.table_dc.setRowCount(len(dcs))
            for r, d in enumerate(dcs):
                self.table_dc.setItem(r, 0, QTableWidgetItem(str(d.get('ma_dc', ''))))
                self.table_dc.setItem(r, 1, QTableWidgetItem(str(d.get('ten_dc', ''))))
                self.table_dc.setItem(r, 2, QTableWidgetItem(str(d.get('tong_nhap', ''))))
                self.table_dc.setItem(r, 3, QTableWidgetItem(str(d.get('luu_hanh', ''))))
                self.table_dc.setItem(r, 4, QTableWidgetItem(str(d.get('ton_ksnk', ''))))
        except: pass
        
        # Load Do Vai voi cong thuc Tong Luu Hanh = KSNK + Tu Truc Cac Khoa
        try:
            dvs = self.db.fetch_all('''
                SELECT d.ma_do_vai, d.ten_do_vai, d.ton_kho_mua, d.cssd_ton_thuc_te, 
                       COALESCE(SUM(t.so_luong + t.dang_su_dung), 0) as tu_truc
                FROM danh_muc_do_vai d
                LEFT JOIN tu_truc_khoa t ON d.ma_do_vai = t.ma_do
                GROUP BY d.ma_do_vai, d.ten_do_vai, d.ton_kho_mua, d.cssd_ton_thuc_te
            ''')
            self.table_dv.setRowCount(len(dvs))
            for r, d in enumerate(dvs):
                ksnk = int(d.get('cssd_ton_thuc_te', 0))
                tu_truc = int(d.get('tu_truc', 0))
                tong_lh = ksnk + tu_truc
                
                self.table_dv.setItem(r, 0, QTableWidgetItem(str(d.get('ma_do_vai', ''))))
                self.table_dv.setItem(r, 1, QTableWidgetItem(str(d.get('ten_do_vai', ''))))
                self.table_dv.setItem(r, 2, QTableWidgetItem(str(d.get('ton_kho_mua', '0'))))
                self.table_dv.setItem(r, 3, QTableWidgetItem(str(ksnk)))
                self.table_dv.setItem(r, 4, QTableWidgetItem(str(tu_truc)))
                
                item_tong = QTableWidgetItem(str(tong_lh))
                item_tong.setFont(QFont("Arial", 13, QFont.Bold))
                self.table_dv.setItem(r, 5, item_tong)
        except: pass

        # Load Bo Dung Cu
        try:
            bos = self.db.fetch_all("SELECT ma_bo, ten_bo, khoa_su_dung, tong_so_bo FROM danh_muc_bo_dung_cu")
            self.table_bo.setRowCount(len(bos))
            for r, b in enumerate(bos):
                self.table_bo.setItem(r, 0, QTableWidgetItem(str(b.get('ma_bo', ''))))
                self.table_bo.setItem(r, 1, QTableWidgetItem(str(b.get('ten_bo', ''))))
                self.table_bo.setItem(r, 2, QTableWidgetItem(str(b.get('khoa_su_dung', ''))))
                self.table_bo.setItem(r, 3, QTableWidgetItem(str(b.get('tong_so_bo', ''))))
        except: pass

    def edit_cell(self, item, table_name, columns):
        row = item.row()
        col = item.column()
        
        pk_col_name = columns[0]
        col_name = columns[col]
        
        if col == 0:
            QMessageBox.warning(self, "Cảnh báo", "Không được phép sửa Mã (ID) của danh mục!")
            return
            
        old_val = item.text()
        
        if table_name == 'danh_muc_dung_cu': table_widget = self.table_dc
        elif table_name == 'danh_muc_do_vai': table_widget = self.table_dv
        elif table_name == 'danh_muc_bo_dung_cu': table_widget = self.table_bo
        
        pk_val = table_widget.item(row, 0).text()
        
        new_val, ok = QInputDialog.getText(self, "Sửa Dữ Liệu", f"Nhập giá trị mới cho '{col_name}':", text=old_val)
        if ok and new_val != old_val:
            try:
                query = f"UPDATE {table_name} SET {col_name} = %s WHERE {pk_col_name} = %s"
                self.db.execute(query, (new_val, pk_val))
                log_msg = f"Sửa cột {col_name} từ '{old_val}' thành '{new_val}'"
                self.log_audit(table_name, pk_val, log_msg)
                QMessageBox.information(self, "Thành công", f"Đã cập nhật: {log_msg}")
                self.load_all_data()
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", str(e))

    def add_item(self, table_type):
        dlg = QDialog(self)
        dlg.setWindowTitle("Thêm Mới")
        layout = QFormLayout(dlg)
        
        txt_ma = QLineEdit()
        txt_ten = QLineEdit()
        layout.addRow("Mã:", txt_ma)
        layout.addRow("Tên:", txt_ten)
        
        btn = QPushButton("Lưu")
        layout.addRow(btn)
        
        def save():
            ma = txt_ma.text().strip()
            ten = txt_ten.text().strip()
            if not ma or not ten: return
            try:
                if table_type == 'dung_cu':
                    self.db.execute("INSERT INTO danh_muc_dung_cu (ma_dc, ten_dc) VALUES (%s, %s)", (ma, ten))
                    self.log_audit('danh_muc_dung_cu', ma, f"Thêm mới Dụng cụ: {ten}")
                elif table_type == 'do_vai':
                    self.db.execute("INSERT INTO danh_muc_do_vai (ma_do_vai, ten_do_vai) VALUES (%s, %s)", (ma, ten))
                    self.log_audit('danh_muc_do_vai', ma, f"Thêm mới Đồ vải: {ten}")
                elif table_type == 'bo':
                    self.db.execute("INSERT INTO danh_muc_bo_dung_cu (ma_bo, ten_bo) VALUES (%s, %s)", (ma, ten))
                    self.log_audit('danh_muc_bo_dung_cu', ma, f"Thêm mới Bộ dụng cụ: {ten}")
                    
                QMessageBox.information(dlg, "Thành công", "Đã thêm mới thành công!")
                dlg.accept()
                self.load_all_data()
            except Exception as e:
                QMessageBox.critical(dlg, "Lỗi", str(e))
                
        btn.clicked.connect(save)
        dlg.exec()
