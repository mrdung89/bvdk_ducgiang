from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget, 
                               QMessageBox, QInputDialog, QDialog, QFormLayout, QLineEdit, QComboBox, QSpinBox, QCheckBox)
from PySide6.QtCore import Qt
from models.db_manager import DBManager
from views.user_management import UserManagementWidget

class EditDialog(QDialog):
    def __init__(self, title, fields, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        self.form = QFormLayout()
        self.inputs = {}
        
        for f in fields:
            name = f['name']
            label = f['label']
            ftype = f.get('type', 'text')
            value = f.get('value', '')
            
            if ftype == 'text':
                widget = QLineEdit(str(value) if value else "")
            elif ftype == 'number':
                widget = QSpinBox()
                widget.setRange(0, 999999)
                if value: widget.setValue(int(value))
            elif ftype == 'combo':
                widget = QComboBox()
                widget.addItems(f.get('options', []))
                if value: widget.setCurrentText(str(value))
            elif ftype == 'multiselect':
                widget = QWidget()
                vbox = QVBoxLayout(widget)
                vbox.setContentsMargins(0,0,0,0)
                options = f.get('options', [])
                selected = f.get('value', [])
                widget.checkboxes = {}
                for opt in options:
                    cb = QCheckBox(opt['name'])
                    if opt['id'] in selected: cb.setChecked(True)
                    vbox.addWidget(cb)
                    widget.checkboxes[opt['id']] = cb
                
            self.form.addRow(label, widget)
            self.inputs[name] = widget
            
        layout.addLayout(self.form)
        
        hl = QHBoxLayout()
        btn_ok = QPushButton("Lưu")
        btn_ok.setObjectName("PrimaryButton")
        btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton("Hủy")
        btn_cancel.clicked.connect(self.reject)
        
        hl.addStretch()
        hl.addWidget(btn_ok)
        hl.addWidget(btn_cancel)
        layout.addLayout(hl)
        
    def get_data(self):
        res = {}
        for k, w in self.inputs.items():
            if isinstance(w, QLineEdit): res[k] = w.text().strip()
            elif isinstance(w, QSpinBox): res[k] = w.value()
            elif isinstance(w, QComboBox): res[k] = w.currentText()
            elif hasattr(w, 'checkboxes'): res[k] = [cid for cid, cb in w.checkboxes.items() if cb.isChecked()]
        return res


class ManagementPage(QWidget):
    def __init__(self):
        super().__init__()
        self.db = DBManager()
        layout = QVBoxLayout(self)
        
        title = QLabel("QUẢN LÝ (THIẾT LẬP DANH MỤC)")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)
        
        self.tabs = QTabWidget()
        
        self.tab_khoa = QWidget()
        self.setup_khoa_tab()
        self.tabs.addTab(self.tab_khoa, "Khoa / Phòng")
        
        self.tab_chutrinh = QWidget()
        self.setup_chutrinh_tab()
        self.tabs.addTab(self.tab_chutrinh, "Các Chu Trình")
        
        self.tab_item = QWidget()
        self.setup_item_tab()
        self.tabs.addTab(self.tab_item, "Bộ Dụng Cụ / Đồ Vải")
        
        self.tab_may = QWidget()
        self.setup_may_tab()
        self.tabs.addTab(self.tab_may, "Máy Móc")

        
        layout.addWidget(self.tabs)
        self.refresh_all()

    def refresh_all(self):
        self.load_khoa()
        self.load_chutrinh()
        self.load_items()
        self.load_may()

    # ================= KHOA =================
    def setup_khoa_tab(self):
        layout = QVBoxLayout(self.tab_khoa)
        hl = QHBoxLayout()
        btn_add = QPushButton(" Thêm Khoa")
        btn_add.setObjectName("PrimaryButton")
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
                
                w = QWidget()
                l = QHBoxLayout(w)
                l.setContentsMargins(0,0,0,0)
                btn_edit = QPushButton("Sửa")
                btn_edit.clicked.connect(lambda ch, r=row: self.edit_khoa(r))
                btn_del = QPushButton("Xóa")
                btn_del.setObjectName("DangerButton")
                btn_del.clicked.connect(lambda ch, cid=row['id']: self.delete_record("danh_muc_khoa", cid))
                l.addWidget(btn_edit)
                l.addWidget(btn_del)
                self.table_khoa.setCellWidget(r, 2, w)
        except: pass

    def add_khoa(self):
        fields = [{'name': 'ten', 'label': 'Tên Khoa:'}]
        dlg = EditDialog("Thêm Khoa", fields, self)
        if dlg.exec():
            data = dlg.get_data()
            if data['ten']:
                self.db.execute("INSERT INTO danh_muc_khoa (ten_khoa) VALUES (%s)", (data['ten'],))
                self.load_khoa()

    def edit_khoa(self, row_data):
        fields = [{'name': 'ten', 'label': 'Tên Khoa:', 'value': row_data['ten_khoa']}]
        dlg = EditDialog("Sửa Khoa", fields, self)
        if dlg.exec():
            data = dlg.get_data()
            if data['ten']:
                self.db.execute("UPDATE danh_muc_khoa SET ten_khoa=%s WHERE id=%s", (data['ten'], row_data['id']))
                self.load_khoa()

    # ================= CHU TRÌNH =================
    def setup_chutrinh_tab(self):
        layout = QVBoxLayout(self.tab_chutrinh)
        hl = QHBoxLayout()
        btn_add = QPushButton(" Thêm Chu Trình")
        btn_add.setObjectName("PrimaryButton")
        btn_add.clicked.connect(self.add_chutrinh)
        hl.addWidget(btn_add)
        hl.addStretch()
        layout.addLayout(hl)
        
        self.table_chutrinh = QTableWidget(0, 5)
        self.table_chutrinh.setHorizontalHeaderLabels(["ID", "Loại Chu Trình (Tên)", "Phương Pháp", "Thời gian (Phút)", "Thao tác"])
        self.table_chutrinh.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        layout.addWidget(self.table_chutrinh)

    def load_chutrinh(self):
        try:
            reqs = self.db.fetch_all("SELECT * FROM cycle_types")
            self.table_chutrinh.setRowCount(len(reqs))
            for r, row in enumerate(reqs):
                self.table_chutrinh.setItem(r, 0, QTableWidgetItem(str(row['id'])))
                self.table_chutrinh.setItem(r, 1, QTableWidgetItem(row['name']))
                self.table_chutrinh.setItem(r, 2, QTableWidgetItem(row.get('phuong_phap', '')))
                self.table_chutrinh.setItem(r, 3, QTableWidgetItem(str(row.get('thoi_gian', 0))))
                
                w = QWidget()
                l = QHBoxLayout(w)
                l.setContentsMargins(0,0,0,0)
                btn_edit = QPushButton("Sửa")
                btn_edit.clicked.connect(lambda ch, r=row: self.edit_chutrinh(r))
                btn_del = QPushButton("Xóa")
                btn_del.setObjectName("DangerButton")
                btn_del.clicked.connect(lambda ch, cid=row['id']: self.delete_record("cycle_types", cid))
                l.addWidget(btn_edit)
                l.addWidget(btn_del)
                self.table_chutrinh.setCellWidget(r, 4, w)
        except: pass

    def add_chutrinh(self):
        fields = [
            {'name': 'name', 'label': 'Tên chu trình:'},
            {'name': 'method', 'label': 'Phương pháp (Steam/Plasma/EO):', 'type': 'combo', 'options': ['Steam', 'Plasma', 'EO']},
            {'name': 'time', 'label': 'Thời gian chạy (Phút):', 'type': 'number', 'value': 60}
        ]
        dlg = EditDialog("Thêm Chu Trình", fields, self)
        if dlg.exec():
            data = dlg.get_data()
            if data['name']:
                self.db.execute("INSERT INTO cycle_types (name, phuong_phap, thoi_gian) VALUES (%s, %s, %s)", 
                                (data['name'], data['method'], data['time']))
                self.load_chutrinh()

    def edit_chutrinh(self, row_data):
        fields = [
            {'name': 'name', 'label': 'Tên chu trình:', 'value': row_data['name']},
            {'name': 'method', 'label': 'Phương pháp:', 'type': 'combo', 'options': ['Steam', 'Plasma', 'EO'], 'value': row_data.get('phuong_phap', 'Steam')},
            {'name': 'time', 'label': 'Thời gian (Phút):', 'type': 'number', 'value': row_data.get('thoi_gian', 60)}
        ]
        dlg = EditDialog("Sửa Chu Trình", fields, self)
        if dlg.exec():
            data = dlg.get_data()
            if data['name']:
                self.db.execute("UPDATE cycle_types SET name=%s, phuong_phap=%s, thoi_gian=%s WHERE id=%s", 
                                (data['name'], data['method'], data['time'], row_data['id']))
                self.load_chutrinh()

    # ================= BỘ DỤNG CỤ / ĐỒ VẢI =================
    def setup_item_tab(self):
        layout = QVBoxLayout(self.tab_item)
        hl = QHBoxLayout()
        btn_add_bo = QPushButton(" Thêm Bộ Dụng Cụ")
        btn_add_bo.setObjectName("PrimaryButton")
        btn_add_bo.clicked.connect(lambda: self.add_item('bo_dung_cu'))
        
        btn_add_do = QPushButton(" Thêm Đồ Vải/Dụng Cụ Lẻ")
        btn_add_do.setObjectName("PrimaryButton")
        btn_add_do.clicked.connect(lambda: self.add_item('do_vai'))
        
        hl.addWidget(btn_add_bo)
        hl.addWidget(btn_add_do)
        hl.addStretch()
        layout.addLayout(hl)
        
        self.table_item = QTableWidget(0, 6)
        self.table_item.setHorizontalHeaderLabels(["Loại", "Mã", "Tên", "Phương pháp TK", "Hạn TK (Ngày)", "Thao tác"])
        self.table_item.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        layout.addWidget(self.table_item)

    def load_items(self):
        try:
            res_bo = self.db.fetch_all("SELECT ma_bo as ma, ten_bo as ten, phuong_phap_tiet_khuan as pp, han_tiet_khuan as han FROM danh_muc_bo_dung_cu")
            res_do = self.db.fetch_all("SELECT ma_do_vai as ma, ten_do_vai as ten, 'Chung' as pp, han_tiet_khuan as han FROM danh_muc_do_vai")
            
            all_items = []
            for b in res_bo:
                b['type'] = 'Bộ DC'
                b['table'] = 'danh_muc_bo_dung_cu'
                b['key'] = 'ma_bo'
                all_items.append(b)
            for d in res_do:
                d['type'] = 'Đồ vải'
                d['table'] = 'danh_muc_do_vai'
                d['key'] = 'ma_do_vai'
                all_items.append(d)
                
            self.table_item.setRowCount(len(all_items))
            for r, row in enumerate(all_items):
                self.table_item.setItem(r, 0, QTableWidgetItem(row['type']))
                self.table_item.setItem(r, 1, QTableWidgetItem(row['ma']))
                self.table_item.setItem(r, 2, QTableWidgetItem(row['ten']))
                self.table_item.setItem(r, 3, QTableWidgetItem(row.get('pp', '')))
                self.table_item.setItem(r, 4, QTableWidgetItem(str(row.get('han', 30))))
                
                w = QWidget()
                l = QHBoxLayout(w)
                l.setContentsMargins(0,0,0,0)
                btn_edit = QPushButton("Sửa")
                btn_edit.clicked.connect(lambda ch, data=row: self.edit_item(data))
                btn_del = QPushButton("Xóa")
                btn_del.setObjectName("DangerButton")
                btn_del.clicked.connect(lambda ch, t=row['table'], c=row['ma'], k=row['key']: self.delete_record(t, c, k))
                l.addWidget(btn_edit)
                l.addWidget(btn_del)
                self.table_item.setCellWidget(r, 5, w)
        except: pass

    def add_item(self, item_type):
        fields = [
            {'name': 'ma', 'label': 'Mã:'},
            {'name': 'ten', 'label': 'Tên:'},
            {'name': 'pp', 'label': 'Phương pháp TK (Steam/Plasma...):', 'type': 'combo', 'options': ['Steam', 'Plasma', 'EO', 'Chung']},
            {'name': 'han', 'label': 'Hạn tiệt khuẩn (Ngày):', 'type': 'number', 'value': 30}
        ]
        dlg = EditDialog("Thêm mới", fields, self)
        if dlg.exec():
            data = dlg.get_data()
            if data['ma'] and data['ten']:
                if item_type == 'bo_dung_cu':
                    self.db.execute("INSERT INTO danh_muc_bo_dung_cu (ma_bo, ten_bo, phuong_phap_tiet_khuan, han_tiet_khuan) VALUES (%s, %s, %s, %s)", 
                                    (data['ma'], data['ten'], data['pp'], data['han']))
                else:
                    self.db.execute("INSERT INTO danh_muc_do_vai (ma_do_vai, ten_do_vai, han_tiet_khuan) VALUES (%s, %s, %s)", 
                                    (data['ma'], data['ten'], data['han']))
                self.load_items()
        self.load_may()

    def edit_item(self, row_data):
        fields = [
            {'name': 'ma', 'label': 'Mã (không thể sửa):', 'value': row_data['ma']}, # Normally shouldn't edit PK easily, but we'll disable it visually by ignoring changes
            {'name': 'ten', 'label': 'Tên:', 'value': row_data['ten']},
            {'name': 'pp', 'label': 'Phương pháp TK:', 'type': 'combo', 'options': ['Steam', 'Plasma', 'EO', 'Chung'], 'value': row_data.get('pp', 'Steam')},
            {'name': 'han', 'label': 'Hạn tiệt khuẩn (Ngày):', 'type': 'number', 'value': row_data.get('han', 30)}
        ]
        dlg = EditDialog("Sửa", fields, self)
        # Disable ma edit
        dlg.inputs['ma'].setEnabled(False)
        
        if dlg.exec():
            data = dlg.get_data()
            if data['ten']:
                if row_data['table'] == 'danh_muc_bo_dung_cu':
                    self.db.execute("UPDATE danh_muc_bo_dung_cu SET ten_bo=%s, phuong_phap_tiet_khuan=%s, han_tiet_khuan=%s WHERE ma_bo=%s", 
                                    (data['ten'], data['pp'], data['han'], row_data['ma']))
                else:
                    self.db.execute("UPDATE danh_muc_do_vai SET ten_do_vai=%s, han_tiet_khuan=%s WHERE ma_do_vai=%s", 
                                    (data['ten'], data['han'], row_data['ma']))
                self.load_items()
        self.load_may()

    # ================= UTILS =================
    def delete_record(self, table, record_id, key_col="id"):
        reply = QMessageBox.question(self, 'Xác nhận', f'Bạn có chắc muốn xóa bản ghi này?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                self.db.execute(f"DELETE FROM {table} WHERE {key_col}=%s", (record_id,))
                self.refresh_all()
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể xóa vì dữ liệu đang được sử dụng ở bảng khác.\n{e}")

    # ================= MÁY MÓC =================
    def setup_may_tab(self):
        layout = QVBoxLayout(self.tab_may)
        hl = QHBoxLayout()
        btn_add = QPushButton(" Thêm Máy")
        btn_add.setObjectName("PrimaryButton")
        btn_add.clicked.connect(self.add_may)
        hl.addWidget(btn_add)
        hl.addStretch()
        layout.addLayout(hl)
        
        self.table_may = QTableWidget(0, 5)
        self.table_may.setHorizontalHeaderLabels(["ID", "Tên Máy", "Nhóm", "Các Chu Trình Gán", "Thao tác"])
        self.table_may.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        layout.addWidget(self.table_may)

    def load_may(self):
        try:
            reqs = self.db.fetch_all("SELECT * FROM machines")
            
            # Fetch assigned cycles
            all_assigned = self.db.fetch_all("SELECT mct.machine_id, ct.name FROM machine_cycle_types mct JOIN cycle_types ct ON mct.cycle_type_id = ct.id")
            assigned_map = {}
            if all_assigned:
                for a in all_assigned:
                    if a['machine_id'] not in assigned_map: assigned_map[a['machine_id']] = []
                    assigned_map[a['machine_id']].append(a['name'])
                
            groups = {1: "Máy Giặt", 2: "Máy Sấy", 3: "Máy Tiệt Trùng/Plasma"}
            
            self.table_may.setRowCount(len(reqs))
            for r, row in enumerate(reqs):
                self.table_may.setItem(r, 0, QTableWidgetItem(str(row['id'])))
                self.table_may.setItem(r, 1, QTableWidgetItem(row['name']))
                self.table_may.setItem(r, 2, QTableWidgetItem(groups.get(row['group_id'], "Khác")))
                
                cycles = assigned_map.get(row['id'], [])
                self.table_may.setItem(r, 3, QTableWidgetItem(", ".join(cycles)))
                
                w = QWidget()
                l = QHBoxLayout(w)
                l.setContentsMargins(0,0,0,0)
                btn_edit = QPushButton("Sửa")
                btn_edit.clicked.connect(lambda ch, row_data=row: self.edit_may(row_data))
                btn_del = QPushButton("Xóa")
                btn_del.setObjectName("DangerButton")
                btn_del.clicked.connect(lambda ch, cid=row['id']: self.delete_record("machines", cid))
                l.addWidget(btn_edit)
                l.addWidget(btn_del)
                self.table_may.setCellWidget(r, 4, w)
        except Exception as e: 
            print(e)

    def _get_may_fields(self, row_data=None):
        try:
            cycles = self.db.fetch_all("SELECT id, name FROM cycle_types")
        except:
            cycles = []
            
        selected_cycles = []
        if row_data:
            try:
                assigned = self.db.fetch_all("SELECT cycle_type_id FROM machine_cycle_types WHERE machine_id=%s", (row_data['id'],))
                if assigned:
                    selected_cycles = [a['cycle_type_id'] for a in assigned]
            except: pass
            
        group_val = "Máy Tiệt Trùng/Plasma"
        if row_data:
            if row_data.get('group_id') == 1: group_val = "Máy Giặt"
            elif row_data.get('group_id') == 2: group_val = "Máy Sấy"
            
        return [
            {'name': 'name', 'label': 'Tên Máy:', 'value': row_data['name'] if row_data else ''},
            {'name': 'group', 'label': 'Nhóm Máy:', 'type': 'combo', 'options': ['Máy Giặt', 'Máy Sấy', 'Máy Tiệt Trùng/Plasma'], 'value': group_val},
            {'name': 'cycles', 'label': 'Gán Chu Trình:', 'type': 'multiselect', 'options': cycles, 'value': selected_cycles}
        ]

    def add_may(self):
        fields = self._get_may_fields()
        dlg = EditDialog("Thêm Máy", fields, self)
        if dlg.exec():
            data = dlg.get_data()
            if data['name']:
                group_id = 3
                if data['group'] == 'Máy Giặt': group_id = 1
                elif data['group'] == 'Máy Sấy': group_id = 2
                
                try:
                    cursor = self.db.conn.cursor()
                    cursor.execute("INSERT INTO machines (name, group_id) VALUES (%s, %s)", (data['name'], group_id))
                    new_id = cursor.lastrowid
                    self.db.conn.commit()
                    
                    if data['cycles']:
                        for cid in data['cycles']:
                            self.db.execute("INSERT INTO machine_cycle_types (machine_id, cycle_type_id) VALUES (%s, %s)", (new_id, cid))
                    self.load_may()
                except Exception as e:
                    QMessageBox.critical(self, "Lỗi", str(e))

    def edit_may(self, row_data):
        fields = self._get_may_fields(row_data)
        dlg = EditDialog("Sửa Máy", fields, self)
        if dlg.exec():
            data = dlg.get_data()
            if data['name']:
                group_id = 3
                if data['group'] == 'Máy Giặt': group_id = 1
                elif data['group'] == 'Máy Sấy': group_id = 2
                
                try:
                    self.db.execute("UPDATE machines SET name=%s, group_id=%s WHERE id=%s", (data['name'], group_id, row_data['id']))
                    
                    self.db.execute("DELETE FROM machine_cycle_types WHERE machine_id=%s", (row_data['id'],))
                    if data['cycles']:
                        for cid in data['cycles']:
                            self.db.execute("INSERT INTO machine_cycle_types (machine_id, cycle_type_id) VALUES (%s, %s)", (row_data['id'], cid))
                        
                    self.load_may()
                except Exception as e:
                    QMessageBox.critical(self, "Lỗi", str(e))
