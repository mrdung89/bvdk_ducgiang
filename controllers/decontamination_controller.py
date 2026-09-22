from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QListWidget, QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QHeaderView, QMessageBox, QInputDialog, QCheckBox, QSpinBox, QTreeWidgetItem, QScrollArea, QWidget
from PySide6.QtCore import Qt, QObject, QTimer
from models.db_manager import DBManager
from datetime import datetime, timedelta
import json


from PySide6.QtCore import Qt

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
        
        self.view.btn_manual_wash.clicked.connect(lambda: self.process_washing("CLEANED"))
        self.view.btn_machine_wash.clicked.connect(lambda: self.process_washing("WASHING"))
        
        self.load_employees()
        self.load_sessions()
        
        # Timer 5s tự refresh bảng Máy Rửa/Khử khuẩn (đọc DB)
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
        """Làm mới bảng Máy Rửa/Khử khuẩn đang chạy (gọi từ DB mỗi 5s)"""
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
        # Vẫn giữ dt_date phòng hờ, nhưng tải toàn bộ chờ
        self.view.tree_cart.clear()
        
        try:
            # ORDER BY thoi_gian DESC để ưu tiên phiên mới nhất lên trên
            rows = self.db.fetch_all("""
                SELECT id, khoa_giao, ma_do, so_luong, DATE_FORMAT(thoi_gian, '%d/%m %H:%i') as tm 
                FROM lich_su_giao_nhan 
                WHERE trang_thai IN ('DA_TIEP_NHAN', 'DANG_GIAT')
                ORDER BY thoi_gian DESC, id DESC
            """)
            
            # Enrich ten_do
            for r in rows:
                ma = r['ma_do']
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
                r['ten_do'] = ten
            
            # Group by Phiên
            from collections import OrderedDict
            groups = OrderedDict()
            for r in rows:
                key = f"{r['khoa_giao']} - {r['tm']}"
                if key not in groups:
                    groups[key] = []
                groups[key].append(r)
                
            self.view.tree_cart.blockSignals(True)
            for key, items in groups.items():
                parent = QTreeWidgetItem([key, "", ""])
                parent.setCheckState(0, Qt.Unchecked)
                # Đổi màu nền cho Parent để dễ nhìn
                from PySide6.QtGui import QColor, QFont
                parent.setBackground(0, QColor("#ecf0f1"))
                parent.setBackground(1, QColor("#ecf0f1"))
                parent.setBackground(2, QColor("#ecf0f1"))
                font = QFont()
                font.setBold(True)
                parent.setFont(0, font)
                
                self.view.tree_cart.addTopLevelItem(parent)
                
                for it in items:
                    child = QTreeWidgetItem([it['ma_do'], it['ten_do'], ""])
                    child.setCheckState(0, Qt.Unchecked)
                    child.setData(0, Qt.UserRole, it['id'])
                    
                    parent.addChild(child)
                    
                    from PySide6.QtWidgets import QSpinBox
                    spin = QSpinBox()
                    spin.setMinimum(1)
                    spin.setMaximum(int(it['so_luong']))
                    spin.setValue(int(it['so_luong']))
                    spin.setStyleSheet("font-size: 16px;")
                    
                    # Store logic data in child UserRole 2
                    child.setData(2, Qt.UserRole, spin) 
                    self.view.tree_cart.setItemWidget(child, 2, spin)
                    
                parent.setExpanded(True)
            self.view.tree_cart.blockSignals(False)
            
            # Hook itemChanged
            try: self.view.tree_cart.itemChanged.disconnect()
            except: pass
            self.view.tree_cart.itemChanged.connect(self.on_tree_item_changed)
                
        except Exception as e:
            print("Error load_sessions:", e)

    def on_tree_item_changed(self, item, column):
        if column != 0: return
        self.view.tree_cart.blockSignals(True)
        state = item.checkState(0)
        
        # Nếu là Parent -> đổi tất cả con
        if item.parent() is None:
            for i in range(item.childCount()):
                item.child(i).setCheckState(0, state)
        else:
            # Nếu là Child -> kiểm tra lại Parent
            parent = item.parent()
            all_checked = True
            any_checked = False
            for i in range(parent.childCount()):
                if parent.child(i).checkState(0) == Qt.Checked:
                    any_checked = True
                else:
                    all_checked = False
            if all_checked: parent.setCheckState(0, Qt.Checked)
            elif any_checked: parent.setCheckState(0, Qt.PartiallyChecked)
            else: parent.setCheckState(0, Qt.Unchecked)
        self.view.tree_cart.blockSignals(False)

    def process_washing(self, status):
        count = self.view.tree_cart.topLevelItemCount()
        if count == 0:
            QMessageBox.warning(self.view, "Cảnh báo", "Không có dữ liệu!")
            return
            
        # Thu thập các mục được chọn
        selected_items = []
        for i in range(count):
            parent = self.view.tree_cart.topLevelItem(i)
            for j in range(parent.childCount()):
                child = parent.child(j)
                if child.checkState(0) == Qt.Checked:
                    pid = child.data(0, Qt.UserRole)
                    spin = child.data(2, Qt.UserRole)
                    if spin:
                        sl_chon = spin.value()
                        selected_items.append({'id': pid, 'sl': sl_chon})
                        
        if not selected_items:
            QMessageBox.warning(self.view, "Cảnh báo", "Vui lòng tích chọn ít nhất 1 món đồ!")
            return

        # Nếu bấm "Rửa máy" thì mở dialog chọn máy & chu trình
        if status == "WASHING":
            # Lưu tạm vào biến để truyền qua máy
            self.temp_selected_items = selected_items
            self.open_washing_machine_dialog()
            return
            
        nguoi_thuc_hien = self.view.cb_employee.currentText()
        phuong_phap = "Rửa thủ công"
            
        try:
            for p_data in selected_items:
                pid = p_data['id']
                sl_chon = p_data['sl']
                
                # 1. Check database lấy số lượng gốc
                row = self.db.fetch_one("SELECT so_luong, ma_do, khoa_giao FROM lich_su_giao_nhan WHERE id=%s", (pid,))
                if not row: continue
                sl_goc = int(row['so_luong'])
                
                # 2. Tạo log (rửa thủ công)
                if sl_chon >= sl_goc:
                    self.db.execute("UPDATE lich_su_giao_nhan SET trang_thai='DA_KHU_NHIEM' WHERE id=%s", (pid,))
                else:
                    self.db.execute("UPDATE lich_su_giao_nhan SET so_luong=so_luong-%s WHERE id=%s", (sl_chon, pid))
                    self.db.execute("""
                        INSERT INTO lich_su_giao_nhan (ma_do, so_luong, khoa_giao, phuong_phap, thoi_gian, nguoi_giao, trang_thai)
                        VALUES (%s, %s, %s, %s, NOW(), %s, 'DA_KHU_NHIEM')
                    """, (row['ma_do'], sl_chon, row['khoa_giao'], phuong_phap, nguoi_thuc_hien))
                    
            QMessageBox.information(self.view, "Thành công", "Đã ghi nhận Khử Nhiễm (Thủ công)!")
            self.load_sessions()
            
        except Exception as e:
            QMessageBox.critical(self.view, "Lỗi", f"Lỗi khi lưu dữ liệu: {e}")

    def open_washing_machine_dialog(self):
        """Mở dialog chọn Máy Rửa/Khử khuẩn và chu trình"""
        try:
            # Lấy danh sách Máy Rửa/Khử khuẩn (group_id=1)
            machines = self.db.fetch_all("SELECT * FROM machines WHERE group_id=1")
            if not machines:
                QMessageBox.warning(self.view, "Không tìm thấy máy", "Chưa có Máy Rửa/Khử khuẩn nào được cấu hình.")
                return
            
            machine_names = []
            for m in machines:
                status_text = "🟢 Sẵn sàng" if m['status'] == 'READY' else f"🔴 Đang chạy (xong lúc {str(m['end_time'])[11:16]})"
                machine_names.append(f"{m['name']} - {status_text}")
            
            chosen_mac, ok = QInputDialog.getItem(self.view, "Chọn Máy Rửa/Khử khuẩn", "Máy Rửa/Khử khuẩn:", machine_names, 0, False)
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
        """Bắt đầu chạy Máy Rửa/Khử khuẩn, lưu item vào máy, đếm ngược"""
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

    def start_washing_machine(self, mac_id, cycle_id):
        selected_items = getattr(self, 'temp_selected_items', [])
        if not selected_items: return
        
        nguoi_thuc_hien = self.view.cb_employee.currentText()
        phuong_phap = "Rửa Máy"
        
        try:
            # Get cycle info
            cycle = self.db.fetch_one("SELECT thoi_gian_phut FROM danh_muc_chu_trinh WHERE id=%s", (cycle_id,))
            mins = int(cycle['thoi_gian_phut']) if cycle else 30
            
            from datetime import datetime, timedelta
            end_time = datetime.now() + timedelta(minutes=mins)
            
            loaded_ids = []
            
            for p_data in selected_items:
                pid = p_data['id']
                sl_chon = p_data['sl']
                
                row = self.db.fetch_one("SELECT so_luong, ma_do, khoa_giao FROM lich_su_giao_nhan WHERE id=%s", (pid,))
                if not row: continue
                sl_goc = int(row['so_luong'])
                
                if sl_chon >= sl_goc:
                    self.db.execute("UPDATE lich_su_giao_nhan SET trang_thai='DANG_RUA_MAY' WHERE id=%s", (pid,))
                    loaded_ids.append({'id': pid, 'ma_do': row['ma_do'], 'sl': sl_chon})
                else:
                    self.db.execute("UPDATE lich_su_giao_nhan SET so_luong=so_luong-%s WHERE id=%s", (sl_chon, pid))
                    new_id = self.db.execute("""
                        INSERT INTO lich_su_giao_nhan (ma_do, so_luong, khoa_giao, phuong_phap, thoi_gian, nguoi_giao, trang_thai)
                        VALUES (%s, %s, %s, %s, NOW(), %s, 'DANG_RUA_MAY')
                    """, (row['ma_do'], sl_chon, row['khoa_giao'], phuong_phap, nguoi_thuc_hien))
                    loaded_ids.append({'id': new_id, 'ma_do': row['ma_do'], 'sl': sl_chon})
            
            import json
            items_json = json.dumps(loaded_ids)
            
            self.db.execute("""
                UPDATE machines 
                SET status='RUNNING', current_cycle_id=%s, employee_name=%s, end_time=%s, loaded_items_json=%s 
                WHERE id=%s
            """, (cycle_id, nguoi_thuc_hien, end_time, items_json, mac_id))
            
            # Ghi lịch sử biến động
            self.db.execute("""
                INSERT INTO lich_su_bien_dong_may (machine_id, status_from, status_to, note) 
                VALUES (%s, 'READY', 'RUNNING', %s)
            """, (mac_id, f"Bắt đầu chu trình {cycle_id}"))
            
            QMessageBox.information(self.view, "Thành công", f"Máy {mac_id} bắt đầu chạy!")
            self.load_sessions()
            
        except Exception as e:
            QMessageBox.critical(self.view, "Lỗi", f"Lỗi khi lưu dữ liệu: {e}")


