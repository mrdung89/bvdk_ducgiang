from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QTableWidget, QTableWidgetItem, QHeaderView, 
                               QMessageBox, QSpinBox, QLineEdit, QWidget, QSplitter)
from PySide6.QtCore import Qt, QSortFilterProxyModel
from PySide6.QtGui import QStandardItemModel, QStandardItem
from models.db_manager import DBManager
import unicodedata

def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)]).lower()

class MultiItemDialog(QDialog):
    def __init__(self, parent, title, list_type="all", target_khoa=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(1200, 800)
        self.db = DBManager()
        self.target_khoa = target_khoa
        self.items_to_submit = []
        
        main_layout = QVBoxLayout(self)
        
        # --- Top Filters ---
        filter_layout = QHBoxLayout()
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Tìm kiếm (Gõ không dấu)...")
        self.txt_search.textChanged.connect(self.filter_table)
        filter_layout.addWidget(self.txt_search, stretch=1)
        
        self.btn_all = QPushButton("Tất cả")
        self.btn_vai = QPushButton("Đồ Vải")
        self.btn_bo = QPushButton("Bộ Dụng Cụ")
        self.btn_le = QPushButton("Dụng Cụ Lẻ")
        
        for btn in [self.btn_all, self.btn_vai, self.btn_bo, self.btn_le]:
            btn.setCheckable(True)
            btn.setStyleSheet("QPushButton { padding: 4px 10px; border-radius: 4px; } QPushButton:checked { background-color: #2980b9; color: white; font-weight: bold; }")
            filter_layout.addWidget(btn)
            
        self.btn_all.setChecked(True)
        self.btn_all.clicked.connect(lambda: self.change_filter("all"))
        self.btn_vai.clicked.connect(lambda: self.change_filter("vai"))
        self.btn_bo.clicked.connect(lambda: self.change_filter("bo"))
        self.btn_le.clicked.connect(lambda: self.change_filter("le"))
        
        main_layout.addLayout(filter_layout)
        
        # --- Splitter (Left: Available, Right: Cart) ---
        splitter = QSplitter(Qt.Horizontal)
        
        # Left Table
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(QLabel("<b>Danh sách mặt hàng (Double-click để thêm)</b>"))
        
        self.table_items = QTableWidget(0, 4)
        self.table_items.setHorizontalHeaderLabels(["Loại", "Mã Đồ", "Tên Đồ", "+"])
        self.table_items.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table_items.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_items.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_items.itemDoubleClicked.connect(self.on_item_double_clicked)
        left_layout.addWidget(self.table_items)
        
        # Right Table
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(QLabel("<b>Giỏ hàng</b>"))
        
        self.table_cart = QTableWidget(0, 4)
        self.table_cart.setHorizontalHeaderLabels(["Loại", "Tên Đồ", "Số Lượng", "Xóa"])
        self.table_cart.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        right_layout.addWidget(self.table_cart)
        
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([600, 400])
        main_layout.addWidget(splitter)
        
        # --- Submit ---
        btn_submit = QPushButton("Xác Nhận Tạo Phiếu (Gửi Toàn Bộ)")
        btn_submit.setObjectName("PrimaryButton")
        btn_submit.clicked.connect(self.submit_all)
        main_layout.addWidget(btn_submit)
        
        self.all_data = []
        self.current_filter = "all"
        self.load_all_data()

    def load_all_data(self):
        self.all_data = []
        try:
            rows = self.db.fetch_all("SELECT ma_do_vai as id, ten_do_vai as ten FROM danh_muc_do_vai")
            for r in rows: self.all_data.append({"type": "vai", "id": r['id'], "name": r['ten']})
        except: pass
        try:
            rows = self.db.fetch_all("SELECT ma_bo as id, ten_bo as ten FROM danh_muc_bo_dung_cu")
            for r in rows: self.all_data.append({"type": "bo", "id": r['id'], "name": r['ten']})
        except: pass
        try:
            rows = self.db.fetch_all("SELECT ma_dc as id, ten_dc as ten FROM danh_muc_dung_cu")
            for r in rows: self.all_data.append({"type": "le", "id": r['id'], "name": r['ten']})
        except: pass
        
        self.populate_left_table()

    def change_filter(self, f_type):
        for b in [self.btn_all, self.btn_vai, self.btn_bo, self.btn_le]: b.setChecked(False)
        if f_type == "all": self.btn_all.setChecked(True)
        elif f_type == "vai": self.btn_vai.setChecked(True)
        elif f_type == "bo": self.btn_bo.setChecked(True)
        elif f_type == "le": self.btn_le.setChecked(True)
        
        self.current_filter = f_type
        self.populate_left_table()

    def filter_table(self):
        self.populate_left_table()

    def populate_left_table(self):
        keyword = remove_accents(self.txt_search.text())
        
        self.table_items.setRowCount(0)
        for item in self.all_data:
            if self.current_filter != "all" and item['type'] != self.current_filter:
                continue
            
            search_str = remove_accents(f"{item['id']} {item['name']}")
            if keyword and keyword not in search_str:
                continue
                
            r = self.table_items.rowCount()
            self.table_items.insertRow(r)
            
            self.table_items.setItem(r, 0, QTableWidgetItem(item['type'].upper()))
            self.table_items.setItem(r, 1, QTableWidgetItem(item['id']))
            self.table_items.setItem(r, 2, QTableWidgetItem(item['name']))
            
            btn_add = QPushButton("+")
            btn_add.clicked.connect(lambda ch, t=item['type'], c=item['id'], n=item['name']: self.add_to_cart(t, c, n))
            self.table_items.setCellWidget(r, 3, btn_add)

    def on_item_double_clicked(self, item):
        row = item.row()
        typ = self.table_items.item(row, 0).text()
        code = self.table_items.item(row, 1).text()
        name = self.table_items.item(row, 2).text()
        self.add_to_cart(typ, code, name)

    def add_to_cart(self, typ, code, name):
        # Check if already added
        for i in range(self.table_cart.rowCount()):
            if self.table_cart.item(i, 1).data(Qt.UserRole) == code:
                sb = self.table_cart.cellWidget(i, 2).findChild(QSpinBox)
                sb.setValue(sb.value() + 1)
                return
                
        r = self.table_cart.rowCount()
        self.table_cart.insertRow(r)
        
        self.table_cart.setItem(r, 0, QTableWidgetItem(typ.upper()))
        
        it_name = QTableWidgetItem(f"{code} - {name}")
        it_name.setData(Qt.UserRole, code)
        self.table_cart.setItem(r, 1, it_name)
        
        qty_widget = QWidget()
        ql = QHBoxLayout(qty_widget)
        ql.setContentsMargins(0,0,0,0)
        sb = QSpinBox()
        sb.setMinimum(1)
        sb.setMaximum(999)
        sb.setValue(1)
        ql.addWidget(sb)
        self.table_cart.setCellWidget(r, 2, qty_widget)
        
        btn_del = QPushButton("Xóa")
        btn_del.clicked.connect(lambda ch, row_widget=qty_widget: self.remove_cart_row(row_widget))
        self.table_cart.setCellWidget(r, 3, btn_del)

    def prefill_cart(self, items_list):
        # items_list: list of dict {'type': 'VAI', 'code': 'A1', 'name': 'Ao', 'qty': 2}
        for it in items_list:
            r = self.table_cart.rowCount()
            self.table_cart.insertRow(r)
            
            self.table_cart.setItem(r, 0, QTableWidgetItem(it['type']))
            
            it_name = QTableWidgetItem(f"{it['code']} - {it['name']}")
            it_name.setData(Qt.UserRole, it['code'])
            self.table_cart.setItem(r, 1, it_name)
            
            qty_widget = QWidget()
            ql = QHBoxLayout(qty_widget)
            ql.setContentsMargins(0,0,0,0)
            sb = QSpinBox()
            sb.setMinimum(1)
            sb.setMaximum(999)
            sb.setValue(it['qty'])
            ql.addWidget(sb)
            self.table_cart.setCellWidget(r, 2, qty_widget)
            
            btn_del = QPushButton("Xóa")
            btn_del.clicked.connect(lambda ch, row_widget=qty_widget: self.remove_cart_row(row_widget))
            self.table_cart.setCellWidget(r, 3, btn_del)
            
    def remove_cart_row(self, widget):
        for i in range(self.table_cart.rowCount()):
            if self.table_cart.cellWidget(i, 2) == widget:
                self.table_cart.removeRow(i)
                break

    def submit_all(self):
        if self.table_cart.rowCount() == 0:
            QMessageBox.warning(self, "Lỗi", "Chưa có món nào trong giỏ!")
            return
            
        for i in range(self.table_cart.rowCount()):
            code_str = self.table_cart.item(i, 1).data(Qt.UserRole)
            qty = self.table_cart.cellWidget(i, 2).findChild(QSpinBox).value()
            self.items_to_submit.append((code_str, qty))
            
        self.accept()
