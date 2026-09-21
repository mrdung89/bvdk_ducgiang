from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QComboBox, 
                               QLineEdit, QTableWidget, QTableWidgetItem, 
                               QCheckBox, QSpinBox, QPushButton, QWidget, QHeaderView, QAbstractItemView)
from PySide6.QtCore import Qt
from models.db_manager import DBManager
from utils.quantity_widget import QuantityWidget
from utils.vietnamese_filter import remove_vietnamese_accents

class ItemSelectorDialog(QDialog):
    def __init__(self, parent=None, existing_ma=None, add_callback=None):
        super().__init__(parent)
        self.existing_ma = existing_ma or []
        self.add_callback = add_callback
        self.setWindowTitle("Chọn từ danh sách")
        self.resize(1200, 800)
        
        self.db = DBManager()
        
        layout = QVBoxLayout(self)
        
        # Filter Layout
        filter_layout = QHBoxLayout()
        self.cb_type = QComboBox()
        self.cb_type.addItems(["Tất cả", "Đồ vải", "Bộ dụng cụ", "Dụng cụ lẻ"])
        self.cb_type.currentIndexChanged.connect(self.load_data)
        
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Tìm kiếm theo tên hoặc mã...")
        self.txt_search.textChanged.connect(self.load_data)
        
        filter_layout.addWidget(self.cb_type)
        filter_layout.addWidget(self.txt_search)
        layout.addLayout(filter_layout)
        
        # Table
        self.table = QTableWidget(0, 4)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.cellDoubleClicked.connect(self.on_double_click)
        self.table.setHorizontalHeaderLabels(["Chọn", "Mã Đồ", "Tên Đồ", "Số lượng"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 150)
        self.table.setColumnWidth(3, 150)
        layout.addWidget(self.table)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_ok = QPushButton("Thêm vào giỏ")
        self.btn_ok.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold; padding: 5px 15px;")
        self.btn_ok.clicked.connect(self.accept)
        
        self.btn_cancel = QPushButton("Hủy")
        self.btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)
        
        self.all_items = []
        self.fetch_all_items()
        self.load_data()

    def fetch_all_items(self):
        try:
            res1 = self.db.fetch_all("SELECT ma_bo as ma, ten_bo as ten FROM danh_muc_bo_dung_cu")
            for r in res1: self.all_items.append({'ma': r['ma'], 'ten': r['ten'], 'type': 'Bộ dụng cụ'})
            
            res2 = self.db.fetch_all("SELECT ma_do_vai as ma, ten_do_vai as ten FROM danh_muc_do_vai")
            for r in res2: self.all_items.append({'ma': r['ma'], 'ten': r['ten'], 'type': 'Đồ vải'})
            
            res3 = self.db.fetch_all("SELECT ma_dc as ma, ten_dc as ten FROM danh_muc_dung_cu")
            for r in res3: self.all_items.append({'ma': r['ma'], 'ten': r['ten'], 'type': 'Dụng cụ lẻ'})
        except:
            pass

    def load_data(self):
        filter_type = self.cb_type.currentText()
                search_txt = self.txt_search.text().strip()
        if search_txt.startswith("ID:"):
            parts = search_txt.split(",")
            search_txt = parts[0].replace("ID:", "").strip()
        search_txt = remove_vietnamese_accents(search_txt)
        
        self.table.setRowCount(0)
        self._cell_widgets = []
        
        filtered = []
        for it in self.all_items:
            if filter_type != "Tất cả" and it['type'] != filter_type:
                continue
            if search_txt:
                norm_ma = remove_vietnamese_accents(it['ma'])
                norm_ten = remove_vietnamese_accents(it['ten'])
                if search_txt not in norm_ma and search_txt not in norm_ten:
                    continue
            filtered.append(it)
            
            if len(filtered) >= 100: # Limit to 100 items to prevent UI freeze
                break
                
        self.table.setRowCount(len(filtered))
        for r, it in enumerate(filtered):
            # Checkbox
            chk_widget = QWidget()
            chk_layout = QHBoxLayout(chk_widget)
            chk_layout.setContentsMargins(0,0,0,0)
            chk_layout.setAlignment(Qt.AlignCenter)
            chk = QCheckBox()
            chk_layout.addWidget(chk)
            self.table.setItem(r, 0, QTableWidgetItem())
            self._cell_widgets.append(chk_widget)
            self.table.setCellWidget(r, 0, chk_widget)
            
            self.table.setItem(r, 1, QTableWidgetItem(it['ma']))
            self.table.setItem(r, 2, QTableWidgetItem(it['ten']))
            self.table.setItem(r, 3, QTableWidgetItem())
            
            # Spinbox
            spin = QuantityWidget()
            self._cell_widgets.append(spin)
            self.table.setCellWidget(r, 3, spin)
            self.table.setRowHeight(r, 50)

    def on_double_click(self, row, col):
        ma = self.table.item(row, 1).text()
        ten = self.table.item(row, 2).text()
        sl = self.table.cellWidget(row, 3).value()
        
        if ma in self.existing_ma:
            return
            
        if self.add_callback:
            self.add_callback(ma, ten, sl)
            self.existing_ma.append(ma)
            
        # Tick the checkbox to show it was added
        chk_widget = self.table.cellWidget(row, 0)
        chk = chk_widget.layout().itemAt(0).widget()
        chk.setChecked(True)

    def get_selected_items(self):
        results = []
        for r in range(self.table.rowCount()):
            chk_widget = self.table.cellWidget(r, 0)
            chk = chk_widget.layout().itemAt(0).widget()
            if chk.isChecked():
                ma = self.table.item(r, 1).text()
                ten = self.table.item(r, 2).text()
                sl = self.table.cellWidget(r, 3).value()
                results.append({'ma': ma, 'ten': ten, 'sl': sl})
        return results
