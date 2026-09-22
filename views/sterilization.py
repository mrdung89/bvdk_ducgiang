import json
from datetime import datetime
from PySide6.QtWidgets import (QSpinBox, QFrame, QScrollArea, QWidget, QVBoxLayout, QPushButton, QLabel, QTableWidget, 
                               QTableWidgetItem, QHeaderView, QMessageBox, QDialog, QComboBox, 
                               QCheckBox, QHBoxLayout, QFormLayout, QDateEdit, QSplitter,
                               QTreeWidget, QTreeWidgetItem)
from PySide6.QtCore import Qt, QTimer, QDate, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import QSpinBox, QFrame, QGridLayout, QScrollArea

class TestResultDialog(QDialog):
    def __init__(self, machine_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Xác nhận kết quả Test - {machine_name}")
        self.setFixedSize(450, 300)
        self.result = "FAIL"
        
        layout = QVBoxLayout(self)
        title = QLabel(f"Báo cáo kết quả chu trình: {machine_name}")
        title.setStyleSheet("font-weight: bold; font-size: 16px; color: #2c3e50;")
        layout.addWidget(title)
        
        form = QFormLayout()
        self.chk_ci = QCheckBox("CI (Chemical Indicator) Đạt")
        self.chk_ci.setChecked(True)
        self.chk_bi = QCheckBox("BI (Biological Indicator) Đạt")
        self.chk_bi.setChecked(True)
        self.chk_chart = QCheckBox("Biểu đồ (Nhiệt/Áp suất) Đạt")
        self.chk_chart.setChecked(True)
        form.addRow(self.chk_ci)
        form.addRow(self.chk_bi)
        form.addRow(self.chk_chart)
        layout.addLayout(form)
        
        self.cb_final = QComboBox()
        self.cb_final.addItems(["PASS (Đạt toàn bộ)", "FAIL (Hủy mẻ)"])
        layout.addWidget(QLabel("Kết luận cuối cùng:"))
        layout.addWidget(self.cb_final)
        
        layout.addSpacing(10)
        btn = QPushButton("Xác Nhận Xuất Mẻ (Release Load)")
        btn.setObjectName("SuccessButton")
        btn.clicked.connect(self.confirm)
        layout.addWidget(btn)
        
    def confirm(self):
        if self.cb_final.currentIndex() == 0:
            if not (self.chk_ci.isChecked() and self.chk_bi.isChecked() and self.chk_chart.isChecked()):
                QMessageBox.warning(self, "Cảnh báo", "Bạn chọn PASS nhưng chưa tick đủ các chỉ thị!")
                return
            self.result = "PASS"
        else:
            self.result = "FAIL"
            
        # TẠO CHUỖI GHI CHÚ CHI TIẾT
        ci = "Đạt" if self.chk_ci.isChecked() else "Lỗi"
        bi = "Đạt" if self.chk_bi.isChecked() else "Lỗi"
        chart = "Đạt" if self.chk_chart.isChecked() else "Lỗi"
        self.test_note = f"CI: {ci} | BI: {bi} | Chart: {chart}"
        
        self.accept()

class LoadItemsDialog(QDialog):
    def __init__(self, parent_page, machine_name, parent=None):
        super().__init__(parent)
        self.parent_page = parent_page
        self.setWindowTitle(f"Xếp đồ vào lò tiệt khuẩn - {machine_name}")
        self.setMinimumSize(1000, 700) # Phóng to màn hình con
        
        layout = QVBoxLayout(self)
        
        lbl_info = QLabel("Đánh dấu (Tick) vào các món đồ và nhập số lượng để đưa vào lò:")
        lbl_info.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(lbl_info)
        
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Khoa / Tên Đồ", "Số Lượng Bỏ Vào Lò"])
        self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        layout.addWidget(self.tree)
        
        btn_layout = QHBoxLayout()
        btn_nap = QPushButton("Xác nhận đưa vào lò")
        btn_nap.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 10px;")
        btn_nap.clicked.connect(self.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_nap)
        layout.addLayout(btn_layout)
        
        self.staged_items = []
        self.load_all_pending_items()
        
    def load_all_pending_items(self):
        self.tree.clear()
        self.staged_items = []
        
        # Gọi thẳng database để lấy toàn bộ đồ chờ tiệt khuẩn (từ Khử nhiễm hoặc Đóng gói)
        rows = self.parent_page.db.fetch_all("""
            SELECT id, khoa_giao, ma_do, so_luong, DATE_FORMAT(thoi_gian, '%d/%m %H:%i') as tm, ma_phieu 
            FROM lich_su_giao_nhan 
            WHERE trang_thai IN ('DA_KHU_NHIEM', 'DA_DONG_GOI')
            ORDER BY thoi_gian ASC
        """)
        
        if not rows: return
        
        groups = {}
        for r in rows:
            ma = r['ma_do']
            ten = ma
            # Truy xuất tên
            try:
                b = self.parent_page.db.fetch_one("SELECT ten_bo FROM danh_muc_bo_dung_cu WHERE ma_bo=%s", (ma,))
                if b: ten = b['ten_bo']
                else:
                    v = self.parent_page.db.fetch_one("SELECT ten_do_vai FROM danh_muc_do_vai WHERE ma_do_vai=%s", (ma,))
                    if v: ten = v['ten_do_vai']
                    else:
                        d = self.parent_page.db.fetch_one("SELECT ten_dc FROM danh_muc_dung_cu WHERE ma_dc=%s", (ma,))
                        if d: ten = d['ten_dc']
            except: pass
            r['ten_do'] = ten
            
            key = f"{r['khoa_giao']} - {r['tm']}"
            if key not in groups: groups[key] = []
            groups[key].append(r)
            
        self.tree.blockSignals(True)
        for key, items in groups.items():
            parent = QTreeWidgetItem([key, ""])
            parent.setCheckState(0, Qt.Unchecked)
            parent.setBackground(0, QColor("#ecf0f1"))
            font = QFont()
            font.setBold(True)
            parent.setFont(0, font)
            self.tree.addTopLevelItem(parent)
            
            for it in items:
                child = QTreeWidgetItem([f"[{it['ma_do']}] {it['ten_do']}", ""])
                child.setCheckState(0, Qt.Unchecked)
                child.setData(0, Qt.UserRole, it['id'])
                parent.addChild(child)
                
                from PySide6.QtWidgets import QSpinBox
                spn = QSpinBox()
                spn.setRange(1, int(it['so_luong']))
                spn.setValue(int(it['so_luong']))
                spn.setStyleSheet("font-size: 16px;")
                self.tree.setItemWidget(child, 1, spn)
                
                self.staged_items.append({
                    "khoa_giao": it['khoa_giao'], "loai": "Khac",
                    "ma_san_pham": it['ma_do'], "ten_san_pham": it['ten_do'],
                    "so_luong": int(it['so_luong']), "req_id": it['id'], "spinbox_ref": spn, "tree_item": child
                })
            parent.setExpanded(True)
        self.tree.blockSignals(False)
        self.tree.itemChanged.connect(self.on_tree_item_changed)

    def on_tree_item_changed(self, item, column):
        if column != 0: return
        self.tree.blockSignals(True)
        state = item.checkState(0)
        if item.parent() is None:
            for i in range(item.childCount()): item.child(i).setCheckState(0, state)
        else:
            parent = item.parent()
            all_checked, any_checked = True, False
            for i in range(parent.childCount()):
                if parent.child(i).checkState(0) == Qt.Checked: any_checked = True
                else: all_checked = False
            if all_checked: parent.setCheckState(0, Qt.Checked)
            elif any_checked: parent.setCheckState(0, Qt.PartiallyChecked)
            else: parent.setCheckState(0, Qt.Unchecked)
        self.tree.blockSignals(False)

    def accept(self):
        # Lọc ra những món user thực sự tick chọn
        final_items = []
        for it in self.staged_items:
            if it['tree_item'].checkState(0) == Qt.Checked:
                it['so_luong_chon'] = it['spinbox_ref'].value()
                final_items.append(it)
                
        if not final_items:
            QMessageBox.warning(self, "Lỗi", "Bạn chưa tick chọn món đồ nào!")
            return
        self.staged_items = final_items
        super().accept()

class DetailViewDialog(QDialog):
    def __init__(self, machine_name, items_list, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Chi tiết đồ trong máy - {machine_name}")
        self.setMinimumSize(500, 500)
        layout = QVBoxLayout(self)
        
        tree = QTreeWidget()
        tree.setHeaderLabels(["Nội dung lồng máy", "Số Lượng"])
        tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        layout.addWidget(tree)
        
        tree_dict = {}
        for it in items_list:
            k = it.get('khoa_giao', 'Khoa')
            l = it.get('loai', 'Dụng cụ')
            if k not in tree_dict: tree_dict[k] = {}
            if l not in tree_dict[k]: tree_dict[k][l] = []
            tree_dict[k][l].append(it)
            
        for k_name, groups in tree_dict.items():
            k_item = QTreeWidgetItem(tree, [k_name, ""])
            k_item.setExpanded(True)
            for grp_name, items in groups.items():
                if not items: continue
                grp_item = QTreeWidgetItem(k_item, [grp_name, ""])
                grp_item.setExpanded(True)
                for it in items:
                    QTreeWidgetItem(grp_item, [f"{it.get('ma_san_pham','')} - {it.get('ten_san_pham','')}", str(it.get('so_luong',''))])


class MachineDetailDialog(QDialog):
    """Dialog phóng to thẻ máy, hiển thị đầy đủ thông tin + countdown live."""
    
    def __init__(self, mac, loaded_items, parent=None):
        super().__init__(parent)
        self.mac = mac
        self.loaded_items = loaded_items
        self.setWindowTitle(f"Chi tiết — {mac.get('name', '')}")
        self.resize(700, 560)
        self.setModal(False)  # Non-modal: vẫn dùng được app bình thường
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # --- Header ---
        state = mac.get('status', 'READY')
        state_colors = {
            'READY':    ('#27ae60', 'SẴN SÀNG'),
            'RUNNING':  ('#f39c12', 'ĐANG CHẠY'),
            'WAIT_END': ('#e74c3c', 'CHỜ KẾT QUẢ'),
        }
        color, state_text = state_colors.get(state, ('#7f8c8d', state))
        
        lbl_name = QLabel(mac.get('name', ''))
        lbl_name.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {color};")
        lbl_name.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_name)
        
        lbl_state = QLabel(state_text)
        lbl_state.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {color};")
        lbl_state.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_state)
        
        # --- Countdown ---
        self.lbl_countdown = QLabel("--:--")
        self.lbl_countdown.setStyleSheet("font-size: 64px; font-weight: bold; color: #e74c3c;")
        self.lbl_countdown.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_countdown)
        
        # --- Info Grid ---
        info_layout = QHBoxLayout()
        
        # Lấy thông tin chu trình từ JSON
        cycle_name = '--'
        operator_name = '--'
        start_time_str = '--'
        end_time_obj = mac.get('end_time')
        items_json = mac.get('loaded_items_json', '')
        if items_json:
            try:
                jdata = json.loads(items_json)
                # Dữ liệu từ tiệt khuẩn (list) hoặc rửa máy (dict có 'cycle')
                if isinstance(jdata, dict):
                    cycle_name = jdata.get('cycle', '--')
                    operator_name = jdata.get('operator', '--')
            except:
                pass
        
        end_time_str = str(end_time_obj)[11:16] if end_time_obj else '--'
        
        def make_info_box(title, value, bg='#f8f9fa'):
            box = QFrame()
            box.setStyleSheet(f"QFrame {{ background: {bg}; border-radius: 6px; padding: 4px; }}")
            bl = QVBoxLayout(box)
            t = QLabel(title)
            t.setStyleSheet("font-size: 11px; color: #7f8c8d; font-weight: bold;")
            t.setAlignment(Qt.AlignCenter)
            v = QLabel(str(value))
            v.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
            v.setAlignment(Qt.AlignCenter)
            bl.addWidget(t)
            bl.addWidget(v)
            return box
        
        if cycle_name != '--':
            info_layout.addWidget(make_info_box("Chu trình", cycle_name, '#e8f4f8'))
        info_layout.addWidget(make_info_box("Người vận hành", operator_name, '#eafaf1'))
        info_layout.addWidget(make_info_box("Dự kiến xong lúc", end_time_str, '#fef9e7'))
        info_layout.addWidget(make_info_box("Số phiếu trong máy", len(loaded_items) if loaded_items else 0, '#fdf2f8'))
        layout.addLayout(info_layout)
        
        # --- Tree nội dung ---
        lbl_content = QLabel("📋 Nội dung trong máy:")
        lbl_content.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(lbl_content)
        
        tree = QTreeWidget()
        tree.setHeaderLabels(["Khoa / Loại / Mã đồ — Tên", "Số lượng"])
        tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        tree.setStyleSheet("font-size: 13px;")
        tree.setEditTriggers(QTreeWidget.NoEditTriggers)
        
        if loaded_items:
            tree_dict = {}
            for it in loaded_items:
                k = it.get('khoa_giao', it.get('khoa', 'Không rõ'))
                l = it.get('loai', 'Dụng cụ')
                if k not in tree_dict: tree_dict[k] = {}
                if l not in tree_dict[k]: tree_dict[k][l] = []
                tree_dict[k][l].append(it)
            
            for k_name, groups in tree_dict.items():
                k_item = QTreeWidgetItem(tree, [k_name, ""])
                k_item.setFont(0, QFont("Arial", 14, QFont.Bold))
                k_item.setExpanded(True)
                for grp_name, items in groups.items():
                    grp_item = QTreeWidgetItem(k_item, [grp_name, str(sum(i.get('so_luong', 0) for i in items))])
                    grp_item.setExpanded(True)
                    for it in items:
                        ma = it.get('ma_san_pham', it.get('ma_do', ''))
                        ten = it.get('ten_san_pham', it.get('ma_do', ''))
                        sl = it.get('so_luong', '')
                        QTreeWidgetItem(grp_item, [f"{ma} — {ten}", str(sl)])
        else:
            QTreeWidgetItem(tree, ["(Máy chưa có đồ)", ""])
        
        layout.addWidget(tree)
        
        # --- Nút đóng ---
        btn_close = QPushButton("Đóng")
        btn_close.setStyleSheet("padding: 8px 30px; font-size: 14px;")
        btn_close.clicked.connect(self.close)
        layout.addWidget(btn_close, alignment=Qt.AlignCenter)
        
        # --- Countdown local ticker ---
        self._end_time = end_time_obj
        self._ticker = QTimer(self)
        self._ticker.timeout.connect(self._tick)
        self._ticker.start(1000)
        self._tick()  # Cập nhật ngay lúc mở
    
    def _tick(self):
        if not self._end_time:
            self.lbl_countdown.setText("--:--")
            return
        diff = (self._end_time - datetime.now()).total_seconds()
        if diff <= 0:
            self.lbl_countdown.setText("00:00 ✅")
            self.lbl_countdown.setStyleSheet("font-size: 64px; font-weight: bold; color: #27ae60;")
            self._ticker.stop()
        else:
            hrs, rem = divmod(int(diff), 3600)
            mins, secs = divmod(rem, 60)
            if hrs > 0:
                t = f"{hrs:02d}:{mins:02d}:{secs:02d}"
            else:
                t = f"{mins:02d}:{secs:02d}"
            self.lbl_countdown.setText(t)


class MachineCard(QFrame):
    def __init__(self, parent_page):
        super().__init__()
        self.parent_page = parent_page
        self.mac = None
        self.auto_popped = False
        self.loaded_items = []
        
        self.setFrameShape(QFrame.StyledPanel)
        self.setFixedSize(300, 420)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("Click để xem chi tiết")
        
        layout = QVBoxLayout(self)
        
        self.lbl_name = QLabel()
        self.lbl_name.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        self.lbl_name.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_name)
        
        self.lbl_status = QLabel()
        self.lbl_status.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_status)
        
        self.lbl_time = QLabel("--:--")
        self.lbl_time.setStyleSheet("font-size: 32px; font-weight: bold; color: #e74c3c;")
        self.lbl_time.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_time)
        
        self.tree_items = QTreeWidget()
        self.tree_items.setHeaderLabels(["Nội Dung Lồng Máy", "SL"])
        self.tree_items.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree_items.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tree_items.setEditTriggers(QTreeWidget.NoEditTriggers)
        self.tree_items.setSelectionMode(QTreeWidget.NoSelection)
        self.tree_items.setStyleSheet("QTreeWidget { font-size: 11px; } QHeaderView::section { font-size: 11px; }")
        layout.addWidget(self.tree_items)
        
        btn_layout = QHBoxLayout()
        self.btn_load = QPushButton("Xếp Đồ")
        self.btn_load.clicked.connect(self.on_load)
        
        self.btn_detail = QPushButton("Chi Tiết")
        self.btn_detail.clicked.connect(self.show_detail)
        
        self.btn_action = QPushButton("Bắt đầu")
        self.btn_action.clicked.connect(self.on_action)
        
        self.btn_cancel = QPushButton("Hủy")
        self.btn_cancel.setObjectName("DangerButton")
        self.btn_cancel.clicked.connect(self.on_cancel)
        self.btn_cancel.hide()
        
        btn_layout.addWidget(self.btn_load)
        btn_layout.addWidget(self.btn_detail)
        btn_layout.addWidget(self.btn_action)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)
        
        # Local ticker — cập nhật countdown mỗi giây mà không cần gọi DB
        self._local_ticker = QTimer(self)
        self._local_ticker.timeout.connect(self._tick_local)
        self._local_ticker.start(1000)
        self._local_end_time = None
        
    def _tick_local(self):
        """Chạy mỗi giây để cập nhật countdown mà không reload DB"""
        if not self._local_end_time:
            return
        now = datetime.now()
        diff = (self._local_end_time - now).total_seconds()
        if diff <= 0:
            self.lbl_time.setText("00:00")
            # Khi hết giờ, trigger poll để cập nhật trạng thái từ DB
            if not self.auto_popped:
                self.auto_popped = True
                QTimer.singleShot(500, self.on_action)
        else:
            hrs, rem = divmod(int(diff), 3600)
            mins, secs = divmod(rem, 60)
            if hrs > 0:
                self.lbl_time.setText(f"{hrs:02d}:{mins:02d}:{secs:02d}")
            else:
                self.lbl_time.setText(f"{mins:02d}:{secs:02d}")

    def show_detail(self):
        if self.loaded_items:
            dlg = DetailViewDialog(self.mac['name'], self.loaded_items, self)
            dlg.exec()
        else:
            QMessageBox.information(self, "Trống", "Lồng máy hiện đang trống.")
            
    def on_load(self):
        if self.mac:
            dlg = LoadItemsDialog(self.parent_page, self.mac['name'], self.parent_page)
            if dlg.exec():
                self.parent_page.signal_load_items.emit(self.mac, dlg.staged_items)
            
    def on_action(self):
        if not self.mac: return
        state = self.mac.get('status', 'READY')
        end_time = self.mac.get('end_time')
        
        if state == 'RUNNING' and end_time:
            if (end_time - datetime.now()).total_seconds() <= 0:
                state = 'WAIT_END'
                
        if state == "READY":
            self.parent_page.signal_start.emit(self.mac)
        elif state == "WAIT_END":
            dlg = TestResultDialog(self.mac['name'], self.parent_page)
            if dlg.exec():
                self.parent_page.signal_end.emit(self.mac, dlg.result, dlg.test_note)

    def on_cancel(self):
        if not self.mac: return
        reply = QMessageBox.question(self, "Hủy chu trình", "Bạn có chắc chắn muốn hủy chu trình đang chạy?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.parent_page.signal_cancel.emit(self.mac)

    def mousePressEvent(self, event):
        """Click vào card → mở dialog phóng to"""
        if event.button() == Qt.LeftButton:
            self.open_detail_dialog()
        super().mousePressEvent(event)

    def open_detail_dialog(self):
        if not self.mac:
            return
        # Cập nhật end_time mới nhất từ local ticker
        mac_copy = dict(self.mac)
        if self._local_end_time:
            mac_copy['end_time'] = self._local_end_time
        dlg = MachineDetailDialog(mac_copy, self.loaded_items, self)
        dlg.show()

    def update_data(self, mac):
        self.mac = mac
        self.lbl_name.setText(mac['name'])
        state = mac.get('status', 'READY')
        end_time = mac.get('end_time')
        
        self.tree_items.clear()
        self.loaded_items = []
        items_json = mac.get('loaded_items_json')
        if items_json:
            try:
                self.loaded_items = json.loads(items_json)
                tree_dict = {}
                for it in self.loaded_items:
                    k = it.get('khoa_giao', 'Khoa')
                    l = it.get('loai', 'Dụng cụ')
                    if k not in tree_dict: tree_dict[k] = {}
                    if l not in tree_dict[k]: tree_dict[k][l] = []
                    tree_dict[k][l].append(it)
                    
                for k_name, groups in tree_dict.items():
                    k_item = QTreeWidgetItem(self.tree_items, [k_name, ""])
                    k_item.setExpanded(True)
                    for grp_name, items in groups.items():
                        if not items: continue
                        grp_item = QTreeWidgetItem(k_item, [grp_name, ""])
                        grp_item.setExpanded(True)
                        for it in items:
                            QTreeWidgetItem(grp_item, [f"{it.get('ma_san_pham','')} - {it.get('ten_san_pham','')}", str(it.get('so_luong',''))])
            except: pass

        now = datetime.now()
        time_str = "--:--"
        if state == "RUNNING" and end_time:
            # Lưu end_time để local ticker tự đếm ngược
            self._local_end_time = end_time
            diff = (end_time - now).total_seconds()
            if diff <= 0:
                state = "WAIT_END"
                time_str = "00:00"
                self._local_end_time = None
                if not self.auto_popped:
                    self.auto_popped = True
                    QTimer.singleShot(500, self.on_action)
            else:
                hrs, rem = divmod(int(diff), 3600)
                mins, secs = divmod(rem, 60)
                if hrs > 0:
                    time_str = f"{hrs:02d}:{mins:02d}:{secs:02d}"
                else:
                    time_str = f"{mins:02d}:{secs:02d}"
        else:
            self._local_end_time = None
                
        self.lbl_time.setText(time_str)
        
        if state == "READY":
            self.auto_popped = False
            self.lbl_status.setText("SẴN SÀNG")
            self.lbl_status.setStyleSheet("font-size: 14px; font-weight: bold; color: #27ae60;")
            self.setStyleSheet("QFrame { background-color: #ffffff; border: 2px solid #bdc3c7; border-radius: 8px; }")
            self.btn_action.setText("Bắt đầu")
            self.btn_action.setEnabled(True)
            self.btn_action.setStyleSheet("background-color: #3498db; color: white; padding: 6px; border-radius: 4px; font-weight: bold;")
            self.btn_action.show()
            self.btn_load.show()
            self.btn_detail.hide()
            self.btn_cancel.hide()
            self.tree_items.setStyleSheet("QTreeWidget { font-size: 11px; background-color: #ffffff; }")
        elif state == "RUNNING":
            self.lbl_status.setText("ĐANG CHẠY")
            self.lbl_status.setStyleSheet("font-size: 14px; font-weight: bold; color: #f39c12;")
            self.setStyleSheet("QFrame { background-color: #fffde7; border: 2px solid #f1c40f; border-radius: 8px; }")
            self.btn_action.setText("Đang chạy...")
            self.btn_action.setEnabled(False)
            self.btn_action.setStyleSheet("background-color: #95a5a6; color: white; padding: 6px; border-radius: 4px;")
            self.btn_action.show()
            self.btn_load.hide()
            self.btn_detail.show()
            self.btn_cancel.show()
            self.tree_items.setStyleSheet("QTreeWidget { font-size: 11px; background-color: #f8f9fa; }")
        elif state == "WAIT_END":
            self.lbl_status.setText("CHỜ KẾT QUẢ")
            self.lbl_status.setStyleSheet("font-size: 14px; font-weight: bold; color: #e74c3c;")
            self.setStyleSheet("QFrame { background-color: #ffebee; border: 2px solid #e74c3c; border-radius: 8px; }")
            self.btn_action.setText("Xác nhận KQ")
            self.btn_action.setEnabled(True)
            self.btn_action.setStyleSheet("background-color: #e74c3c; color: white; padding: 6px; border-radius: 4px; font-weight: bold;")
            self.btn_action.show()
            self.btn_load.hide()
            self.btn_detail.show()
            self.btn_cancel.hide()
            self.tree_items.setStyleSheet("QTreeWidget { font-size: 11px; background-color: #f8f9fa; }")

class SterilizationPage(QWidget):
    signal_load_history = Signal()
    signal_poll = Signal()
    signal_cancel = Signal(dict)
    signal_start = Signal(dict)
    signal_end = Signal(dict, str, str)
    signal_load_items = Signal(dict, list)

    def __init__(self):
        super().__init__()
        self.db = None
        self.fetch_session_items_callback = None
        
        layout = QVBoxLayout(self)
        splitter = QSplitter(Qt.Vertical)
        layout.addWidget(splitter)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setMinimumHeight(450)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; } QWidget#cards_container { background: transparent; }")
        self.cards_container = QWidget()
        self.cards_container.setObjectName("cards_container")
        self.cards_layout = QGridLayout(self.cards_container)
        self.cards_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.scroll.setWidget(self.cards_container)
        splitter.addWidget(self.scroll)
        
        bot_widget = QWidget()
        bot_layout = QVBoxLayout(bot_widget)
        bot_layout.setContentsMargins(0,10,0,0)
        
        hl = QHBoxLayout()
        hl.addWidget(QLabel("Lịch sử vận hành lò:"))
        self.dt_history = QDateEdit()
        self.dt_history.setCalendarPopup(True)
        self.dt_history.setDate(QDate.currentDate())
        self.dt_history.dateChanged.connect(lambda: self.signal_load_history.emit())
        hl.addWidget(self.dt_history)
        hl.addStretch()
        
        btn_refresh = QPushButton("Làm mới")
        btn_refresh.clicked.connect(lambda: self.signal_load_history.emit())
        hl.addWidget(btn_refresh)
        
        bot_layout.addLayout(hl)
        
        self.table_history = QTableWidget(0, 5)
        self.table_history.setHorizontalHeaderLabels(["Tên Lò", "Ngày", "Giờ", "Trạng Thái", "Ghi chú"])
        self.table_history.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        bot_layout.addWidget(self.table_history)
        splitter.addWidget(bot_widget)
        
        self.machine_cards = {}
        
        self.timer = QTimer()
        self.timer.timeout.connect(lambda: self.signal_poll.emit())
        self.timer.start(2000)

    def set_db(self, db):
        self.db = db

    def render_table(self, machines):
        if len(machines) != len(getattr(self, 'machine_cards', {})):
            while self.cards_layout.count():
                child = self.cards_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            self.machine_cards = {}
            
            row, col = 0, 0
            for mac in machines:
                card = MachineCard(self)
                self.machine_cards[mac['id']] = card
                self.cards_layout.addWidget(card, row, col)
                col += 1
                if col > 3:
                    col = 0
                    row += 1
                    
        for mac in machines:
            card = self.machine_cards.get(mac['id'])
            if card:
                card.update_data(mac)

    def update_history_table(self, rows):
        self.table_history.setRowCount(0)
        if not rows: return
        self.table_history.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.table_history.setItem(i, 0, QTableWidgetItem(r.get('m_name', '')))
            self.table_history.setItem(i, 1, QTableWidgetItem(str(r.get('date', ''))))
            self.table_history.setItem(i, 2, QTableWidgetItem(str(r.get('time', ''))))
            
            st = QTableWidgetItem(str(r.get('status', '')))
            if r.get('status') == 'PASS': st.setForeground(Qt.green)
            else: st.setForeground(Qt.red)
            self.table_history.setItem(i, 3, st)
            
            self.table_history.setItem(i, 4, QTableWidgetItem(r.get('note', '')))
