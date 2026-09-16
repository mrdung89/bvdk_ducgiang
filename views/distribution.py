from utils.vietnamese_filter import remove_vietnamese_accents
from PySide6.QtWidgets import (QComboBox, QWidget, QLineEdit, QListWidget, QVBoxLayout, QHBoxLayout, QPushButton, QDateEdit, 
                               QLabel, QTableWidget, QTableWidgetItem, QTreeWidget, QTreeWidgetItem, QHeaderView, QTabWidget, 
                               QMessageBox, QInputDialog, QFileDialog)
from PySide6.QtCore import QTimer, Qt, QDate
from models.db_manager import DBManager
from utils.ui_helpers import get_autocomplete_input
from utils.multi_item_dialog import MultiItemDialog
import csv

class ReceivePage(QWidget):
    def __init__(self, user_data=None):
        super().__init__()
        self.user_data = user_data or {"role": "ADMIN", "khoa_id": "Unknown", "full_name": "Admin"}
        self.role = self.user_data.get('role', 'ADMIN')
        self.khoa = self.user_data.get('khoa_id', 'Unknown')
        
        self.db = DBManager()
        self.last_notified_id = -1
        layout = QVBoxLayout(self)
        
        # --- Date Picker ---
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("Ngày làm việc:"))
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        top_layout.addWidget(self.date_edit)
        top_layout.addStretch()
        layout.addLayout(top_layout)
        # -------------------

        self.tabs = QTabWidget()
        
        if self.role != "KHOA_LAM_SANG":
            # KSNK Receiving - Gets both the Approval table and the Creation form
            self.tab_multi = QWidget()
            self.setup_multi_tab()
            self.tabs.addTab(self.tab_multi, "Duyệt Phiếu Gửi (App & GG Form)")
            
            self.tab_ward_send = QWidget()
            self.setup_ward_send_tab()
            self.tabs.addTab(self.tab_ward_send, "Tạo Phiếu Giao Nhận Tại Chỗ")
            
            # Google Form sync timer & button setup will be inside setup_multi_tab
        else:
            # Wards see only their creation and history tabs
            self.tab_ward_send = QWidget()
            self.setup_ward_send_tab()
            self.tabs.addTab(self.tab_ward_send, "1. Tạo Phiếu Giao Nhận")
            
            self.tab_ward_nhan = QWidget()
            self.setup_ward_nhan_tab()
            self.tabs.addTab(self.tab_ward_nhan, "2. Lịch Sử Nhận Về (Từ KSNK)")
            
            self.tab_ward_req = QWidget()
            self.setup_ward_req_tab()
            self.tabs.addTab(self.tab_ward_req, "3. Yêu Cầu Lĩnh Bù")
            
            self.tab_patient = QWidget()
            self.setup_patient_tab()
            self.tabs.addTab(self.tab_patient, "4. Phát Đồ Bệnh Nhân")
            
            self.tab_ward_inv = QWidget()
            self.setup_ward_inv_tab()
            self.tabs.addTab(self.tab_ward_inv, "5. Tủ Trực Khoa")
            
        layout.addWidget(self.tabs)
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_all)
        self.timer.start(3000)

    def refresh_all(self):
        if self.role != "KHOA_LAM_SANG":
            self.load_multi_client()
        else:
            self.load_ward_send()
            self.load_ward_req()
            self.load_ward_inv()
            self.load_ward_nhan()

    # KSNK Tab
    def setup_multi_tab(self):
        layout = QVBoxLayout(self.tab_multi)
        
        # Sync bar
        sync_layout = QHBoxLayout()
        self.btn_sync = QPushButton(" Đồng bộ Google Form (Giao Nhận)")
        self.btn_sync.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 8px;")
        self.btn_sync.clicked.connect(self.sync_google_form)
        sync_layout.addWidget(self.btn_sync)
        sync_layout.addStretch()
        layout.addLayout(sync_layout)
        
        self.tree_multi = QTreeWidget()
        self.tree_multi.setHeaderLabels(["Khoa / Loại / Mã Đồ", "SL Dơ", "Tiếp Nhận", "Từ Chối"])
        self.tree_multi.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree_multi.setColumnWidth(1, 100)
        self.tree_multi.setColumnWidth(2, 200)
        self.tree_multi.setColumnWidth(3, 200)
        self.tree_multi.itemDoubleClicked.connect(self.show_receive_detail)
        layout.addWidget(self.tree_multi)

    def sync_google_form(self):
        import pandas as pd
        import urllib.request
        from io import StringIO
        from PySide6.QtWidgets import QMessageBox
        
        try:
            links = self.db.get_links()
            urls = [link['url'] for link in links if link['loai_link'] == 'Google Form Dong Bo']
            # Also support Vietnamese label stored
            if not urls:
                urls = [link['url'] for link in links if 'Form' in link.get('loai_link','') or 'form' in link.get('loai_link','')]
            
            if not urls:
                QMessageBox.warning(self, "Canh bao", "Chua co link Google Form nao.\nVao Cai dat -> Cau Hinh Links de them!")
                return
                
            self.btn_sync.setText("Dang dong bo...")
            self.btn_sync.setEnabled(False)
            
            # Date selected in format M/d/yyyy or d/M/yyyy - match against timestamp col
            sel_date = self.date_edit.date()
            sel_ymd = sel_date.toString("yyyy-MM-dd")
            # Google Sheet timestamps are like "9/9/2026 07:05:11"
            sel_m_d = f"{sel_date.month()}/{sel_date.day()}/{sel_date.year()}"
            target_time = sel_ymd + " 23:59:59"
            count = 0
            
            for url in urls:
                try:
                    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req) as response:
                        csv_data = response.read().decode('utf-8')
                    
                    # Read raw to find the correct header row
                    try:
                        df_raw = pd.read_csv(StringIO(csv_data), header=None, on_bad_lines='skip')
                    except TypeError:
                        df_raw = pd.read_csv(StringIO(csv_data), header=None, error_bad_lines=False)
                    header_row = None
                    
                    for i in range(len(df_raw)):
                        cell_col0 = str(df_raw.iloc[i, 0]).strip()
                        # Data rows have timestamps like "9/9/2026 07:05:11" or "07/03/2025"
                        if '/' in cell_col0 and len(cell_col0) > 5:
                            # Check if it looks like a date/timestamp
                            parts = cell_col0.split(' ')[0].split('/')
                            if len(parts) == 3:
                                try:
                                    int(parts[0]); int(parts[1]); int(parts[2])
                                    # First data row found - header is the row before
                                    header_row = i - 1
                                    break
                                except:
                                    pass
                    
                    if header_row is None or header_row < 0:
                        header_row = 10  # Fallback for this specific form
                    
                    try:
                        df = pd.read_csv(StringIO(csv_data), header=header_row, on_bad_lines='skip')
                    except TypeError:
                        df = pd.read_csv(StringIO(csv_data), header=header_row, error_bad_lines=False)
                    
                    # Column 0 = timestamp, Column 1 = khoa name
                    # Remaining columns = item names with quantities
                    # Skip columns that are purely Unnamed (no real name)
                    item_cols = [c for c in df.columns[2:] if not str(c).startswith('Unnamed')]
                    
                    SKIP_KHOA = {'nan', '', 'khoa phong', 'khoa', 'khoa phong', 'khoa ph\u00f2ng'}
                    
                    # Load mapping ONCE per URL (not per row)
                    mapping_rows = self.db.fetch_all(
                        "SELECT form_col, ma_do, loai FROM form_column_mapping WHERE ma_do IS NOT NULL"
                    )
                    mapping_dict = {r['form_col']: r for r in mapping_rows}
                    
                    # Detect timestamp format from first valid data row
                    # Form 1 (do vai): M/D/YYYY  e.g. "9/9/2026 07:05"
                    # Form 2 (dung cu): DD/MM/YYYY e.g. "07/03/2025"
                    fmt_detected = None
                    for _, sample_row in df.iterrows():
                        ts_sample = str(sample_row.iloc[0]).strip()
                        if '/' in ts_sample and len(ts_sample) > 5:
                            parts = ts_sample.split(' ')[0].split('/')
                            if len(parts) == 3:
                                try:
                                    p0, p1, p2 = int(parts[0]), int(parts[1]), int(parts[2])
                                    if p2 > 1000:  # year is last
                                        if p0 > 12:  # day > 12 means DD/MM/YYYY
                                            fmt_detected = 'dmy'
                                        elif p1 > 12:  # month > 12 means M/D/YYYY
                                            fmt_detected = 'mdy'
                                        else:
                                            # Ambiguous - check year position
                                            fmt_detected = 'mdy'  # Google Forms default
                                    elif p0 > 1000:  # year is first: YYYY/MM/DD
                                        fmt_detected = 'ymd'
                                    break
                                except:
                                    pass
                    
                    def parse_ts_to_ymd(ts_str):
                        date_part = ts_str.split(' ')[0]
                        parts = date_part.split('/')
                        if len(parts) != 3:
                            return None
                        try:
                            p0, p1, p2 = parts[0].strip(), parts[1].strip(), parts[2].strip()
                            if fmt_detected == 'dmy':  # DD/MM/YYYY
                                return f"{p2}-{p1.zfill(2)}-{p0.zfill(2)}"
                            elif fmt_detected == 'ymd':  # YYYY/MM/DD
                                return f"{p0}-{p1.zfill(2)}-{p2.zfill(2)}"
                            else:  # mdy = M/D/YYYY (default Google Forms)
                                return f"{p2}-{p0.zfill(2)}-{p1.zfill(2)}"
                        except:
                            return None
                    
                    for index, row in df.iterrows():
                        ts = str(row.iloc[0]).strip()
                        khoa_val = row.iloc[1]
                        if pd.isna(khoa_val):
                            continue
                        khoa = str(khoa_val).strip()
                        
                        # Skip non-data rows
                        if khoa.lower() in SKIP_KHOA or khoa == '':
                            continue
                        if not ts or ts.lower() == 'nan':
                            continue
                        
                        ts_ymd = parse_ts_to_ymd(ts)
                        if not ts_ymd:
                            continue
                        
                        if ts_ymd != sel_ymd:
                            continue
                            
                        # Extract real time instead of 23:59:59
                        from datetime import datetime
                        time_part = datetime.now().strftime("%H:%M:%S")
                        if ' ' in ts:
                            try:
                                t_str = ts.split(' ', 1)[1].strip()
                                parts = t_str.split(':')
                                if len(parts) == 2:
                                    time_part = f"{parts[0].zfill(2)}:{parts[1].zfill(2)}:00"
                                elif len(parts) >= 3:
                                    time_part = f"{parts[0].zfill(2)}:{parts[1].zfill(2)}:{parts[2][:2].zfill(2)}"
                            except: pass
                        
                        actual_time = f"{ts_ymd} {time_part}"
                        
                        # Insert one row per item that has quantity > 0
                        for col_name in item_cols:
                            val = row[col_name]
                            if pd.isna(val):
                                continue
                            try:
                                sl = int(float(str(val).replace(',', '.')))
                            except:
                                continue
                            if sl <= 0:
                                continue
                            
                            col_str = str(col_name).strip()
                            # Lookup mapping
                            mapped = mapping_dict.get(col_str)
                            if mapped:
                                ma_do = mapped['ma_do']
                                loai_ghi = mapped['loai'] or 'vai'
                            else:
                                ma_do = col_str[:100]
                                loai_ghi = 'khac'
                            
                            self.db.execute(
                                "INSERT INTO lich_su_giao_nhan (khoa_giao, ma_do, so_luong, thoi_gian, trang_thai) VALUES (%s, %s, %s, %s, %s)",
                                (khoa[:100], ma_do, sl, actual_time, 'CHO_TIEP_NHAN')
                            )
                            count += 1
                except Exception as e2:
                    print("Loi sync url:", e2)
            
            QMessageBox.information(self, "Dong bo", f"Tao thanh cong {count} dong giao nhan (ngay {sel_ymd}) tu Google Form.\nVui long duyet ben duoi.")
            self.load_multi_client()
        except Exception as e:
            QMessageBox.warning(self, "Loi dong bo", f"Khong the lay du lieu:\n{str(e)}")
        finally:
            self.btn_sync.setText(" Dong bo Google Form (Giao Nhan)")
            self.btn_sync.setEnabled(True)

    def load_multi_client(self):
        try:
            # Lưu lại vị trí thanh cuộn
            try:
                v_scroll_val = self.tree_multi.verticalScrollBar().value()
            except:
                v_scroll_val = 0

            reqs = self.db.get_pending_dirty_items()
            if reqs:
                max_id = max(r['id'] for r in reqs)
                if self.last_notified_id != -1 and max_id > self.last_notified_id:
                    import winsound
                    winsound.MessageBeep()
                self.last_notified_id = max_id
            
            # Fetch master data to classify items
            dict_vai = {r['ma_do_vai'] for r in self.db.fetch_all("SELECT ma_do_vai FROM danh_muc_do_vai")}
            dict_bo = {r['ma_bo'] for r in self.db.fetch_all("SELECT ma_bo FROM danh_muc_bo_dung_cu")}
            dict_le = {r['ma_dc'] for r in self.db.fetch_all("SELECT ma_dc FROM danh_muc_dung_cu")}
            
            # Group by Khoa -> Loại -> Items
            tree_data = {}
            for row in reqs:
                khoa_goc = row['khoa_giao']
                tg = row['thoi_gian']
                
                if hasattr(tg, 'strftime'):
                    tg_str = tg.strftime('%H:%M %d/%m')
                else:
                    tg_str = str(tg)[:16]
                    
                khoa = f"{khoa_goc} - {tg_str}"
                
                ma_do = row['ma_do']
                if ma_do in dict_vai: loai = "Đồ Vải"
                elif ma_do in dict_bo: loai = "Bộ Dụng Cụ"
                elif ma_do in dict_le: loai = "Dụng Cụ Lẻ"
                else: loai = "Khác"
                
                if khoa not in tree_data:
                    tree_data[khoa] = {}
                if loai not in tree_data[khoa]:
                    tree_data[khoa][loai] = []
                tree_data[khoa][loai].append(row)
                
            self.tree_multi.clear()
            
            for khoa, loai_dict in tree_data.items():
                # Collect all IDs in this khoa for batch receive
                all_ids_khoa = [row['id'] for items in loai_dict.values() for row in items]
                total_sl = sum(row['so_luong'] for items in loai_dict.values() for row in items)
                
                item_khoa = QTreeWidgetItem(self.tree_multi, [khoa, f"Tổng: {total_sl}", "", ""])
                item_khoa.setExpanded(True)
                
                # Nút "Nhận tất cả" ở level Khoa
                btn_receive_all = QPushButton(f"Nhận tất cả ({len(all_ids_khoa)} món)")
                btn_receive_all.setObjectName("PrimaryButton")
                btn_receive_all.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
                btn_receive_all.clicked.connect(lambda ch, ids=all_ids_khoa: self.receive_all_ids(ids))
                self.tree_multi.setItemWidget(item_khoa, 2, btn_receive_all)
                
                btn_rej_all = QPushButton("Từ chối tất cả")
                btn_rej_all.setObjectName("DangerButton")
                btn_rej_all.clicked.connect(lambda ch, ids=all_ids_khoa: self.reject_all_ids(ids))
                self.tree_multi.setItemWidget(item_khoa, 3, btn_rej_all)
                
                for loai, items in loai_dict.items():
                    ids_loai = [row['id'] for row in items]
                    sl_loai = sum(row['so_luong'] for row in items)
                    
                    item_loai = QTreeWidgetItem(item_khoa, [loai, f"{sl_loai}", "", ""])
                    item_loai.setExpanded(True)
                    
                    # Nút nhận cả loại
                    btn_recv_loai = QPushButton(f"Nhận cả {loai}")
                    btn_recv_loai.clicked.connect(lambda ch, ids=ids_loai: self.receive_all_ids(ids))
                    self.tree_multi.setItemWidget(item_loai, 2, btn_recv_loai)
                    
                    for row in items:
                        item_row = QTreeWidgetItem(item_loai, [f"[{row['id']}] {row['ma_do']}", str(row['so_luong']), "", ""])
                        item_row.setData(0, Qt.UserRole, row['id'])
                        
                        btn_acc = QPushButton("Nhận")
                        btn_acc.setObjectName("PrimaryButton")
                        btn_acc.clicked.connect(lambda ch, req_id=row['id']: self.receive_only(req_id))
                        self.tree_multi.setItemWidget(item_row, 2, btn_acc)
                        
                        btn_rej = QPushButton("Từ chối")
                        btn_rej.setObjectName("DangerButton")
                        btn_rej.clicked.connect(lambda ch, req_id=row['id']: self.reject_ticket(req_id))
                        self.tree_multi.setItemWidget(item_row, 3, btn_rej)
            
            # Phục hồi vị trí thanh cuộn
            try:
                self.tree_multi.verticalScrollBar().setValue(v_scroll_val)
            except:
                pass
        except Exception as e:
            print("Error load_multi_client:", e)

    def receive_all_ids(self, ids):
        from datetime import datetime
        now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        count_ok = 0
        count_skip = 0
        for req_id in ids:
            ma_phieu_str = f"PN_RECEIVE_{now_str}"
            ok = self.db.receive_dirty_items_only_advanced(req_id, ma_phieu=ma_phieu_str)
            if ok:
                count_ok += 1
            else:
                count_skip += 1
        msg = f"Đã tiếp nhận: {count_ok} phiếu."
        if count_skip > 0:
            msg += f"\n(Bỏ qua {count_skip} phiếu đã được máy khác nhận trước.)"
        QMessageBox.information(self, "Hoàn thành", msg)
        self.load_multi_client()

    def reject_all_ids(self, ids):
        reason, ok = QInputDialog.getText(self, "Tu choi", "Ly do tu choi:")
        if ok:
            for req_id in ids:
                self.db.reject_dirty_items(req_id, reason)
            self.load_multi_client()

    def receive_only(self, req_id):
        from datetime import datetime
        now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        ma_phieu_str = f"PN_RECEIVE_{now_str}"
        ok = self.db.receive_dirty_items_only_advanced(req_id, ma_phieu=ma_phieu_str)
        if ok:
            QMessageBox.information(self, "Thành công", "Đã tiếp nhận 1 món đồ!")
        else:
            QMessageBox.warning(self, "Đã được nhận", f"Phiếu #{req_id} đã được máy khác tiếp nhận rồi!")
        self.load_multi_client()
        
    def reject_ticket(self, req_id):
        reason, ok = QInputDialog.getText(self, "Từ chối", "Nhập lý do từ chối:")
        if ok and reason:
            self.db.reject_dirty_items(req_id, reason)
            self.load_multi_client()

    # Ward Tabs
    def setup_ward_send_tab(self):
        layout = QVBoxLayout(self.tab_ward_send)
        
        top_h = QHBoxLayout()
        if self.role != "KHOA_LAM_SANG":
            top_h.addWidget(QLabel("Khoa Giao:"))
            khoa_layout = QVBoxLayout()
            self.txt_ward_send_khoa = QLineEdit()
            self.txt_ward_send_khoa.setPlaceholderText("Gõ tên/mã khoa...")
            self.txt_ward_send_khoa.setMinimumWidth(200)
            
            self.list_ward_send_khoa = QListWidget()
            self.list_ward_send_khoa.hide()
            
            self.timer_ward_send_khoa = QTimer()
            self.timer_ward_send_khoa.setSingleShot(True)
            
            self.txt_ward_send_khoa.textEdited.connect(lambda t: self.timer_ward_send_khoa.start(500))
            self.timer_ward_send_khoa.timeout.connect(self.do_search_ward_send_khoa)
            self.list_ward_send_khoa.itemClicked.connect(self.select_ward_send_khoa)
            
            khoa_layout.addWidget(self.txt_ward_send_khoa)
            khoa_layout.addWidget(self.list_ward_send_khoa)
            top_h.addLayout(khoa_layout)
            
        btn_send = QPushButton("Tạo Phiếu Giao Nhận")
        btn_send.setObjectName("DangerButton")
        btn_send.clicked.connect(self.client_send_dirty)
        top_h.addWidget(btn_send)
        top_h.addStretch()
        
        layout.addLayout(top_h)
        
        self.table_ward_send = QTableWidget(0, 5)
        self.table_ward_send.setHorizontalHeaderLabels(["ID", "Thời Gian", "Mã Đồ", "SL Dơ", "Tình Trạng KSNK"])
        self.table_ward_send.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        layout.addWidget(self.table_ward_send)
        
    def client_send_dirty(self):
        dlg = MultiItemDialog(self, "Tạo Phiếu Giao Nhận (Nhiều Món)", list_type="do_vai")
        if dlg.exec():
            from datetime import datetime
            now = datetime.now()
            target_date = self.date_edit.date().toString("yyyy-MM-dd")
            if target_date == now.strftime("%Y-%m-%d"):
                target_time = now.strftime("%Y-%m-%d %H:%M:%S")
            else:
                target_time = f"{target_date} {now.strftime('%H:%M:%S')}"
                
            target_khoa = self.khoa
            trang_thai_phieu = 'CHO_TIEP_NHAN'
            if self.role != "KHOA_LAM_SANG":
                trang_thai_phieu = 'DANG_GIAT'
                if hasattr(self, 'txt_ward_send_khoa'):
                    target_khoa = self.txt_ward_send_khoa.text().strip()
                    if not target_khoa:
                        QMessageBox.warning(self, "Lỗi", "Vui lòng chọn hoặc nhập tên Khoa!")
                        return
                        
            ma_phieu_str = f"PN_{target_khoa}_{now.strftime('%Y%m%d_%H%M%S')}"
            
            for ma, sl in dlg.items_to_submit:
                self.db.send_dirty_items(target_khoa, ma, sl, thoi_gian=target_time, trang_thai=trang_thai_phieu, ma_phieu=ma_phieu_str)
            QMessageBox.information(self, "Thành công", f"Đã gửi {len(dlg.items_to_submit)} món xuống KSNK!")
            self.load_ward_send()


    def show_receive_detail(self, item, column):
        # Determine if it's a leaf node
        req_id = item.data(0, Qt.UserRole)
        if not req_id: return # Not a leaf node
        
        # We need to fetch details for this req_id
        try:
            row = self.db.fetch_all(f"SELECT * FROM lich_su_giao_nhan WHERE id={req_id}")
            if row:
                row = row[0]
                msg = "Chi tiết Phiếu Giao Nhận:\n\n"
                msg += f"ID: {row['id']}\n"
                msg += f"Khoa/Thời Gian: {row['khoa_giao']} - {row['thoi_gian']}\n"
                msg += f"Mã/Tên Đồ: {row['ma_do']}\n"
                msg += f"Số Lượng: {row['so_luong']}\n"
                msg += f"Tình Trạng: {row['trang_thai']}\n"
                QMessageBox.information(self, "Chi Tiết Phiếu", msg)
        except: pass

    def load_ward_send(self):
        try:
            reqs = self.db.get_phieu_gui_cua_khoa(self.khoa)
            self.table_ward_send.setRowCount(len(reqs))
            for r, row in enumerate(reqs):
                self.table_ward_send.setItem(r, 0, QTableWidgetItem(str(row['id'])))
                self.table_ward_send.setItem(r, 1, QTableWidgetItem(str(row['thoi_gian'])))
                self.table_ward_send.setItem(r, 2, QTableWidgetItem(row['ma_do']))
                self.table_ward_send.setItem(r, 3, QTableWidgetItem(str(row['so_luong'])))
                
                tt = row['trang_thai']
                if tt == 'CHO_TIEP_NHAN': text_tt = "Chờ KSNK nhận"
                elif tt == 'TU_CHOI': text_tt = "❌ Bị từ chối"
                elif tt == 'DANG_GIAT': text_tt = "Đang giặt"
                elif tt == 'CHO_CAP_PHAT': text_tt = "Sạch (chờ cấp phát)"
                else: text_tt = tt
                self.table_ward_send.setItem(r, 4, QTableWidgetItem(text_tt))
        except: pass

    def setup_ward_nhan_tab(self):
        layout = QVBoxLayout(self.tab_ward_nhan)
        self.table_ward_nhan = QTableWidget(0, 4)
        self.table_ward_nhan.setHorizontalHeaderLabels(["ID Phiếu", "Thời Gian", "Mã Đồ Nhận Về", "Số Lượng Sạch"])
        self.table_ward_nhan.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        layout.addWidget(self.table_ward_nhan)

    def load_ward_nhan(self):
        try:
            reqs = self.db.fetch_all("SELECT * FROM phieu_cap_phat WHERE khoa_nhan=%s ORDER BY thoi_gian DESC", (self.khoa,))
            self.table_ward_nhan.setRowCount(len(reqs))
            for r, row in enumerate(reqs):
                self.table_ward_nhan.setItem(r, 0, QTableWidgetItem(str(row['id'])))
                self.table_ward_nhan.setItem(r, 1, QTableWidgetItem(str(row['thoi_gian'])))
                self.table_ward_nhan.setItem(r, 2, QTableWidgetItem(row['ma_do']))
                self.table_ward_nhan.setItem(r, 3, QTableWidgetItem(str(row['so_luong'])))
        except: pass

    def setup_ward_req_tab(self):
        layout = QVBoxLayout(self.tab_ward_req)
        btn_req = QPushButton("Tạo Phiếu Lĩnh Bù")
        btn_req.clicked.connect(self.req_linh_bu)
        layout.addWidget(btn_req)
        
        self.table_ward_lb = QTableWidget(0, 3)
        self.table_ward_lb.setHorizontalHeaderLabels(["ID", "Mã ĐV", "SL Yêu Cầu"])
        self.table_ward_lb.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        layout.addWidget(self.table_ward_lb)
        
    def req_linh_bu(self):
        ma_dv, ok1 = get_autocomplete_input(self, "Lĩnh Bù", "Mã Đồ Vải:", "do_vai")
        if ok1:
            sl, ok2 = QInputDialog.getInt(self, "Lĩnh Bù", "Số lượng cần bù:")
            if ok2:
                self.db.request_linh_bu(self.khoa, ma_dv, sl)
                self.load_ward_req()

    def load_ward_req(self):
        try:
            reqs = self.db.fetch_all("SELECT * FROM phieu_linh_bu WHERE khoa_gui=%s", (self.khoa,))
            self.table_ward_lb.setRowCount(len(reqs))
            for r, row in enumerate(reqs):
                self.table_ward_lb.setItem(r, 0, QTableWidgetItem(str(row['id'])))
                self.table_ward_lb.setItem(r, 1, QTableWidgetItem(row['ma_do_vai']))
                self.table_ward_lb.setItem(r, 2, QTableWidgetItem(str(row['so_luong'])))
        except: pass

    def setup_patient_tab(self):
        layout = QVBoxLayout(self.tab_patient)
        btn_phat = QPushButton("➕ Tạo Phiếu Phát Đồ Cho Bệnh Nhân")
        btn_phat.setObjectName("PrimaryButton")
        btn_phat.clicked.connect(self.phat_do)
        layout.addWidget(btn_phat)
        layout.addStretch()
        
    def phat_do(self):
        ma_bn, ok1 = QInputDialog.getText(self, "Mã BN", "Nhập mã Bệnh Nhân / Số Giường:")
        if ok1 and ma_bn:
            ma_do, ok2 = get_autocomplete_input(self, "Mã Đồ", "Chọn mã đồ vải:", "do_vai")
            if ok2 and ma_do:
                sl, ok3 = QInputDialog.getInt(self, "Số lượng", "Nhập số lượng giao:", 1, 1, 100)
                if ok3:
                    self.db.phat_do_benh_nhan(self.khoa, ma_bn, ma_do, sl)
                    self.db.execute("UPDATE tu_truc_khoa SET so_luong = so_luong - %s, dang_su_dung = dang_su_dung + %s WHERE khoa=%s AND ma_do=%s", (sl, sl, self.khoa, ma_do))
                    QMessageBox.information(self, "OK", f"Đã phát {sl} {ma_do} cho BN {ma_bn}.")

    def setup_ward_inv_tab(self):
        layout = QVBoxLayout(self.tab_ward_inv)
        self.table_ward_inv = QTableWidget(0, 2)
        self.table_ward_inv.setHorizontalHeaderLabels(["Mã Đồ", "Số Lượng (Tủ Trực)"])
        self.table_ward_inv.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        layout.addWidget(self.table_ward_inv)

    def load_ward_inv(self):
        try:
            reqs = self.db.get_tu_truc_khoa(self.khoa)
            self.table_ward_inv.setRowCount(len(reqs))
            for r, row in enumerate(reqs):
                self.table_ward_inv.setItem(r, 0, QTableWidgetItem(row['ma_do']))
                self.table_ward_inv.setItem(r, 1, QTableWidgetItem(str(row['so_luong'])))
        except: pass



    def do_search_ward_send_khoa(self):
        text = remove_vietnamese_accents(self.txt_ward_send_khoa.text().strip())
        self.list_ward_send_khoa.clear()
        if not text:
            self.list_ward_send_khoa.hide()
            return
        try:
            res = self.db.fetch_all("SELECT ten_khoa FROM danh_muc_khoa")
            for r in res:
                if text.lower() in remove_vietnamese_accents(r['ten_khoa']).lower():
                    self.list_ward_send_khoa.addItem(r['ten_khoa'])
            if self.list_ward_send_khoa.count() > 0:
                self.list_ward_send_khoa.show()
            else:
                self.list_ward_send_khoa.hide()
        except:
            pass

    def select_ward_send_khoa(self, item):
        self.txt_ward_send_khoa.setText(item.text())
        self.list_ward_send_khoa.hide()

class IssuePage(QWidget):
    def __init__(self, user_data=None):
        super().__init__()
        self.user_data = user_data or {"role": "ADMIN", "khoa_id": "Unknown", "full_name": "Admin"}
        self.role = self.user_data.get('role', 'ADMIN')
        self.khoa = self.user_data.get('khoa_id', 'Unknown')
        
        self.db = DBManager()
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        
        if self.role != "KHOA_LAM_SANG":
            self.tab_laundry = QWidget()
            self.setup_laundry_tab()
            self.tabs.addTab(self.tab_laundry, "B2. Giặt Là")
            
            self.tab_issue = QWidget()
            self.setup_issue_tab()
            self.tabs.addTab(self.tab_issue, "B3. Cấp Phát (Xuất Phiếu)")
            
            self.tab_linh_bu = QWidget()
            self.setup_linh_bu_tab_ksnk()
            self.tabs.addTab(self.tab_linh_bu, "Duyệt Lĩnh Bù")
            
            layout.addWidget(self.tabs)
            self.timer = QTimer()
            self.timer.timeout.connect(self.refresh_all)
            self.timer.start(3000)

    def refresh_all(self):
        if self.role != "KHOA_LAM_SANG":
            self.load_laundry()
            self.load_issue()
            self.load_linh_bu_ksnk()

    def setup_laundry_tab(self):
        layout = QVBoxLayout(self.tab_laundry)
        self.table_laundry = QTableWidget(0, 5)
        self.table_laundry.setHorizontalHeaderLabels(["ID", "Khoa Gửi", "Mã Đồ", "SL", "Hành Động"])
        self.table_laundry.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        layout.addWidget(self.table_laundry)

    def load_laundry(self):
        try:
            reqs = self.db.get_laundry_items()
            self.table_laundry.setRowCount(len(reqs))
            for r, row in enumerate(reqs):
                self.table_laundry.setItem(r, 0, QTableWidgetItem(str(row['id'])))
                self.table_laundry.setItem(r, 1, QTableWidgetItem(row['khoa_giao']))
                self.table_laundry.setItem(r, 2, QTableWidgetItem(row['ma_do']))
                self.table_laundry.setItem(r, 3, QTableWidgetItem(str(row['so_luong'])))
                
                btn_done = QPushButton("✅ Hoàn Tất Giặt (Cộng Kho Sạch)")
                btn_done.setObjectName("SuccessButton")
                btn_done.clicked.connect(lambda ch, req_id=row['id'], ma=row['ma_do'], sl=row['so_luong']: self.finish_laundry(req_id, ma, sl))
                self.table_laundry.setCellWidget(r, 4, btn_done)
        except Exception: pass

    def finish_laundry(self, req_id, ma, sl):
        self.db.complete_laundry(req_id, ma, sl)
        self.load_laundry()

    def setup_issue_tab(self):
        layout = QVBoxLayout(self.tab_issue)
        hl = QHBoxLayout()
        
        if self.role != "KHOA_LAM_SANG":
            hl.addWidget(QLabel("Khoa Nhận:"))
            khoa_layout = QVBoxLayout()
            self.txt_issue_khoa = QLineEdit()
            self.txt_issue_khoa.setPlaceholderText("Gõ tên/mã khoa...")
            self.txt_issue_khoa.setMinimumWidth(200)
            
            self.list_issue_khoa = QListWidget()
            self.list_issue_khoa.hide()
            
            self.timer_issue_khoa = QTimer()
            self.timer_issue_khoa.setSingleShot(True)
            
            self.txt_issue_khoa.textEdited.connect(lambda t: self.timer_issue_khoa.start(500))
            self.timer_issue_khoa.timeout.connect(self.do_search_issue_khoa)
            self.list_issue_khoa.itemClicked.connect(self.select_issue_khoa)
            
            khoa_layout.addWidget(self.txt_issue_khoa)
            khoa_layout.addWidget(self.list_issue_khoa)
            hl.addLayout(khoa_layout)
            
        btn_issue = QPushButton("Tạo Phiếu Cấp Phát")
        btn_issue.setObjectName("PrimaryButton")
        btn_issue.clicked.connect(self.create_issue)
        hl.addWidget(btn_issue)
        
        btn_export = QPushButton("📥 Xuất Bảng Cấp Phát (Excel)")
        btn_export.setObjectName("SuccessButton")
        btn_export.clicked.connect(self.export_issue_csv)
        hl.addWidget(btn_export)
        
        hl.addStretch()
        layout.addLayout(hl)
        
        self.table_issue = QTableWidget(0, 5)
        self.table_issue.setHorizontalHeaderLabels(["ID Phiếu", "Thời Gian", "Khoa Nhận", "Mã Đồ", "Số Lượng"])
        self.table_issue.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        layout.addWidget(self.table_issue)

    def create_issue(self):
        if hasattr(self, 'txt_issue_khoa'):
            khoa = self.txt_issue_khoa.text().strip()
            if not khoa:
                QMessageBox.warning(self, "Lỗi", "Vui lòng chọn hoặc nhập tên Khoa!")
                return
        else:
            khoa, ok0 = get_autocomplete_input(self, "Cấp Phát", "Chọn khoa nhận:", "khoa")
            if not ok0 or not khoa: return
        
        dlg = MultiItemDialog(self, f"Tạo Phiếu Cấp Phát cho {khoa}", list_type="do_vai", target_khoa=khoa)
        pending = self.db.get_pending_issue_items(khoa)
        if pending:
            dlg.prefill_cart(pending)
            
        if dlg.exec():
            target_time = self.date_edit.date().toString("yyyy-MM-dd") + " 23:59:59"
            for ma_do, sl in dlg.items_to_submit:
                self.db.tao_phieu_cap_phat(khoa, ma_do, sl, thoi_gian=target_time)
                self.db.execute('''INSERT INTO tu_truc_khoa (khoa, ma_do, so_luong) VALUES (%s, %s, %s) 
                                   ON DUPLICATE KEY UPDATE so_luong = so_luong + %s''', (khoa, ma_do, sl, sl))
            QMessageBox.information(self, "OK", f"Đã tạo phiếu cấp phát gồm {len(dlg.items_to_submit)} món cho {khoa}.")
            self.load_issue()


    def show_issue_detail(self, item):
        row = item.row()
        table = item.tableWidget()
        msg = "Chi tiết Phiếu Cấp Phát:\n\n"
        try:
            msg += f"Thời Gian: {table.item(row, 0).text()}\n"
            msg += f"Khoa Nhận: {table.item(row, 1).text()}\n"
            msg += f"Mã Đồ: {table.item(row, 2).text()}\n"
            msg += f"Số Lượng: {table.item(row, 3).text()}\n"
        except: pass
        QMessageBox.information(self, "Chi Tiết Phiếu", msg)

    def load_issue(self):
        try:
            reqs = self.db.get_phieu_cap_phat()
            self.table_issue.setRowCount(len(reqs))
            for r, row in enumerate(reqs):
                self.table_issue.setItem(r, 0, QTableWidgetItem(str(row['id'])))
                self.table_issue.setItem(r, 1, QTableWidgetItem(str(row['thoi_gian'])))
                self.table_issue.setItem(r, 2, QTableWidgetItem(row['khoa_nhan']))
                self.table_issue.setItem(r, 3, QTableWidgetItem(row['ma_do']))
                self.table_issue.setItem(r, 4, QTableWidgetItem(str(row['so_luong'])))
        except Exception: pass

    def export_issue_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Lưu danh sách cấp phát", "", "CSV Files (*.csv)")
        if path:
            try:
                with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    headers = [self.table_issue.horizontalHeaderItem(i).text() for i in range(self.table_issue.columnCount())]
                    writer.writerow(headers)
                    for row in range(self.table_issue.rowCount()):
                        row_data = [self.table_issue.item(row, col).text() if self.table_issue.item(row, col) else "" for col in range(self.table_issue.columnCount())]
                        writer.writerow(row_data)
                QMessageBox.information(self, "Thành công", f"Đã lưu bảng cấp phát ra Excel:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", str(e))

    def setup_linh_bu_tab_ksnk(self):
        layout = QVBoxLayout(self.tab_linh_bu)
        self.table_lb = QTableWidget(0, 4)
        self.table_lb.setHorizontalHeaderLabels(["ID", "Khoa Yêu Cầu", "Mã ĐV", "SL Bù"])
        layout.addWidget(self.table_lb)
        
        btn_approve = QPushButton("✅ Duyệt Lĩnh Bù (Hàng Đang Chọn)")
        btn_approve.setObjectName("SuccessButton")
        btn_approve.clicked.connect(self.approve_lb)
        layout.addWidget(btn_approve)

    def load_linh_bu_ksnk(self):
        try:
            reqs = self.db.get_linh_bu()
            self.table_lb.setRowCount(len(reqs))
            for r, row in enumerate(reqs):
                self.table_lb.setItem(r, 0, QTableWidgetItem(str(row['id'])))
                self.table_lb.setItem(r, 1, QTableWidgetItem(row['khoa_gui']))
                self.table_lb.setItem(r, 2, QTableWidgetItem(row['ma_do_vai']))
                self.table_lb.setItem(r, 3, QTableWidgetItem(str(row['so_luong'])))
        except: pass

    def approve_lb(self):
        row = self.table_lb.currentRow()
        if row >= 0:
            r_id = self.table_lb.item(row, 0).text()
            khoa = self.table_lb.item(row, 1).text()
            ma_dv = self.table_lb.item(row, 2).text()
            sl = int(self.table_lb.item(row, 3).text())
            
            original = self.db.fetch_one("SELECT so_luong FROM phieu_linh_bu WHERE id=%s", (r_id,))
            if not original: return
            
            if sl < original['so_luong']:
                reply = QMessageBox.question(self, "Thiếu đồ", f"Khoa yêu cầu {original['so_luong']} nhưng bạn chỉ duyệt {sl}. Bạn có muốn tạo phiếu NỢ (Backorder) cho {original['so_luong'] - sl} món còn thiếu không?", QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.Yes:
                    self.db.execute("INSERT INTO phieu_linh_bu (khoa_gui, ma_do_vai, so_luong, trang_thai) VALUES (%s, %s, %s, %s)", (khoa, ma_dv, original['so_luong'] - sl, 'CHO_DUYET'))
                    
            self.db.approve_linh_bu(r_id, ma_dv, sl)
            self.db.execute('''INSERT INTO tu_truc_khoa (khoa, ma_do, so_luong) VALUES (%s, %s, %s) 
                               ON DUPLICATE KEY UPDATE so_luong = so_luong + %s''', (khoa, ma_dv, sl, sl))
            QMessageBox.information(self, "OK", "Đã duyệt và chuyển đồ vào Tủ trực khoa!")
            self.load_linh_bu_ksnk()




    def do_search_issue_khoa(self):
        text = remove_vietnamese_accents(self.txt_issue_khoa.text().strip())
        self.list_issue_khoa.clear()
        if not text:
            self.list_issue_khoa.hide()
            return
        try:
            res = self.db.fetch_all("SELECT ten_khoa FROM danh_muc_khoa")
            for r in res:
                if text.lower() in remove_vietnamese_accents(r['ten_khoa']).lower():
                    self.list_issue_khoa.addItem(r['ten_khoa'])
            if self.list_issue_khoa.count() > 0:
                self.list_issue_khoa.show()
            else:
                self.list_issue_khoa.hide()
        except:
            pass

    def select_issue_khoa(self, item):
        self.txt_issue_khoa.setText(item.text())
        self.list_issue_khoa.hide()
