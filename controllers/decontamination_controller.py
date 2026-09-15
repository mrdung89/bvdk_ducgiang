from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QListWidget, QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QHeaderView, QMessageBox, QInputDialog, QCheckBox, QSpinBox, QTreeWidgetItem, QScrollArea, QWidget
from PySide6.QtCore import Qt, QObject, QTimer
from models.db_manager import DBManager
from datetime import datetime, timedelta
import json


from PySide6.QtCore import Qt

class SelectionPopup(QDialog):
    def __init__(self, parent, items):
        super().__init__(parent)
        self.setWindowTitle("Chọn đồ đưa vào máy")
        self.resize(1000, 600)
        
        self.all_items = items
        self.selected_items = []
        
        main_layout = QVBoxLayout(self)
        
        # Dual Pane Layout
        pane_layout = QHBoxLayout()
        
        # --- LEFT PANE (Available Items) ---
        left_group = QGroupBox("Đồ trong phiếu (Chưa chọn)")
        left_layout = QVBoxLayout(left_group)
        
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Tìm kiếm...")
        self.search_box.textChanged.connect(self.filter_list)
        left_layout.addWidget(self.search_box)
        
        self.list_available = QListWidget()
        self.list_available.setStyleSheet("font-size: 14px; padding: 5px;")
        self.list_available.itemDoubleClicked.connect(self.on_item_select)
        # also support single click selection with a button or just use double click
        left_layout.addWidget(self.list_available)
        
        pane_layout.addWidget(left_group, 1)
        
        # --- RIGHT PANE (Selected Items) ---
        right_group = QGroupBox("Đã chọn")
        right_layout = QVBoxLayout(right_group)
        
        self.table_selected = QTableWidget(0, 3)
        self.table_selected.setHorizontalHeaderLabels(["Mã đồ", "Tên đồ", "Số lượng"])
        self.table_selected.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_selected.setStyleSheet("font-size: 14px;")
        self.table_selected.setSelectionBehavior(QTableWidget.SelectRows)
        right_layout.addWidget(self.table_selected)
        
        # Buttons for right pane
        btn_remove = QPushButton("Xóa mục chọn")
        btn_remove.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold; padding: 8px;")
        btn_remove.clicked.connect(self.remove_selected)
        right_layout.addWidget(btn_remove)
        
        pane_layout.addWidget(right_group, 1)
        
        main_layout.addLayout(pane_layout)
        
        # --- BOTTOM BUTTONS ---
        btn_layout = QHBoxLayout()
        
        btn_add_all = QPushButton("Chọn tất cả")
        btn_add_all.setStyleSheet("background-color: #3498db; color: white; padding: 10px; font-weight: bold;")
        btn_add_all.clicked.connect(self.select_all)
        
        btn_ok = QPushButton("Hoàn Tất")
        btn_ok.setStyleSheet("background-color: #2ecc71; color: white; padding: 10px; font-weight: bold;")
        btn_ok.clicked.connect(self.accept)
        
        btn_cancel = QPushButton("Hủy")
        btn_cancel.setStyleSheet("padding: 10px;")
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(btn_add_all)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_ok)
        main_layout.addLayout(btn_layout)
        
        self.populate_list()
        
    def populate_list(self):
        self.list_available.clear()
        for it in self.all_items:
            # check how many remaining
            sl_goc = int(it['so_luong'])
            sl_da_chon = sum(x['selected_sl'] for x in self.selected_items if x['id'] == it['id'])
            sl_con_lai = sl_goc - sl_da_chon
            
            if sl_con_lai > 0:
                display_text = f"{it['ma_do']} - {it['ten_do']} (Còn: {sl_con_lai})"
                self.list_available.addItem(display_text)
                # Store item data in UserRole
                last_item = self.list_available.item(self.list_available.count() - 1)
                last_item.setData(Qt.UserRole, it)
                
    def filter_list(self, text):
        text = text.lower()
        for i in range(self.list_available.count()):
            item = self.list_available.item(i)
            it_data = item.data(Qt.UserRole)
            match = text in str(it_data['ma_do']).lower() or text in str(it_data['ten_do']).lower()
            item.setHidden(not match)

    def on_item_select(self, item):
        it_data = item.data(Qt.UserRole)
        sl_goc = int(it_data['so_luong'])
        sl_da_chon = sum(x['selected_sl'] for x in self.selected_items if x['id'] == it_data['id'])
        sl_con_lai = sl_goc - sl_da_chon
        
        if sl_con_lai <= 0:
            return
            
        sl, ok = QInputDialog.getInt(self, "Nhập số lượng", 
                                     f"Nhập số lượng cho {it_data['ten_do']}:", 
                                     value=sl_con_lai, minValue=1, maxValue=sl_con_lai)
        if ok and sl > 0:
            # Check if already in selected
            existing = next((x for x in self.selected_items if x['id'] == it_data['id']), None)
            if existing:
                existing['selected_sl'] += sl
            else:
                new_it = it_data.copy()
                new_it['selected_sl'] = sl
                self.selected_items.append(new_it)
            
            self.update_table()
            self.populate_list()
            
    def select_all(self):
        for i in range(self.list_available.count()):
            item = self.list_available.item(i)
            if not item.isHidden():
                it_data = item.data(Qt.UserRole)
                sl_goc = int(it_data['so_luong'])
                sl_da_chon = sum(x['selected_sl'] for x in self.selected_items if x['id'] == it_data['id'])
                sl_con_lai = sl_goc - sl_da_chon
                if sl_con_lai > 0:
                    existing = next((x for x in self.selected_items if x['id'] == it_data['id']), None)
                    if existing:
                        existing['selected_sl'] += sl_con_lai
                    else:
                        new_it = it_data.copy()
                        new_it['selected_sl'] = sl_con_lai
                        self.selected_items.append(new_it)
        
        self.update_table()
        self.populate_list()
            
    def remove_selected(self):
        selected_rows = self.table_selected.selectedItems()
        if not selected_rows:
            return
        row = selected_rows[0].row()
        item_id = self.table_selected.item(row, 0).data(Qt.UserRole)
        
        # Remove from selected_items
        self.selected_items = [x for x in self.selected_items if x['id'] != item_id]
        self.update_table()
        self.populate_list()

    def update_table(self):
        self.table_selected.setRowCount(0)
        for it in self.selected_items:
            row = self.table_selected.rowCount()
            self.table_selected.insertRow(row)
            
            i1 = QTableWidgetItem(str(it['ma_do']))
            i1.setData(Qt.UserRole, it['id'])
            
            i2 = QTableWidgetItem(str(it['ten_do']))
            i3 = QTableWidgetItem(str(it['selected_sl']))
            i3.setTextAlignment(Qt.AlignCenter)
            
            self.table_selected.setItem(row, 0, i1)
            self.table_selected.setItem(row, 1, i2)
            self.table_selected.setItem(row, 2, i3)

    def get_selected(self):
        return self.selected_items

class DecontaminationController(QObject):
    def __init__(self, view, user_data):
        super().__init__()
        self.view = view
        self.user_data = user_data
        self.db = DBManager()
        
        self.view.setup_ui()
        
        self.current_sessions = {} # { "Khoa - HH:MM": [id1, id2] }
        
        # Connect signals
        self.view.dt_date.dateChanged.connect(self.load_sessions)
        self.view.btn_select_items.clicked.connect(self.open_selection_popup)
        self.view.btn_manual_wash.clicked.connect(lambda: self.process_washing("CLEANED"))
        self.view.btn_machine_wash.clicked.connect(lambda: self.process_washing("WASHING"))
        
        self.load_employees()
        self.load_sessions()
        
        # Timer 5s tự refresh bảng máy giặt (đọc DB)
        self._machine_poll_timer = QTimer()
        self._machine_poll_timer.timeout.connect(self.refresh_wash_machines_table)
        self._machine_poll_timer.start(5000)
        
        # Timer 1s cập nhật countdown local (không gọi DB)
        self._wash_countdown_timer = QTimer()
        self._wash_countdown_timer.timeout.connect(self._tick_wash_countdown)
        self._wash_countdown_timer.start(1000)
        self._wash_end_times = {}
        self._wash_row_map = {}

    def load_employees(self):
        try:
            # Chỉ hiển thị NV thuộc khoa KSNK (role NV_KSNK hoặc ADMIN)
            emps = self.db.fetch_all("SELECT full_name FROM employees WHERE role IN ('NV_KSNK', 'ADMIN', 'LANH_DAO') ORDER BY full_name")
            self.view.cb_employee.clear()
            
            # Thêm user hiện tại vào đầu tiên nếu chưa có
            current_user = self.user_data.get('full_name', '')
            if current_user:
                self.view.cb_employee.addItem(current_user)
                
            if emps:
                for emp in emps:
                    name = emp['full_name']
                    if name != current_user: # Tránh trùng lặp
                        self.view.cb_employee.addItem(name)
        except Exception as e:
            print("Error loading employees:", e)

    def refresh_wash_machines_table(self):
        """Làm mới bảng máy giặt đang chạy (gọi từ DB mỗi 5s)"""
        if not hasattr(self.view, 'table_wash_machines'):
            return
        try:
            from PySide6.QtWidgets import QPushButton, QTableWidgetItem
            machines = self.db.fetch_all("SELECT * FROM machines WHERE group_id=1")
            if not machines:
                machines = []
            running = [m for m in machines if m.get('status', 'READY') == 'RUNNING']
            
            # Lưu end_times để local ticker dùng
            self._wash_end_times = {}
            for m in running:
                if m.get('end_time'):
                    self._wash_end_times[m['id']] = m['end_time']
            
            self.view.table_wash_machines.setRowCount(len(running))
            self._wash_row_map = {}  # machine_id -> row index
            
            for row, m in enumerate(running):
                self._wash_row_map[m['id']] = row
                self.view.table_wash_machines.setItem(row, 0, QTableWidgetItem(m['name']))
                
                cycle_name = ''
                operator_name = ''
                try:
                    jdata = json.loads(m.get('loaded_items_json') or '{}')
                    cycle_name = jdata.get('cycle', '')
                    operator_name = jdata.get('operator', '')
                except:
                    pass
                self.view.table_wash_machines.setItem(row, 1, QTableWidgetItem(cycle_name))
                self.view.table_wash_machines.setItem(row, 2, QTableWidgetItem(operator_name))
                
                # Cột countdown — sẽ được local ticker cập nhật
                end_time = m.get('end_time')
                if end_time:
                    diff = (end_time - datetime.now()).total_seconds()
                    if diff > 0:
                        mins, secs = divmod(int(diff), 60)
                        hrs, mins = divmod(mins, 60)
                        if hrs > 0:
                            time_str = f"{hrs:02d}:{mins:02d}:{secs:02d}"
                        else:
                            time_str = f"{mins:02d}:{secs:02d}"
                    else:
                        time_str = "00:00"
                else:
                    time_str = "--:--"
                self.view.table_wash_machines.setItem(row, 3, QTableWidgetItem(time_str))
                
                btn = QPushButton("✅ Hoàn thành")
                btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 3px 8px;")
                mac_id = m['id']
                btn.clicked.connect(lambda ch, mid=mac_id: self.force_complete_wash(mid))
                self.view.table_wash_machines.setCellWidget(row, 4, btn)
        except Exception as e:
            print("refresh_wash_machines_table error:", e)

    def _tick_wash_countdown(self):
        """Local ticker 1s — cập nhật cột countdown mà không gọi DB"""
        if not hasattr(self.view, 'table_wash_machines'):
            return
        if not hasattr(self, '_wash_end_times') or not hasattr(self, '_wash_row_map'):
            return
        from PySide6.QtWidgets import QTableWidgetItem
        now = datetime.now()
        for mac_id, end_time in self._wash_end_times.items():
            row = self._wash_row_map.get(mac_id)
            if row is None:
                continue
            diff = (end_time - now).total_seconds()
            if diff <= 0:
                time_str = "00:00 ⚠️"
            else:
                mins, secs = divmod(int(diff), 60)
                hrs, mins = divmod(mins, 60)
                if hrs > 0:
                    time_str = f"{hrs:02d}:{mins:02d}:{secs:02d}"
                else:
                    time_str = f"{mins:02d}:{secs:02d}"
            self.view.table_wash_machines.setItem(row, 3, QTableWidgetItem(time_str))

    def load_sessions(self):
        self.refresh_wash_machines_table()
        # Vẫn giữ dòng này để tránh lỗi nếu có biến nào khác gọi đến, dù ta không dùng dt để lọc SQL nữa
        dt = self.view.dt_date.date().toString("yyyy-MM-dd") 
        self.view.cb_sessions.clear()
        self.current_sessions.clear()
        
        try:
            # 1. BỎ ĐIỀU KIỆN DATE(thoi_gian) = %s ĐỂ LẤY TOÀN BỘ ĐỒ ĐANG CHỜ
            # 2. Đổi định dạng tm thành '%d/%m %H:%i' để hiển thị luôn ngày gửi
            rows = self.db.fetch_all("""
                SELECT id, khoa_giao, ma_do, so_luong, DATE_FORMAT(thoi_gian, '%d/%m %H:%i') as tm 
                FROM lich_su_giao_nhan 
                WHERE trang_thai IN ('DA_TIEP_NHAN', 'DANG_GIAT')
            """)
            
            # Group by Khoa and Time
            for r in rows:
                # Key hiển thị sẽ có dạng: "Khoa Ngoại - 14/09 08:30"
                key = f"{r['khoa_giao']} - {r['tm']}"
                if key not in self.current_sessions:
                    self.current_sessions[key] = []
                self.current_sessions[key].append(r)
                
            for key in self.current_sessions.keys():
                self.view.cb_sessions.addItem(key)
                
        except Exception as e:
            print("Error loading sessions:", e)

    def open_selection_popup(self):
        key = self.view.cb_sessions.currentText()
        if not key or key not in self.current_sessions:
            QMessageBox.warning(self.view, "Lỗi", "Vui lòng chọn một phiên giao nhận hợp lệ!")
            return
            
        items = self.current_sessions[key]
        if not items:
            return
            
        # Lấy danh sách ID các phiếu đã nằm sẵn trong giỏ hàng
        cart_ids = set()
        for i in range(self.view.tree_cart.topLevelItemCount()):
            node = self.view.tree_cart.topLevelItem(i)
            pgd_ids = node.data(0, Qt.UserRole)
            if pgd_ids:
                for x in pgd_ids:
                    if isinstance(x, dict):
                        cart_ids.add(x['id'])
                    else:
                        cart_ids.add(x)
                
        # Lọc bỏ những phiếu đã có trong giỏ
        available_items = [it for it in items if it['id'] not in cart_ids]
        
        # Nếu tất cả đã nằm trong giỏ thì chặn popup hiển thị
        if not available_items:
            QMessageBox.information(self.view, "Thông báo", "Tất cả đồ của phiên này đã được đưa vào giỏ!")
            return
            
        # Enrich with ten_do
        for it in available_items:
            ma = it['ma_do']
            ten = ma
            is_digit = str(ma).isdigit()
            try:
                q1 = "SELECT ten_bo FROM danh_muc_bo_dung_cu WHERE ma_bo=%s" + (" OR id=%s" if is_digit else "")
                p1 = (ma, ma) if is_digit else (ma,)
                res1 = self.db.fetch_one(q1, p1)
                if res1: ten = res1['ten_bo']
                else:
                    q2 = "SELECT ten_do_vai FROM danh_muc_do_vai WHERE ma_do_vai=%s" + (" OR id=%s" if is_digit else "")
                    p2 = (ma, ma) if is_digit else (ma,)
                    res2 = self.db.fetch_one(q2, p2)
                    if res2: ten = res2['ten_do_vai']
                    else:
                        q3 = "SELECT ten_dc FROM danh_muc_dung_cu WHERE ma_dc=%s" + (" OR id=%s" if is_digit else "")
                        p3 = (ma, ma) if is_digit else (ma,)
                        res3 = self.db.fetch_one(q3, p3)
                        if res3: ten = res3['ten_dc']
            except: pass
            it['ten_do'] = ten

        dlg = SelectionPopup(self.view, available_items)
        if dlg.exec():
            selected_items = dlg.get_selected()
            for it in selected_items:
                self.add_to_cart(it)
                
    def add_to_cart(self, item_data):
        for i in range(self.view.tree_cart.topLevelItemCount()):
            node = self.view.tree_cart.topLevelItem(i)
            if node.text(0) == item_data['ma_do']:
                old_sl = int(node.text(2))
                node.setText(2, str(old_sl + item_data['selected_sl']))
                
                pgd_ids = node.data(0, Qt.UserRole)
                if not pgd_ids: pgd_ids = []
                # Lưu dict gồm ID phiếu và số lượng chọn
                pgd_ids.append({'id': item_data['id'], 'sl': item_data['selected_sl']})
                node.setData(0, Qt.UserRole, pgd_ids)
                return
                
        node = QTreeWidgetItem([item_data['ma_do'], item_data['ten_do'], str(item_data['selected_sl'])])
        node.setData(0, Qt.UserRole, [{'id': item_data['id'], 'sl': item_data['selected_sl']}])
        self.view.tree_cart.addTopLevelItem(node)

    def process_washing(self, status):
        count = self.view.tree_cart.topLevelItemCount()
        if count == 0:
            QMessageBox.warning(self.view, "Cảnh báo", "Giỏ hàng đang trống!")
            return
        
        # Nếu bấm "Rửa máy" thì mở dialog chọn máy & chu trình
        if status == "WASHING":
            self.open_washing_machine_dialog()
            return
            
        nguoi_thuc_hien = self.view.cb_employee.currentText()
        phuong_phap = "Rửa thủ công"
            
        try:
            for i in range(count):
                node = self.view.tree_cart.topLevelItem(i)
                pgd_info = node.data(0, Qt.UserRole)
                
                for p_data in pgd_info:
                    pid = p_data['id']
                    sl_chon = p_data['sl']
                    
                    # 1. Check database lấy số lượng gốc
                    req = self.db.fetch_one("SELECT * FROM lich_su_giao_nhan WHERE id=%s", (pid,))
                    if not req: continue
                    sl_goc = int(req['so_luong'])
                    
                    # 2. Logic Tách Phiếu
                    if sl_chon < sl_goc:
                        sl_con_lai = sl_goc - sl_chon
                        # Clone phiếu mới cho số thừa lại, giữ nguyên trạng thái cũ
                        self.db.execute("""INSERT INTO lich_su_giao_nhan 
                            (khoa_giao, ma_do, so_luong, trang_thai, thoi_gian, ma_phieu) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s)""", 
                            (req['khoa_giao'], req['ma_do'], sl_con_lai, req['trang_thai'], req['thoi_gian'], req['ma_phieu']))
                        
                        # Cập nhật phiếu hiện tại thành số lượng đưa vào máy
                        self.db.execute("UPDATE lich_su_giao_nhan SET so_luong=%s, trang_thai='DA_KHU_NHIEM' WHERE id=%s", (sl_chon, pid))
                    else:
                        # Chọn hết thì chỉ cần update trạng thái
                        self.db.execute("UPDATE lich_su_giao_nhan SET trang_thai='DA_KHU_NHIEM' WHERE id=%s", (pid,))
                    
                    # 3. Lưu log
                    self.db.execute("INSERT INTO lich_su_bien_dong (thoi_gian, nguoi_thuc_hien, bang_du_lieu, ma_item, noi_dung) VALUES (NOW(), %s, %s, %s, %s)", 
                           (nguoi_thuc_hien, 'lich_su_giao_nhan', pid, f"Khử nhiễm ({phuong_phap}) - SL: {sl_chon}"))
                    
            QMessageBox.information(self.view, "Thành công", f"Đã khử nhiễm ({phuong_phap}) xong!")
            self.view.tree_cart.clear()
            self.load_sessions()
            
        except Exception as e:
            QMessageBox.warning(self.view, "Lỗi", f"Có lỗi xảy ra: {e}")


    def open_washing_machine_dialog(self):
        """Mở dialog chọn máy giặt và chu trình"""
        try:
            # Lấy danh sách máy giặt (group_id=1)
            machines = self.db.fetch_all("SELECT * FROM machines WHERE group_id=1")
            if not machines:
                QMessageBox.warning(self.view, "Không tìm thấy máy", "Chưa có máy giặt nào được cấu hình.")
                return
            
            machine_names = []
            for m in machines:
                status_text = "🟢 Sẵn sàng" if m['status'] == 'READY' else f"🔴 Đang chạy (xong lúc {str(m['end_time'])[11:16]})"
                machine_names.append(f"{m['name']} - {status_text}")
            
            chosen_mac, ok = QInputDialog.getItem(self.view, "Chọn máy giặt", "Máy giặt:", machine_names, 0, False)
            if not ok or not chosen_mac:
                return
            
            mac = machines[machine_names.index(chosen_mac)]
            
            if mac['status'] != 'READY':
                QMessageBox.warning(self.view, "Máy đang bận", f"{mac['name']} đang chạy chu trình khác!")
                return
            
            # Lấy chu trình phù hợp của máy
            cycles = self.db.fetch_all(
                "SELECT c.id, c.name, c.thoi_gian FROM cycle_types c "
                "JOIN machine_cycle_types m ON c.id=m.cycle_type_id WHERE m.machine_id=%s",
                (mac['id'],)
            )
            if not cycles:
                QMessageBox.warning(self.view, "Chưa cấu hình", 
                                    f"Máy {mac['name']} chưa được gán chu trình. Vào Quản lý để cấu hình.")
                return
            
            cycle_names = [f"{c['name']} ({c['thoi_gian']} phút)" for c in cycles]
            chosen_cyc, ok2 = QInputDialog.getItem(self.view, "Chọn chu trình", "Chu trình rửa:", cycle_names, 0, False)
            if not ok2 or not chosen_cyc:
                return
            
            cycle = cycles[cycle_names.index(chosen_cyc)]
            self.start_washing_machine(mac, cycle)
            
        except Exception as e:
            QMessageBox.critical(self.view, "Lỗi", str(e))

    def start_washing_machine(self, mac, cycle):
        """Bắt đầu chạy máy giặt, lưu item vào máy, đếm ngược"""
        nguoi_thuc_hien = self.view.cb_employee.currentText()
        
        try:
            # Thu thập item từ giỏ
            items_list = []
            for i in range(self.view.tree_cart.topLevelItemCount()):
                node = self.view.tree_cart.topLevelItem(i)
                pgd_info = node.data(0, Qt.UserRole)
                if pgd_info:
                    for p_data in pgd_info:
                        pid = p_data['id']
                        sl_chon = p_data['sl']
                        
                        req = self.db.fetch_one("SELECT * FROM lich_su_giao_nhan WHERE id=%s", (pid,))
                        if not req:
                            continue
                        sl_goc = int(req['so_luong'])
                        
                        # Tách phiếu nếu chọn 1 phần
                        if sl_chon < sl_goc:
                            sl_con_lai = sl_goc - sl_chon
                            self.db.execute(
                                "INSERT INTO lich_su_giao_nhan (khoa_giao, ma_do, so_luong, trang_thai, thoi_gian, ma_phieu) "
                                "VALUES (%s, %s, %s, %s, %s, %s)",
                                (req['khoa_giao'], req['ma_do'], sl_con_lai, req['trang_thai'], req['thoi_gian'], req['ma_phieu'])
                            )
                            self.db.execute(
                                "UPDATE lich_su_giao_nhan SET so_luong=%s, trang_thai='DANG_RUA_MAY' WHERE id=%s",
                                (sl_chon, pid)
                            )
                        else:
                            self.db.execute(
                                "UPDATE lich_su_giao_nhan SET trang_thai='DANG_RUA_MAY' WHERE id=%s", (pid,)
                            )
                        
                        self.db.execute(
                            "INSERT INTO lich_su_bien_dong (thoi_gian, nguoi_thuc_hien, bang_du_lieu, ma_item, noi_dung) "
                            "VALUES (NOW(), %s, %s, %s, %s)",
                            (nguoi_thuc_hien, 'lich_su_giao_nhan', pid, 
                             f"Đưa vào {mac['name']} - Chu trình: {cycle['name']} - SL: {sl_chon}")
                        )
                        
                        items_list.append({
                            'req_id': pid,
                            'ma_do': req['ma_do'],
                            'so_luong': sl_chon,
                            'khoa_giao': req['khoa_giao'],
                            'chu_trinh': cycle['name'],
                        })
            
            if not items_list:
                QMessageBox.warning(self.view, "Lỗi", "Không có đồ hợp lệ để đưa vào máy!")
                return
            
            # Cập nhật trạng thái máy
            cycle_mins = int(cycle.get('thoi_gian', 60))
            end_time = datetime.now() + timedelta(minutes=cycle_mins)
            
            # Lưu thêm info chu trình vào JSON của máy
            machine_data = {
                'items': items_list,
                'cycle': cycle['name'],
                'cycle_mins': cycle_mins,
                'operator': nguoi_thuc_hien,
            }
            self.db.execute(
                "UPDATE machines SET status='RUNNING', end_time=%s, loaded_items_json=%s WHERE id=%s",
                (end_time, json.dumps(machine_data, ensure_ascii=False), mac['id'])
            )
            
            # Xóa giỏ hàng
            self.view.tree_cart.clear()
            self.load_sessions()
            
            # Bắt đầu đếm ngược hiển thị
            self._wash_mac_id = mac['id']
            self._wash_mac_name = mac['name']
            self._wash_end_time = end_time
            self._wash_cycle_mins = cycle_mins
            
            if not hasattr(self, '_wash_timer'):
                self._wash_timer = QTimer()
                self._wash_timer.timeout.connect(self._tick_wash_timer)
            self._wash_timer.start(1000)
            
            QMessageBox.information(
                self.view, "Bắt đầu",
                f"✅ Đã nạp {len(items_list)} phiếu vào {mac['name']}\n"
                f"Chu trình: {cycle['name']}\n"
                f"Thời gian chạy: {cycle_mins} phút\n"
                f"Dự kiến xong lúc: {end_time.strftime('%H:%M')}"
            )
            
        except Exception as e:
            QMessageBox.critical(self.view, "Lỗi", str(e))

    def _tick_wash_timer(self):
        """Đếm ngược và tự động hoàn thành khi hết giờ"""
        now = datetime.now()
        remaining = (self._wash_end_time - now).total_seconds()
        
        if remaining <= 0:
            self._wash_timer.stop()
            self.complete_washing_machine(self._wash_mac_id, self._wash_mac_name)

    def complete_washing_machine(self, mac_id, mac_name):
        """Hoàn thành chu trình rửa máy, chuyển trạng thái sang DA_KHU_NHIEM"""
        try:
            mac = self.db.fetch_one("SELECT * FROM machines WHERE id=%s", (mac_id,))
            if not mac:
                return
            
            machine_data_str = mac.get('loaded_items_json')
            if machine_data_str:
                try:
                    machine_data = json.loads(machine_data_str)
                    items_list = machine_data.get('items', [])
                    cycle_name = machine_data.get('cycle', '')
                    operator = machine_data.get('operator', '')
                except:
                    items_list = []
                    cycle_name = ''
                    operator = ''
                
                now = datetime.now()
                for it in items_list:
                    req_id = it.get('req_id')
                    if req_id:
                        # Chuyển sang DA_KHU_NHIEM = có thể đưa vào tiệt khuẩn
                        self.db.execute(
                            "UPDATE lich_su_giao_nhan SET trang_thai='DA_KHU_NHIEM' WHERE id=%s AND trang_thai='DANG_RUA_MAY'",
                            (req_id,)
                        )
                        self.db.execute(
                            "INSERT INTO lich_su_bien_dong (thoi_gian, nguoi_thuc_hien, bang_du_lieu, ma_item, noi_dung) "
                            "VALUES (NOW(), %s, %s, %s, %s)",
                            (operator, 'lich_su_giao_nhan', req_id,
                             f"Hoàn thành rửa máy - Chu trình: {cycle_name} - Máy: {mac_name}")
                        )
                        # Ghi nhật ký khử nhiễm
                        self.db.execute(
                            "INSERT INTO nhat_ky_khu_nhiem (ma_do, ten_do, nguoi_thuc_hien, phuong_phap) "
                            "VALUES (%s, %s, %s, %s)",
                            (it.get('ma_do', ''), it.get('ma_do', ''), operator,
                             f"Rửa máy - {cycle_name} - {mac_name}")
                        )
            
            # Reset máy về READY
            self.db.execute(
                "UPDATE machines SET status='READY', end_time=NULL, loaded_items_json=NULL WHERE id=%s",
                (mac_id,)
            )
            
            self.load_sessions()
            
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(
                self.view, "✅ Hoàn thành",
                f"Máy {mac_name} đã hoàn thành chu trình!\n"
                f"Tất cả phiếu đã sẵn sàng để đưa vào Tiệt khuẩn."
            )
            
        except Exception as e:
            print("complete_washing_machine error:", e)

    def force_complete_wash(self, mac_id):
        """Cho phép người dùng bấm hoàn thành thủ công (nếu không muốn chờ đếm ngược)"""
        mac = self.db.fetch_one("SELECT * FROM machines WHERE id=%s", (mac_id,))
        if not mac or mac['status'] != 'RUNNING':
            QMessageBox.warning(self.view, "Lỗi", "Máy không đang chạy!")
            return
        reply = QMessageBox.question(
            self.view, "Xác nhận hoàn thành",
            f"Bạn có chắc muốn kết thúc chu trình của {mac['name']} sớm?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if hasattr(self, '_wash_timer'):
                self._wash_timer.stop()
            self.complete_washing_machine(mac_id, mac['name'])
