from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtWidgets import QMessageBox, QInputDialog
from datetime import datetime, timedelta
import json
from models.db_manager import DBManager

class SterilizationController(QObject):
    def __init__(self, view, user_data):
        super().__init__()
        self.view = view
        self.user_data = user_data
        self.db = DBManager()
        
        self.machines = []
        
        # Connect View Signals
        self.view.signal_load_history.connect(self.load_history)
        self.view.signal_poll.connect(self.poll_db)
        self.view.signal_cancel.connect(self.cancel_machine)
        self.view.signal_start.connect(self.start_machine)
        self.view.signal_end.connect(self.end_machine)
        self.view.signal_load_items.connect(self.load_items_into_machine)
        
        # Give view access to DB for fetching ma_phieu in dialog (or we can pass it)
        self.view.set_db(self.db)
        self.view.fetch_session_items_callback = self.get_session_items
        self.view.fetch_pending_sessions_callback = self.get_pending_sessions
        
        self.poll_db()
        self.load_history()

    
    def get_pending_sessions(self):
        # CHỈ TÌM CÁC PHIẾU ĐÃ KHỬ NHIỄM
        query = "SELECT DISTINCT khoa_giao, ma_phieu FROM lich_su_giao_nhan WHERE trang_thai IN ('DA_KHU_NHIEM', 'DA_DONG_GOI')"
        sessions = self.db.fetch_all(query)
        result = []
        if sessions:
            for s in sessions:
                k = s['khoa_giao']
                mp = s['ma_phieu']
                display = f"Mã phiên: {mp}" if mp else f"{k} (Không mã)"
                result.append({"khoa": k, "ma_phieu": mp, "display": display})
        return result

    def get_session_items(self, khoa, ma_phieu):
        query = "SELECT * FROM lich_su_giao_nhan WHERE ma_phieu=%s AND trang_thai IN ('DA_KHU_NHIEM', 'DA_DONG_GOI')"
        items = self.db.fetch_all(query, (ma_phieu,))
        
        groups = {}
        if not items: return groups
        for it in items:
            loai = it.get('loai_do')
            ma = it.get('ma_do')
            sl = it.get('so_luong', 1)
            req_id = it.get('id')
            khoa_giao = it.get('khoa_giao', khoa)
            ten = ma
            is_digit = str(ma).isdigit()
            
            if loai == 'Bộ Dụng Cụ' or (not loai and is_digit):
                q1 = "SELECT ten_bo FROM danh_muc_bo_dung_cu WHERE ma_bo=%s" + (" OR id=%s" if is_digit else "")
                p1 = (ma, ma) if is_digit else (ma,)
                b = self.db.fetch_one(q1, p1)
                if b: ten = b['ten_bo']
            elif loai == 'Đồ Vải' or (not loai and is_digit):
                q2 = "SELECT ten_do_vai FROM danh_muc_do_vai WHERE ma_do_vai=%s" + (" OR id=%s" if is_digit else "")
                p2 = (ma, ma) if is_digit else (ma,)
                v = self.db.fetch_one(q2, p2)
                if v: ten = v['ten_do_vai']
            
            if ten == ma:
                q3 = "SELECT ten_dc FROM danh_muc_dung_cu WHERE ma_dc=%s" + (" OR id=%s" if is_digit else "")
                p3 = (ma, ma) if is_digit else (ma,)
                d = self.db.fetch_one(q3, p3)
                if d: ten = d['ten_dc']
            
            if khoa_giao not in groups:
                groups[khoa_giao] = []
            groups[khoa_giao].append({"ma": ma, "ten": ten, "sl": sl, "req_id": req_id})
            
        return groups

    def poll_db(self):
        try:
            res = self.db.fetch_all("SELECT * FROM machines WHERE group_id=3")
            if res:
                self.machines = res
                self.view.render_table(self.machines)
        except Exception as e:
            print("Poll DB error:", e)

    def load_history(self):
        dt = self.view.dt_history.date().toString("yyyy-MM-dd")
        try:
            rows = self.db.fetch_all("SELECT r.*, m.name as m_name FROM runs r JOIN machines m ON r.machine_id = m.id WHERE r.date=%s ORDER BY r.time DESC", (dt,))
            self.view.update_history_table(rows if rows else [])
        except:
            pass

    def cancel_machine(self, mac):
        try:
            items_json = mac.get('loaded_items_json')
            if items_json:
                items = json.loads(items_json)
                for it in items:
                    req_id = it.get('req_id')
                    if req_id:
                        self.db.execute("UPDATE lich_su_giao_nhan SET trang_thai IN ('DA_KHU_NHIEM', 'DA_DONG_GOI') WHERE id=%s", (req_id,))
                        
            self.db.execute("UPDATE machines SET status='READY', end_time=NULL, loaded_items_json=NULL, current_cycle_id=NULL WHERE id=%s", (mac['id'],))
            now = datetime.now()
            self.db.execute("INSERT INTO runs (machine_id, date, time, cycle_type_id, status, note) VALUES (%s, %s, %s, %s, %s, %s)",
                            (mac['id'], now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"), mac.get('current_cycle_id'), "CANCELLED", "Người dùng bấm Hủy"))
            payload = json.dumps({"action": "CANCEL", "machine_id": mac['id']})
            self.db.execute("INSERT INTO sync_system (event_type, payload) VALUES (%s, %s)", ("STERILIZATION_SYNC", payload))
            self.poll_db()
            self.load_history()
        except Exception as e:
            QMessageBox.critical(self.view, "Lỗi", str(e))

    def start_machine(self, mac):
        try:
            cycles = self.db.fetch_all("SELECT c.id, c.name, c.thoi_gian FROM cycle_types c JOIN machine_cycle_types m ON c.id=m.cycle_type_id WHERE m.machine_id=%s", (mac['id'],))
            if not cycles:
                QMessageBox.warning(self.view, "Cảnh báo", f"Máy {mac['name']} chưa được gán chu trình nào. Vui lòng cấu hình ở phần Quản lý.")
                return
            
            cycle_names = [f"{c['name']} ({c['thoi_gian']} phút)" for c in cycles]
            chosen, ok = QInputDialog.getItem(self.view, "Chọn chu trình", "Chu trình tiệt khuẩn:", cycle_names, 0, False)
            if not ok or not chosen: return
            
            idx = cycle_names.index(chosen)
            selected_cycle = cycles[idx]
            
            is_test = any(kw in selected_cycle['name'].lower() for kw in ['test', 'bowie', 'leak'])
            if is_test and mac.get('loaded_items_json'):
                QMessageBox.warning(self.view, "Cảnh báo", "Chu trình Test không được phép chứa đồ. Vui lòng bấm Hủy hoặc dọn sạch máy trước khi chạy.")
                return
                
            if not is_test and not mac.get('loaded_items_json'):
                QMessageBox.warning(self.view, "Cảnh báo", "Chu trình này yêu cầu phải nạp đồ trước khi chạy. Vui lòng bấm Xếp đồ.")
                return
            
            cycle_mins = int(selected_cycle.get('thoi_gian', 60))
            end_time = datetime.now() + timedelta(minutes=cycle_mins)
            
            self.db.execute("UPDATE machines SET status='RUNNING', end_time=%s, current_cycle_id=%s WHERE id=%s", (end_time, selected_cycle['id'], mac['id']))
            
            payload = json.dumps({"action": "START", "machine_id": mac['id']})
            self.db.execute("INSERT INTO sync_system (event_type, payload) VALUES (%s, %s)", ("STERILIZATION_SYNC", payload))
            
            # Update sets status that are WAITING_STERILIZATION? 
            # In our system we just track everything as STERILIZING.
            sets = self.db.get_tracked_sets()
            for s in sets:
                if s['trang_thai'] == "ASSEMBLED (Đã đóng gói)":
                    self.db.track_set_status(s['ma_bo'], s['ten_bo'], s['khoa_gui'], f"STERILIZING ({mac['name']})")
                    
            self.poll_db()
        except Exception as e:
            QMessageBox.critical(self.view, "Lỗi", str(e))

    def end_machine(self, mac, result_status, test_note=""):
        trang_thai_moi = "CHO_CAP_PHAT" if result_status == "PASS" else "LOI_TIET_KHUAN"
        nv_thuc_hien = getattr(self, 'user_data', {}).get('full_name', 'KSNK')
        
        try:
            status = "STERILE (Pass)" if result_status == "PASS" else "FAIL (Lỗi Hấp)"
            sets = self.db.get_tracked_sets()
            for s in sets:
                if f"STERILIZING ({mac['name']})" in s['trang_thai']:
                    self.db.track_set_status(s['ma_bo'], s['ten_bo'], s['khoa_gui'], status)
            
            items_json = mac.get('loaded_items_json')
            if items_json:
                items = json.loads(items_json)
                for it in items:
                    req_id = it.get('req_id')
                    sl = it.get('so_luong', 0)
                    ma_sp = it.get('ma_san_pham')
                    
                    if req_id:
                        self.db.execute("UPDATE lich_su_giao_nhan SET trang_thai=%s WHERE id=%s", (trang_thai_moi, req_id))
                        ghi_chu_log = f"Xuất lò {mac['name']} - KQ: {result_status}. {test_note}"
                        self.db.execute("INSERT INTO lich_su_bien_dong (thoi_gian, nguoi_thuc_hien, bang_du_lieu, ma_item, noi_dung) VALUES (NOW(), %s, %s, %s, %s)", 
                           (nv_thuc_hien, 'lich_su_giao_nhan', req_id, ghi_chu_log))
                        if result_status == "PASS" and ma_sp:
                            self.db.execute("UPDATE danh_muc_do_vai SET cssd_ton_thuc_te = cssd_ton_thuc_te + %s WHERE ma_do_vai=%s", (sl, ma_sp))
            
            self.db.execute("UPDATE machines SET status='READY', end_time=NULL, loaded_items_json=NULL, current_cycle_id=NULL WHERE id=%s", (mac['id'],))
            now = datetime.now()
            self.db.execute("INSERT INTO runs (machine_id, date, time, cycle_type_id, status, note) VALUES (%s, %s, %s, %s, %s, %s)",
                            (mac['id'], now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"), mac.get('current_cycle_id'), result_status, test_note))
            
            payload = json.dumps({"action": "END", "machine_id": mac['id']})
            self.db.execute("INSERT INTO sync_system (event_type, payload) VALUES (%s, %s)", ("STERILIZATION_SYNC", payload))
            
            self.poll_db()
            self.load_history()
            QMessageBox.information(self.view, "Hoàn tất", f"Đã xuất mẻ lò {mac['name']} với kết quả: {result_status}")
        except Exception as e:
            QMessageBox.critical(self.view, "Lỗi", str(e))

    def load_items_into_machine(self, mac, items_list):
        if not items_list: return
        nv_thuc_hien = getattr(self, 'user_data', {}).get('full_name', 'KSNK')
        try:
            for it in items_list:
                req_id = it.get('req_id')
                sl_chon = it.get('so_luong_chon', it.get('so_luong'))
                
                # Cleanup reference để có thể parse JSON lưu vào DB
                if 'spinbox_ref' in it: del it['spinbox_ref']
                if 'so_luong_chon' in it: del it['so_luong_chon']
                
                # Sửa số lượng của JSON bằng đúng số lượng đưa vào máy
                it['so_luong'] = sl_chon 
                
                if req_id:
                    req = self.db.fetch_one("SELECT * FROM lich_su_giao_nhan WHERE id=%s", (req_id,))
                    if req:
                        sl_goc = int(req['so_luong'])
                        if sl_chon < sl_goc:
                            sl_con_lai = sl_goc - sl_chon
                            # Tạo bản sao giữ lại số dư chờ ở ngoài
                            self.db.execute("""INSERT INTO lich_su_giao_nhan 
                                (khoa_giao, ma_do, so_luong, trang_thai, thoi_gian, ma_phieu) 
                                VALUES (%s, %s, %s, %s, %s, %s, %s)""", 
                                (req['khoa_giao'], req['ma_do'], sl_con_lai, req['trang_thai'], req['thoi_gian'], req['ma_phieu']))
                            # Khóa phiếu hiện tại
                            self.db.execute("UPDATE lich_su_giao_nhan SET so_luong=%s, trang_thai='DANG_TIET_KHUAN' WHERE id=%s", (sl_chon, req_id))
                        else:
                            self.db.execute("UPDATE lich_su_giao_nhan SET trang_thai='DANG_TIET_KHUAN' WHERE id=%s", (req_id,))
                            
                        self.db.execute("INSERT INTO lich_su_bien_dong (thoi_gian, nguoi_thuc_hien, bang_du_lieu, ma_item, noi_dung) VALUES (NOW(), %s, %s, %s, %s)", 
                               (nv_thuc_hien, 'lich_su_giao_nhan', req_id, f"Xếp vào lò {mac['name']} - SL: {sl_chon}"))
            
            # Ghi trạng thái JSON lồng máy
            json_str = json.dumps(items_list)
            self.db.execute("UPDATE machines SET loaded_items_json=%s WHERE id=%s", (json_str, mac['id']))
            self.poll_db()
            QMessageBox.information(self.view, "Thành công", f"Đã nạp {len(items_list)} mã đồ vào {mac['name']}.")
            
        except Exception as e:
            QMessageBox.critical(self.view, "Lỗi", str(e))
