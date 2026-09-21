import pymysql
import logging

class DBManager:
    def __init__(self, host="127.0.0.1", user="root", password="", database="bvdk_ducgiang"):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        self.setup_tracking_table()

    def connect(self):
        try:
            self.connection = pymysql.connect(
                host=self.host, user=self.user, password=self.password,
                database=self.database, cursorclass=pymysql.cursors.DictCursor
            )
            return True
        except Exception as e:
            logging.error(f"Database connection error: {e}")
            return False

    def close(self):
        if self.connection and self.connection.open:
            self.connection.close()

    def fetch_all(self, query, params=None):
        if not self.connect(): return []
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        except: return []

    def fetch_one(self, query, params=None):
        if not self.connect(): return None
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchone()
        except: return None

    def execute(self, query, params=None):
        if not self.connect(): return False
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
            self.connection.commit()
            return True
        except:
            if self.connection: self.connection.rollback()
            return False

    def execute_rowcount(self, query, params=None):
        """Thực thi query và trả về số rows bị ảnh hưởng.
        Dùng cho optimistic locking: nếu rowcount == 0 nghĩa là record đã bị client khác thay đổi."""
        if not self.connect(): return 0
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.rowcount
            self.connection.commit()
            return rows
        except:
            if self.connection: self.connection.rollback()
            return 0

    def authenticate(self, username, password):
        return self.fetch_one("SELECT * FROM employees WHERE username = %s AND password_hash = %s", (username, password))

    def register_user(self, username, password, full_name, khoa_id, is_ksnk=False):
        role = "NV_KSNK" if is_ksnk else "KHOA_LAM_SANG"
        return self.execute("INSERT INTO employees (username, password_hash, full_name, role, khoa_id) VALUES (%s, %s, %s, %s, %s)",
                            (username, password, full_name, role, khoa_id))

    def get_danh_muc_khoa(self):
        return self.fetch_all("SELECT * FROM danh_muc_khoa")

    def get_chi_tiet_bo(self, ma_bo):
        return self.fetch_all('''SELECT c.ma_dc, d.ten_dc, c.so_luong 
                                 FROM chi_tiet_bo_dung_cu c JOIN danh_muc_dung_cu d ON c.ma_dc = d.ma_dc 
                                 WHERE c.ma_bo = %s''', (ma_bo,))

    def setup_tracking_table(self):
        query = '''
        CREATE TABLE IF NOT EXISTS spm_set_tracking (
            id INT AUTO_INCREMENT PRIMARY KEY,
            ma_bo VARCHAR(50),
            ten_bo VARCHAR(150),
            khoa_gui VARCHAR(100),
            trang_thai VARCHAR(50),
            cap_nhat_cuoi DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        '''
        self.execute(query)

    def track_set_status(self, ma_bo, ten_bo, khoa_gui, trang_thai):
        # Insert or Update the tracking record for testing
        exist = self.fetch_one("SELECT id FROM spm_set_tracking WHERE ma_bo=%s", (ma_bo,))
        if exist:
            return self.execute("UPDATE spm_set_tracking SET trang_thai=%s, khoa_gui=%s WHERE ma_bo=%s", (trang_thai, khoa_gui, ma_bo))
        else:
            return self.execute("INSERT INTO spm_set_tracking (ma_bo, ten_bo, khoa_gui, trang_thai) VALUES (%s, %s, %s, %s)", 
                                (ma_bo, ten_bo, khoa_gui, trang_thai))

    def get_tracked_sets(self):
        return self.fetch_all("SELECT * FROM spm_set_tracking ORDER BY cap_nhat_cuoi DESC")

    def setup_extended_tables(self):
        self.execute('''CREATE TABLE IF NOT EXISTS phieu_linh_bu (
            id INT AUTO_INCREMENT PRIMARY KEY,
            khoa_gui VARCHAR(100),
            ma_do_vai VARCHAR(50),
            so_luong INT,
            trang_thai VARCHAR(50) DEFAULT 'CHO_DUYET'
        )''')
        self.execute('''CREATE TABLE IF NOT EXISTS danh_muc_link (
            id INT AUTO_INCREMENT PRIMARY KEY,
            ten_link VARCHAR(255),
            url VARCHAR(1000),
            loai_link VARCHAR(50)
        )''')
        
    def request_linh_bu(self, khoa, ma_dv, sl):
        return self.execute("INSERT INTO phieu_linh_bu (khoa_gui, ma_do_vai, so_luong) VALUES (%s, %s, %s)", (khoa, ma_dv, sl))

    def get_linh_bu(self):
        self.setup_extended_tables()
        return self.fetch_all("SELECT * FROM phieu_linh_bu WHERE trang_thai='CHO_DUYET'")

    def approve_linh_bu(self, req_id, ma_dv, sl):
        self.execute("UPDATE danh_muc_do_vai SET cssd_ton_thuc_te = cssd_ton_thuc_te - %s WHERE ma_do_vai=%s", (sl, ma_dv))
        return self.execute("UPDATE phieu_linh_bu SET trang_thai='DA_DUYET' WHERE id=%s", (req_id,))

    def thanh_ly_do_vai(self, ma_dv, sl):
        return self.execute("UPDATE danh_muc_do_vai SET cssd_ton_thuc_te = cssd_ton_thuc_te - %s WHERE ma_do_vai=%s", (sl, ma_dv))
        
    def get_report_data(self):
        total_sets = self.fetch_one("SELECT COUNT(*) as c FROM spm_set_tracking")['c'] if self.fetch_one("SELECT COUNT(*) as c FROM spm_set_tracking") else 0
        total_dv = self.fetch_one("SELECT SUM(cssd_ton_thuc_te) as c FROM danh_muc_do_vai")['c'] if self.fetch_one("SELECT SUM(cssd_ton_thuc_te) as c FROM danh_muc_do_vai") else 0
        return {"sets": total_sets, "linens": total_dv}

    def setup_multi_client_tables(self):
        self.execute('''CREATE TABLE IF NOT EXISTS lich_su_giao_nhan (
            id INT AUTO_INCREMENT PRIMARY KEY,
            khoa_giao VARCHAR(100),
            ma_do VARCHAR(50),
            so_luong INT,
            trang_thai VARCHAR(50) DEFAULT 'CHO_TIEP_NHAN',
            thoi_gian DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')

    def send_dirty_items(self, khoa, ma_do, sl, thoi_gian=None, trang_thai='CHO_TIEP_NHAN', ma_phieu=None):
        self.setup_multi_client_tables()
        if thoi_gian:
            return self.execute("INSERT INTO lich_su_giao_nhan (khoa_giao, ma_do, so_luong, thoi_gian, trang_thai, ma_phieu) VALUES (%s, %s, %s, %s, %s, %s)", (khoa, ma_do, sl, thoi_gian, trang_thai, ma_phieu))
        return self.execute("INSERT INTO lich_su_giao_nhan (khoa_giao, ma_do, so_luong, trang_thai, ma_phieu) VALUES (%s, %s, %s, %s, %s)", (khoa, ma_do, sl, trang_thai, ma_phieu))

    def get_pending_dirty_items(self):
        self.setup_multi_client_tables()
        return self.fetch_all("SELECT * FROM lich_su_giao_nhan WHERE trang_thai='CHO_TIEP_NHAN' ORDER BY thoi_gian DESC, id DESC")

    def receive_dirty_items(self, req_id, ma_do, sl):
        # Tiep nhan -> Update ton kho
        self.execute("UPDATE lich_su_giao_nhan SET trang_thai='DA_TIEP_NHAN' WHERE id=%s", (req_id,))
        # Example update: Tang hang dang cho giat
        pass

    def distribute_clean_items(self, req_id, ma_do, sl):
        # Xuat phieu -> Tru ton kho sach
        self.execute("UPDATE danh_muc_do_vai SET cssd_ton_thuc_te = cssd_ton_thuc_te - %s WHERE ma_do_vai=%s", (sl, ma_do))
        self.execute("UPDATE lich_su_giao_nhan SET trang_thai='DA_CAP_PHAT' WHERE id=%s", (req_id,))

    def setup_dovai_advanced(self):
        # Add ton_kho_mua column if not exists
        try:
            self.execute("ALTER TABLE danh_muc_do_vai ADD COLUMN ton_kho_mua INT DEFAULT 0")
        except:
            pass
            
    def nhap_kho_mua(self, ma_do_vai, sl):
        self.setup_dovai_advanced()
        self.execute("UPDATE danh_muc_do_vai SET ton_kho_mua = COALESCE(ton_kho_mua, 0) + %s WHERE ma_do_vai=%s", (sl, ma_do_vai))
        
    def xuat_kho_mua_sang_lh(self, ma_do_vai, sl):
        self.setup_dovai_advanced()
        # Tru kho mua, cong kho LH (cssd_ton_thuc_te)
        self.execute("UPDATE danh_muc_do_vai SET ton_kho_mua = ton_kho_mua - %s, cssd_ton_thuc_te = cssd_ton_thuc_te + %s WHERE ma_do_vai=%s", (sl, sl, ma_do_vai))

    def chuyen_loai_do_vai(self, ma_cu, ma_moi, sl):
        # Tru kho cu, cong kho moi
        self.execute("UPDATE danh_muc_do_vai SET cssd_ton_thuc_te = cssd_ton_thuc_te - %s WHERE ma_do_vai=%s", (sl, ma_cu))
        self.execute("UPDATE danh_muc_do_vai SET cssd_ton_thuc_te = cssd_ton_thuc_te + %s WHERE ma_do_vai=%s", (sl, ma_moi))

    def reject_dirty_items(self, req_id, reason):
        self.execute("UPDATE lich_su_giao_nhan SET trang_thai='TU_CHOI' WHERE id=%s", (req_id,))
        self.execute("INSERT INTO lich_su_bien_dong (thoi_gian, nguoi_thuc_hien, bang_du_lieu, ma_item, noi_dung) VALUES (NOW(), 'KSNK', 'lich_su_giao_nhan', %s, %s)",
                     (req_id, f"Từ chối phiếu đồ dơ: {reason}"))

    def receive_dirty_items_only(self, req_id):
        self.execute("UPDATE lich_su_giao_nhan SET trang_thai='DANG_GIAT' WHERE id=%s", (req_id,))
        self.execute("INSERT INTO lich_su_bien_dong (thoi_gian, nguoi_thuc_hien, bang_du_lieu, ma_item, noi_dung) VALUES (NOW(), 'KSNK', 'lich_su_giao_nhan', %s, 'Tiếp nhận đồ dơ vào mẻ giặt')", (req_id,))

    def get_laundry_items(self):
        return self.fetch_all("SELECT * FROM lich_su_giao_nhan WHERE trang_thai='DANG_GIAT'")

    def complete_laundry(self, req_id, ma_do, sl):
        # Giặt xong -> Cộng kho sạch
        self.execute("UPDATE danh_muc_do_vai SET cssd_ton_thuc_te = cssd_ton_thuc_te + %s WHERE ma_do_vai=%s", (sl, ma_do))
        self.execute("UPDATE lich_su_giao_nhan SET trang_thai='CHO_CAP_PHAT' WHERE id=%s", (req_id,))
        self.execute("INSERT INTO lich_su_bien_dong (thoi_gian, nguoi_thuc_hien, bang_du_lieu, ma_item, noi_dung) VALUES (NOW(), 'KSNK', 'lich_su_giao_nhan', %s, 'Giặt xong, cộng kho sạch')", (req_id,))

    def phat_do_benh_nhan(self, khoa, ma_bn, ma_do, sl):
        self.execute('''CREATE TABLE IF NOT EXISTS phieu_phat_benh_nhan (
            id INT AUTO_INCREMENT PRIMARY KEY, thoi_gian DATETIME DEFAULT CURRENT_TIMESTAMP,
            khoa VARCHAR(100), ma_benh_nhan VARCHAR(100), ma_do VARCHAR(100), so_luong INT)''')
        self.execute("INSERT INTO phieu_phat_benh_nhan (khoa, ma_benh_nhan, ma_do, so_luong) VALUES (%s, %s, %s, %s)", (khoa, ma_bn, ma_do, sl))
        self.execute("INSERT INTO lich_su_bien_dong (thoi_gian, nguoi_thuc_hien, bang_du_lieu, ma_item, noi_dung) VALUES (NOW(), %s, 'phieu_phat_benh_nhan', %s, %s)", (khoa, ma_bn, f"Phát {sl} {ma_do} cho BN"))

    def get_phieu_cap_phat(self):
        self.execute('''CREATE TABLE IF NOT EXISTS phieu_cap_phat (
            id INT AUTO_INCREMENT PRIMARY KEY, thoi_gian DATETIME DEFAULT CURRENT_TIMESTAMP,
            khoa_nhan VARCHAR(100), ma_do VARCHAR(100), so_luong INT)''')
        return self.fetch_all("SELECT * FROM phieu_cap_phat ORDER BY thoi_gian DESC")

    def tao_phieu_cap_phat(self, khoa, ma_do, sl, thoi_gian=None):
        # Trừ tồn kho sạch
        self.execute("UPDATE danh_muc_do_vai SET cssd_ton_thuc_te = cssd_ton_thuc_te - %s WHERE ma_do_vai=%s", (sl, ma_do))
        # Tạo phiếu
        if thoi_gian:
            self.execute("INSERT INTO phieu_cap_phat (khoa_nhan, ma_do, so_luong, thoi_gian) VALUES (%s, %s, %s, %s)", (khoa, ma_do, sl, thoi_gian))
        else:
            self.execute("INSERT INTO phieu_cap_phat (khoa_nhan, ma_do, so_luong) VALUES (%s, %s, %s)", (khoa, ma_do, sl))
        self.execute("INSERT INTO lich_su_bien_dong (thoi_gian, nguoi_thuc_hien, bang_du_lieu, ma_item, noi_dung) VALUES (NOW(), 'KSNK', 'phieu_cap_phat', %s, %s)", (ma_do, f"Cấp phát {sl} cái cho {khoa}"))

        # FIFO update lich_su_giao_nhan
        rows = self.fetch_all("SELECT id, so_luong FROM lich_su_giao_nhan WHERE khoa_giao=%s AND ma_do=%s AND trang_thai='CHO_CAP_PHAT' ORDER BY thoi_gian ASC", (khoa, ma_do))
        if rows:
            sl_remain = sl
            for r in rows:
                if sl_remain <= 0: break
                if r['so_luong'] <= sl_remain:
                    self.execute("UPDATE lich_su_giao_nhan SET trang_thai='DA_CAP_PHAT' WHERE id=%s", (r['id'],))
                    sl_remain -= r['so_luong']
                else:
                    self.execute("UPDATE lich_su_giao_nhan SET so_luong = so_luong - %s WHERE id=%s", (sl_remain, r['id']))
                    self.execute("INSERT INTO lich_su_giao_nhan (khoa_giao, ma_do, so_luong, trang_thai, thoi_gian) SELECT khoa_giao, ma_do, %s, 'DA_CAP_PHAT', thoi_gian FROM lich_su_giao_nhan WHERE id=%s", (sl_remain, r['id']))
                    sl_remain = 0

    def get_linh_bu(self):
        self.execute('''CREATE TABLE IF NOT EXISTS phieu_linh_bu (
            id INT AUTO_INCREMENT PRIMARY KEY, thoi_gian DATETIME DEFAULT CURRENT_TIMESTAMP,
            khoa_gui VARCHAR(100), ma_do_vai VARCHAR(100), so_luong INT)''')
        return self.fetch_all("SELECT * FROM phieu_linh_bu ORDER BY thoi_gian DESC")
        
    def request_linh_bu(self, khoa, ma_dv, sl):
        self.execute("INSERT INTO phieu_linh_bu (khoa_gui, ma_do_vai, so_luong) VALUES (%s, %s, %s)", (khoa, ma_dv, sl))
        
    def approve_linh_bu(self, req_id, ma_dv, sl):
        self.execute("UPDATE danh_muc_do_vai SET cssd_ton_thuc_te = cssd_ton_thuc_te - %s WHERE ma_do_vai=%s", (sl, ma_dv))
        self.execute("DELETE FROM phieu_linh_bu WHERE id=%s", (req_id,))
        self.execute("INSERT INTO lich_su_bien_dong (thoi_gian, nguoi_thuc_hien, bang_du_lieu, ma_item, noi_dung) VALUES (NOW(), 'KSNK', 'phieu_linh_bu', %s, %s)", (ma_dv, f"Duyệt lĩnh bù {sl} cái"))

    def get_tu_truc_khoa(self, khoa):
        self.execute('''CREATE TABLE IF NOT EXISTS tu_truc_khoa (
            id INT AUTO_INCREMENT PRIMARY KEY,
            khoa VARCHAR(100),
            ma_do VARCHAR(100),
            so_luong INT DEFAULT 0,
            UNIQUE KEY (khoa, ma_do)
        )''')
        return self.fetch_all("SELECT ma_do, so_luong FROM tu_truc_khoa WHERE khoa=%s", (khoa,))

    def get_phieu_gui_cua_khoa(self, khoa):
        return self.fetch_all("SELECT * FROM lich_su_giao_nhan WHERE khoa_giao=%s ORDER BY thoi_gian DESC", (khoa,))

    def receive_dirty_items_only_advanced(self, req_id, ma_phieu=None):
        """
        Tiếp nhận phiếu với Optimistic Locking.
        Chỉ cập nhật nếu phiếu đang ở trạng thái 'CHO_TIEP_NHAN'.
        Trả về True nếu thành công, False nếu phiếu đã bị client khác nhận rồi.
        """
        # --- OPTIMISTIC LOCK ---
        # Dùng WHERE trang_thai='CHO_TIEP_NHAN' để đảm bảo chỉ 1 client thắng
        if ma_phieu:
            rows = self.execute_rowcount(
                "UPDATE lich_su_giao_nhan SET trang_thai='DANG_GIAT', ma_phieu=%s "
                "WHERE id=%s AND trang_thai='CHO_TIEP_NHAN'",
                (ma_phieu, req_id)
            )
        else:
            rows = self.execute_rowcount(
                "UPDATE lich_su_giao_nhan SET trang_thai='DANG_GIAT' "
                "WHERE id=%s AND trang_thai='CHO_TIEP_NHAN'",
                (req_id,)
            )
        
        # Nếu rows == 0: client khác đã nhận trước → bỏ qua, không trừ kho
        if rows == 0:
            return False
        
        # Chỉ trừ kho nếu UPDATE thành công (rows == 1)
        req = self.fetch_one("SELECT khoa_giao, ma_do, so_luong FROM lich_su_giao_nhan WHERE id=%s", (req_id,))
        if req:
            khoa = req['khoa_giao']
            ma_do = req['ma_do']
            sl = int(req['so_luong'])
            
            tu = self.fetch_one("SELECT so_luong, dang_su_dung FROM tu_truc_khoa WHERE khoa=%s AND ma_do=%s", (khoa, ma_do))
            if tu:
                cur_dang = int(tu.get('dang_su_dung', 0))
                tru_dang = min(cur_dang, sl)
                tru_sach = sl - tru_dang
                self.execute(
                    "UPDATE tu_truc_khoa SET dang_su_dung = dang_su_dung - %s, so_luong = so_luong - %s "
                    "WHERE khoa=%s AND ma_do=%s",
                    (tru_dang, tru_sach, khoa, ma_do)
                )
        
        self.execute(
            "INSERT INTO lich_su_bien_dong (thoi_gian, nguoi_thuc_hien, bang_du_lieu, ma_item, noi_dung) "
            "VALUES (NOW(), 'KSNK', 'lich_su_giao_nhan', %s, 'Tiếp nhận đồ dơ vào mẻ giặt')",
            (req_id,)
        )
        return True

    def get_dashboard_ksnk(self):
        stats = {}
        # Do Vai Sach KSNK
        r = self.fetch_one("SELECT SUM(cssd_ton_thuc_te) as sl FROM danh_muc_do_vai")
        stats['dv_sach'] = r['sl'] if r and r['sl'] else 0
        
        # Do Vai Dang Giat
        r = self.fetch_one("SELECT SUM(so_luong) as sl FROM lich_su_giao_nhan WHERE trang_thai='DANG_GIAT'")
        stats['dv_giat'] = r['sl'] if r and r['sl'] else 0
        
        # Bo dung cu dang xu ly (Not READY)
        r = self.fetch_one("SELECT COUNT(*) as c FROM danh_muc_bo_dung_cu WHERE trang_thai != 'READY'")
        stats['bo_xu_ly'] = r['c'] if r else 0
        
        return stats

    def get_dashboard_khoa(self, khoa_name):
        stats = {}
        # Tu truc sach
        r = self.fetch_one("SELECT SUM(so_luong) as sl FROM tu_truc_khoa WHERE khoa=%s", (khoa_name,))
        stats['dv_sach'] = r['sl'] if r and r['sl'] else 0
        
        # Dang su dung
        r = self.fetch_one("SELECT SUM(dang_su_dung) as sl FROM tu_truc_khoa WHERE khoa=%s", (khoa_name,))
        stats['dv_dung'] = r['sl'] if r and r['sl'] else 0
        
        # Phieu dang cho KSNK tiep nhan
        r = self.fetch_one("SELECT COUNT(*) as c FROM lich_su_giao_nhan WHERE khoa_giao=%s AND trang_thai='CHO_TIEP_NHAN'", (khoa_name,))
        stats['phieu_cho'] = r['c'] if r else 0
        
        return stats

    def edit_phieu_cap_phat(self, phieu_id, new_sl):
        # Retrieve old info
        old = self.fetch_one("SELECT * FROM phieu_cap_phat WHERE id=%s", (phieu_id,))
        if not old: return False
        diff = new_sl - old['so_luong']
        if diff == 0: return True
        
        # update phieu
        self.execute("UPDATE phieu_cap_phat SET so_luong=%s WHERE id=%s", (new_sl, phieu_id))
        
        # update danh_muc_do_vai (cssd_ton_thuc_te)
        self.execute("UPDATE danh_muc_do_vai SET cssd_ton_thuc_te = cssd_ton_thuc_te - %s WHERE ma_do_vai=%s", (diff, old['ma_do']))
        
        # update tu_truc_khoa
        self.execute("UPDATE tu_truc_khoa SET so_luong = so_luong + %s WHERE khoa=%s AND ma_do=%s", (diff, old['khoa_nhan'], old['ma_do']))
        
        self.execute("INSERT INTO lich_su_bien_dong (thoi_gian, nguoi_thuc_hien, bang_du_lieu, ma_item, noi_dung) VALUES (NOW(), 'KSNK', 'phieu_cap_phat', %s, %s)", 
                     (old['ma_do'], f"Sửa phiếu {phieu_id}: {old['so_luong']} -> {new_sl}"))
        return True

    def edit_phieu_gui_do_do(self, phieu_id, new_sl):
        old = self.fetch_one("SELECT * FROM lich_su_giao_nhan WHERE id=%s", (phieu_id,))
        if not old: return False
        if old['trang_thai'] != 'CHO_TIEP_NHAN':
            return False # Only allow edit if not yet processed
        
        self.execute("UPDATE lich_su_giao_nhan SET so_luong=%s WHERE id=%s", (new_sl, phieu_id))
        return True

    # --- DASHBOARD METHODS EXTRACTED FROM GS.PY ---
    def get_kpi_summary_v2(self, date_str):
        """Lấy 4 KPI quan trọng cho Dashboard Giám Sát"""
        try:
            # 1. Nhận hôm nay (Tổng số Khoa đã giao)
            sql_nhan = "SELECT COUNT(DISTINCT khoa_giao) as cnt FROM lich_su_giao_nhan WHERE DATE(thoi_gian) = %s"
            nhan_rows = self.fetch_all(sql_nhan, (date_str,))
            nhan = nhan_rows[0]['cnt'] if nhan_rows else 0
            
            # 2. Chờ xử lý (Chưa hấp xong)
            sql_cho = "SELECT SUM(so_luong) as cnt FROM lich_su_giao_nhan WHERE trang_thai NOT IN ('CHO_CAP_PHAT', 'DA_CAP_PHAT')"
            cho_rows = self.fetch_all(sql_cho)
            cho = int(cho_rows[0]['cnt']) if cho_rows and cho_rows[0]['cnt'] else 0
            
            # 3. Đã hấp (Mẻ) hôm nay
            sql_hap = "SELECT COUNT(*) as cnt FROM runs WHERE status='COMPLETED' AND date=%s"
            hap_rows = self.fetch_all(sql_hap, (date_str,))
            hap = hap_rows[0]['cnt'] if hap_rows else 0
            
            # 4. Kho sạch (Món)
            sql_kho = "SELECT SUM(so_luong) as cnt FROM lich_su_giao_nhan WHERE trang_thai = 'CHO_CAP_PHAT'"
            kho_rows = self.fetch_all(sql_kho)
            kho = int(kho_rows[0]['cnt']) if kho_rows and kho_rows[0]['cnt'] else 0
            
            return {
                "nhan": nhan,
                "cho_xu_ly": cho,
                "da_xu_ly": hap,
                "kho_sach": kho
            }
        except Exception as e: 
            print("Lỗi dash stats:", e)
            return {"nhan": 0, "cho_xu_ly": 0, "da_xu_ly": 0, "kho_sach": 0}

    def get_bo_suggestions(self, keyword):
        if not keyword: return []
        import unicodedata
        def remove_accents(input_str):
            nfkd_form = unicodedata.normalize('NFKD', input_str)
            return u"".join([c for c in nfkd_form if not unicodedata.combining(c)]).lower()
            
        kw_clean = remove_accents(keyword)
        sql = "SELECT id, ten_bo, ma_qr FROM bo_dung_cu WHERE ten_bo LIKE %s OR ten_bo_chuan_hoa LIKE %s LIMIT 10"
        return self.fetch_all(sql, (f"%{keyword}%", f"%{kw_clean}%")) or []

    def get_chart_data_7days(self, start_str, end_str):
        # start_str might be "2026-09-09 00:00:00", we just need "2026-09-09"
        d1 = start_str.split()[0]
        d2 = end_str.split()[0]
        sql = """
            SELECT r.date as ngay, m.name as ten_may, COUNT(*) as so_me
            FROM runs r JOIN machines m ON r.machine_id = m.id 
            WHERE r.date BETWEEN %s AND %s
            GROUP BY r.date, m.name ORDER BY r.date
        """
        return self.fetch_all(sql, (d1, d2)) or []
        
    def get_realtime_machines(self):
        sql = """
            SELECT 
                name as ten_may, 
                status as trang_thai, 
                DATE_SUB(end_time, INTERVAL 60 MINUTE) as thoi_gian_bat_dau,
                60 as thoi_gian_du_kien
            FROM machines
            ORDER BY group_id, name
        """
        return self.fetch_all(sql) or []
        
    def get_traceability_timeline(self, keyword):
        """Truy vết dựa trên lich_su_giao_nhan"""
        id_val = int(keyword) if keyword.isdigit() else 0
        sql = """
            SELECT id, khoa_giao, ma_do, so_luong, trang_thai, thoi_gian, ma_phieu 
            FROM lich_su_giao_nhan 
            WHERE ma_do LIKE %s OR id = %s
            ORDER BY thoi_gian DESC LIMIT 1
        """
        rows = self.fetch_all(sql, (f"%{keyword}%", id_val))
        if not rows: return None
        
        latest = rows[0]
        
        bo_info = {
            "ten_bo": latest['ma_do'],
            "trang_thai": latest['trang_thai']
        }
        
        cycle = {
            'nhan': {'thoi_gian_str': latest['thoi_gian'].strftime('%H:%M %d/%m/%Y') if hasattr(latest['thoi_gian'], 'strftime') else str(latest['thoi_gian']), 'ma_phien': latest['ma_phieu'] or 'Chưa tạo'}
        }
        
        if latest['trang_thai'] in ['CHO_CAP_PHAT', 'DA_CAP_PHAT']:
            cycle['hap'] = {'thoi_gian_str': 'Hoàn thành', 'ma_phien': 'OK'}
            
        if latest['trang_thai'] == 'DA_CAP_PHAT':
            cycle['cap'] = {'thoi_gian_str': 'Đã giao', 'ma_phien': 'OK'}
            
        return {
            "bo_info": bo_info,
            "cycles": [cycle]
        }

    def _get_bulk_trace(self, date_str):
        # Store lists of events to handle multiple cycles per day
        hap_map = {}
        sql_hap = """
            SELECT c.id_goc, c.loai_goc, v.ten_may, v.thoi_gian, v.nhan_vien
            FROM lich_su_van_hanh v
            JOIN chi_tiet_chu_trinh_van_hanh c ON v.ma_phien = c.ma_phien_van_hanh
            WHERE DATE(v.thoi_gian) = %s
        """
        haps = self.fetch_all(sql_hap, (date_str,)) or []
        for h in haps:
            lg = 'THU_THUAT' if 'THU_THUAT' in str(h['loai_goc']).upper() else ('BO' if 'BO' in str(h['loai_goc']).upper() or 'BỘ' in str(h['loai_goc']).upper() else 'DONG_LE')
            key = (h['id_goc'], lg)
            if key not in hap_map: hap_map[key] = []
            hap_map[key].append({"thoi_gian": h['thoi_gian'].strftime('%d/%m/%Y %H:%M:%S') if h['thoi_gian'] else "", "dt": h['thoi_gian'], "ten_may": h['ten_may'], "nhan_vien": h['nhan_vien']})

        cap_map = {}
        sql_cap1 = "SELECT bo_id as id_goc, 'BO' as loai_goc, thoi_gian, khoa, nguoi_cap as nhan_vien FROM lich_su_cap_phat WHERE DATE(thoi_gian) = %s AND bo_id IS NOT NULL"
        sql_cap2 = "SELECT dung_cu_id as id_goc, 'DONG_LE' as loai_goc, thoi_gian, khoa, nguoi_cap as nhan_vien FROM lich_su_cap_phat WHERE DATE(thoi_gian) = %s AND dung_cu_id IS NOT NULL"
        sql_cap3 = "SELECT dung_cu_id as id_goc, 'THU_THUAT' as loai_goc, gio_cap as thoi_gian, khoa, nguoi_cap as nhan_vien FROM lich_su_cap_phat_thu_thuat WHERE DATE(gio_cap) = %s"
        
        for c in (self.fetch_all(sql_cap1, (date_str,)) or []):
            key = (c['id_goc'], c['loai_goc'])
            if key not in cap_map: cap_map[key] = []
            cap_map[key].append({"thoi_gian": c['thoi_gian'].strftime('%d/%m/%Y %H:%M:%S') if c['thoi_gian'] else "", "dt": c['thoi_gian'], "khoa": c['khoa'], "nhan_vien": c['nhan_vien']})
            
        for c in (self.fetch_all(sql_cap2, (date_str,)) or []):
            key = (c['id_goc'], c['loai_goc'])
            if key not in cap_map: cap_map[key] = []
            cap_map[key].append({"thoi_gian": c['thoi_gian'].strftime('%d/%m/%Y %H:%M:%S') if c['thoi_gian'] else "", "dt": c['thoi_gian'], "khoa": c['khoa'], "nhan_vien": c['nhan_vien']})
            
        for c in (self.fetch_all(sql_cap3, (date_str,)) or []):
            key = (c['id_goc'], c['loai_goc'])
            if key not in cap_map: cap_map[key] = []
            cap_map[key].append({"thoi_gian": c['thoi_gian'].strftime('%d/%m/%Y %H:%M:%S') if c['thoi_gian'] else "", "dt": c['thoi_gian'], "khoa": c['khoa'], "nhan_vien": c['nhan_vien']})
            
        for k in hap_map: hap_map[k].sort(key=lambda x: x['dt'])
        for k in cap_map: cap_map[k].sort(key=lambda x: x['dt'])
            
        return hap_map, cap_map

    def get_expiry_alerts(self):
        # Scan CHO_CAP_PHAT items, find expiry date
        sql = """
            SELECT n.khoa_giao as khoa, n.ma_do as ten, n.trang_thai, n.thoi_gian as ngay_hap,
                   IFNULL(b.han_tiet_khuan, IFNULL(v.han_tiet_khuan, 30)) as han
            FROM lich_su_giao_nhan n
            LEFT JOIN danh_muc_bo_dung_cu b ON n.ma_do = b.ma_bo
            LEFT JOIN danh_muc_do_vai v ON n.ma_do = v.ma_do_vai
            WHERE n.trang_thai = 'CHO_CAP_PHAT'
        """
        rows = self.fetch_all(sql)
        alerts = []
        from datetime import datetime
        now = datetime.now()
        for r in rows:
            if not r['ngay_hap']: continue
            # Calculate days left
            delta = (now - r['ngay_hap']).days
            days_left = r['han'] - delta
            if days_left <= 3:
                r['days_left'] = days_left
                alerts.append(r)
        return alerts
        
    def get_min_stock_alerts(self):
        sql = """
            SELECT ma_do_vai, ten_do_vai, cssd_ton_thuc_te, cssd_ton_toi_thieu 
            FROM danh_muc_do_vai 
            WHERE cssd_ton_thuc_te < cssd_ton_toi_thieu AND trang_thai = 1
        """
        return self.fetch_all(sql) or []
        
    def get_pending_issue_items(self, khoa):
        # Chỉ lấy những đồ đã tiệt khuẩn xong (CHO_CAP_PHAT) thuộc về khoa này
        sql = """
            SELECT n.ma_do as code, n.so_luong as qty,
                   IFNULL(b.ten_bo, IFNULL(v.ten_do_vai, d.ten_dc)) as name,
                   CASE WHEN b.ten_bo IS NOT NULL THEN 'BỘ'
                        WHEN v.ten_do_vai IS NOT NULL THEN 'VẢI'
                        ELSE 'LẺ' END as type
            FROM lich_su_giao_nhan n
            LEFT JOIN danh_muc_bo_dung_cu b ON n.ma_do = b.ma_bo
            LEFT JOIN danh_muc_do_vai v ON n.ma_do = v.ma_do_vai
            LEFT JOIN danh_muc_dung_cu d ON n.ma_do = d.ma_dc
            WHERE n.khoa_giao = %s AND n.trang_thai = 'CHO_CAP_PHAT'
        """
        return self.fetch_all(sql, (khoa,)) or []
        
    def get_kpi_received_drilldown(self, date_str):
        sql = """
            SELECT khoa_giao as khoa, ma_do as ten, so_luong, trang_thai, thoi_gian, ma_phieu 
            FROM lich_su_giao_nhan 
            WHERE DATE(thoi_gian) = %s
        """
        rows = self.fetch_all(sql, (date_str,))
        items = []
        for r in rows:
            trace = {'nhan': {'thoi_gian': r['thoi_gian'].strftime('%H:%M %d/%m') if hasattr(r['thoi_gian'], 'strftime') else str(r['thoi_gian'])[:16], 'khoa': r['khoa'], 'nhan_vien': ''}}
            if r['trang_thai'] in ['CHO_CAP_PHAT', 'DA_CAP_PHAT']:
                trace['hap'] = {'thoi_gian': 'Hoàn thành', 'ten_may': 'N/A', 'nhan_vien': ''}
            if r['trang_thai'] == 'DA_CAP_PHAT':
                trace['cap'] = {'thoi_gian': 'Đã giao', 'khoa': '', 'nhan_vien': ''}
            items.append({'loai_goc': '', 'ten': r['ten'], 'so_luong': r['so_luong'], 'trace': trace})
        return items
        
    def get_kpi_sterilized_drilldown(self, date_str):
        sql = """
            SELECT khoa_giao as khoa, ma_do as ten, so_luong, trang_thai, thoi_gian, ma_phieu 
            FROM lich_su_giao_nhan 
            WHERE DATE(thoi_gian) = %s AND trang_thai IN ('CHO_CAP_PHAT', 'DA_CAP_PHAT')
        """
        rows = self.fetch_all(sql, (date_str,))
        items = []
        for r in rows:
            trace = {'nhan': {'thoi_gian': r['thoi_gian'].strftime('%H:%M %d/%m') if hasattr(r['thoi_gian'], 'strftime') else str(r['thoi_gian'])[:16], 'khoa': r['khoa'], 'nhan_vien': ''}}
            if r['trang_thai'] in ['CHO_CAP_PHAT', 'DA_CAP_PHAT']:
                trace['hap'] = {'thoi_gian': 'Hoàn thành', 'ten_may': 'N/A', 'nhan_vien': ''}
            if r['trang_thai'] == 'DA_CAP_PHAT':
                trace['cap'] = {'thoi_gian': 'Đã giao', 'khoa': '', 'nhan_vien': ''}
            items.append({'loai_goc': '', 'ten': r['ten'], 'so_luong': r['so_luong'], 'trace': trace})
        return items

    def get_kpi_clean_inventory_drilldown(self):
        sql = """
            SELECT khoa_giao as khoa, ma_do as ten, so_luong, trang_thai, thoi_gian, ma_phieu 
            FROM lich_su_giao_nhan 
            WHERE trang_thai = 'CHO_CAP_PHAT'
        """
        rows = self.fetch_all(sql)
        items = []
        for r in rows:
            trace = {'nhan': {'thoi_gian': r['thoi_gian'].strftime('%H:%M %d/%m') if hasattr(r['thoi_gian'], 'strftime') else str(r['thoi_gian'])[:16], 'khoa': r['khoa'], 'nhan_vien': ''}}
            if r['trang_thai'] in ['CHO_CAP_PHAT', 'DA_CAP_PHAT']:
                trace['hap'] = {'thoi_gian': 'Hoàn thành', 'ten_may': 'N/A', 'nhan_vien': ''}
            if r['trang_thai'] == 'DA_CAP_PHAT':
                trace['cap'] = {'thoi_gian': 'Đã giao', 'khoa': '', 'nhan_vien': ''}
            items.append({'loai_goc': '', 'ten': r['ten'], 'so_luong': r['so_luong'], 'trace': trace})
        return items



    # --- Settings / Links ---
    def get_links(self):
        self.setup_extended_tables()
        return self.fetch_all("SELECT * FROM danh_muc_link")

    def add_link(self, ten, url, loai):
        self.setup_extended_tables()
        return self.execute("INSERT INTO danh_muc_link (ten_link, url, loai_link) VALUES (%s, %s, %s)", (ten, url, loai))

    def update_link(self, link_id, ten, url, loai):
        return self.execute("UPDATE danh_muc_link SET ten_link=%s, url=%s, loai_link=%s WHERE id=%s", (ten, url, loai, link_id))

    def delete_link(self, link_id):
        return self.execute("DELETE FROM danh_muc_link WHERE id=%s", (link_id,))
