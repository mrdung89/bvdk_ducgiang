from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget, 
                               QMessageBox, QInputDialog)
from models.db_manager import DBManager

class MasterDataPage(QWidget):
    def __init__(self):
        super().__init__()
        self.db = DBManager()
        layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        
        self.tab_khoa = QWidget()
        self.setup_khoa_tab()
        self.tabs.addTab(self.tab_khoa, "Khoa / Phòng")
        
        self.tab_dovai = QWidget()
        self.setup_dovai_tab()
        self.tabs.addTab(self.tab_dovai, "Đồ Vải / Dụng Cụ")
        
        self.tab_bodungcu = QWidget()
        self.setup_bodungcu_tab()
        self.tabs.addTab(self.tab_bodungcu, "Bộ Dụng Cụ")
        
        self.tab_may = QWidget()
        self.setup_may_tab()
        self.tabs.addTab(self.tab_may, "Máy & Chu Trình")
        
        layout.addWidget(self.tabs)
        self.refresh_all()

    def refresh_all(self):
        self.load_khoa()
        self.load_dovai()
        self.load_bodungcu()
        self.load_may()

    # --- KHOA ---
    def setup_khoa_tab(self):
        layout = QVBoxLayout(self.tab_khoa)
        hl = QHBoxLayout()
        btn_add = QPushButton("➕ Thêm Khoa")
        btn_add.clicked.connect(self.add_khoa)
        hl.addWidget(btn_add)
        hl.addStretch()
        layout.addLayout(hl)
        
        self.table_khoa = QTableWidget(0, 3)
        self.table_khoa.setHorizontalHeaderLabels(["ID", "Tên Khoa", "Thao tác"])
        self.table_khoa.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        layout.addWidget(self.table_khoa)

    def load_khoa(self):
        try:
            reqs = self.db.fetch_all("SELECT * FROM danh_muc_khoa")
            self.table_khoa.setRowCount(len(reqs))
            for r, row in enumerate(reqs):
                self.table_khoa.setItem(r, 0, QTableWidgetItem(str(row['id'])))
                self.table_khoa.setItem(r, 1, QTableWidgetItem(row['ten_khoa']))
                btn_del = QPushButton("❌ Xóa")
                btn_del.clicked.connect(lambda ch, cid=row['id']: self.delete_record("danh_muc_khoa", cid))
                self.table_khoa.setCellWidget(r, 2, btn_del)
        except: pass

    def add_khoa(self):
        ten, ok = QInputDialog.getText(self, "Thêm Khoa", "Nhập tên khoa mới:")
        if ok and ten:
            self.db.execute("INSERT INTO danh_muc_khoa (ten_khoa) VALUES (%s)", (ten,))
            self.load_khoa()

    # --- DO VAI ---
    def setup_dovai_tab(self):
        layout = QVBoxLayout(self.tab_dovai)
        hl = QHBoxLayout()
        btn_add = QPushButton("➕ Thêm Đồ Vải/Dụng Cụ lẻ")
        btn_add.clicked.connect(self.add_dovai)
        hl.addWidget(btn_add)
        hl.addStretch()
        layout.addLayout(hl)
        
        self.table_dovai = QTableWidget(0, 4)
        self.table_dovai.setHorizontalHeaderLabels(["Mã", "Tên", "Phân Loại", "Thao tác"])
        self.table_dovai.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        layout.addWidget(self.table_dovai)

    def load_dovai(self):
        try:
            reqs = self.db.fetch_all("SELECT ma_do_vai, ten_do_vai, phan_loai FROM danh_muc_do_vai")
            self.table_dovai.setRowCount(len(reqs))
            for r, row in enumerate(reqs):
                self.table_dovai.setItem(r, 0, QTableWidgetItem(row['ma_do_vai']))
                self.table_dovai.setItem(r, 1, QTableWidgetItem(row['ten_do_vai']))
                self.table_dovai.setItem(r, 2, QTableWidgetItem(row['phan_loai']))
                btn_del = QPushButton("❌ Xóa")
                btn_del.clicked.connect(lambda ch, ma=row['ma_do_vai']: self.delete_record("danh_muc_do_vai", ma, "ma_do_vai"))
                self.table_dovai.setCellWidget(r, 3, btn_del)
        except: pass

    def add_dovai(self):
        ma, ok = QInputDialog.getText(self, "Mã", "Mã đồ (VD: QUAN-NAM):")
        if not ok or not ma: return
        ten, ok2 = QInputDialog.getText(self, "Tên", "Tên đồ:")
        if not ok2 or not ten: return
        loai, ok3 = QInputDialog.getItem(self, "Phân loại", "Chọn loại:", ["THUONG", "VIP"], 0, False)
        if ok3:
            self.db.execute("INSERT INTO danh_muc_do_vai (ma_do_vai, ten_do_vai, phan_loai, ton_kho_mua, cssd_ton_thuc_te) VALUES (%s, %s, %s, 0, 0)", (ma, ten, loai))
            self.load_dovai()

    # --- BO DUNG CU ---
    def setup_bodungcu_tab(self):
        layout = QVBoxLayout(self.tab_bodungcu)
        hl = QHBoxLayout()
        btn_add = QPushButton("➕ Thêm Bộ Mới")
        btn_add.clicked.connect(self.add_bo)
        hl.addWidget(btn_add)
        hl.addStretch()
        layout.addLayout(hl)
        
        self.table_bo = QTableWidget(0, 3)
        self.table_bo.setHorizontalHeaderLabels(["Mã Bộ", "Tên Bộ", "Thao tác"])
        self.table_bo.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        layout.addWidget(self.table_bo)

    def load_bodungcu(self):
        try:
            reqs = self.db.fetch_all("SELECT ma_bo, ten_bo FROM danh_muc_bo_dung_cu")
            self.table_bo.setRowCount(len(reqs))
            for r, row in enumerate(reqs):
                self.table_bo.setItem(r, 0, QTableWidgetItem(row['ma_bo']))
                self.table_bo.setItem(r, 1, QTableWidgetItem(row['ten_bo']))
                btn_del = QPushButton("❌ Xóa")
                btn_del.clicked.connect(lambda ch, ma=row['ma_bo']: self.delete_record("danh_muc_bo_dung_cu", ma, "ma_bo"))
                self.table_bo.setCellWidget(r, 2, btn_del)
        except: pass

    def add_bo(self):
        ma, ok = QInputDialog.getText(self, "Mã Bộ", "Mã bộ (VD: BO-TIEUPHAU):")
        if not ok or not ma: return
        ten, ok2 = QInputDialog.getText(self, "Tên", "Tên bộ:")
        if ok2 and ten:
            self.db.execute("INSERT INTO danh_muc_bo_dung_cu (ma_bo, ten_bo) VALUES (%s, %s)", (ma, ten))
            self.load_bodungcu()

    # --- MAY & CHU TRINH ---
    def setup_may_tab(self):
        layout = QVBoxLayout(self.tab_may)
        layout.addWidget(QLabel("Mục quản lý danh sách máy (Giặt/Hấp) và Chu trình..."))

    def load_may(self):
        pass

    # --- UTILS ---
    def delete_record(self, table, record_id, key_col="id"):
        reply = QMessageBox.question(self, 'Xác nhận', f'Bạn có chắc muốn xóa dòng này trong bảng {table}?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db.execute(f"DELETE FROM {table} WHERE {key_col}=%s", (record_id,))
            self.refresh_all()
