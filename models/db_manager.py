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
        # 1. Nhận hôm nay (Tổng số Khoa đã giao)
        sql_nhan = """
            SELECT COUNT(DISTINCT khoa) as cnt FROM (
                SELECT khoa FROM lich_su_giao_nhan WHERE DATE(thoi_gian) = %s
                UNION ALL
                SELECT khoa FROM lich_su_giao_nhan_thu_thuat WHERE DATE(gio_giao) = %s
            ) as tmp
        """
        # 3. Đã xử lý (Số chu trình chạy hôm nay)
        sql_chay = "SELECT COUNT(*) as cnt FROM lich_su_van_hanh WHERE DATE(thoi_gian) = %s"
        
        # 4. Kho sạch (Sẵn sàng cấp phát) từ vòng lặp tiệt khuẩn thực tế
        sql_kho_sach = """
            SELECT SUM(available) as cnt FROM (
                SELECT (SUM(ct.so_luong) - IFNULL(T_DIST.total_distributed, 0)) as available
                FROM chi_tiet_chu_trinh_van_hanh ct 
                JOIN lich_su_van_hanh ls ON ct.ma_phien_van_hanh = ls.ma_phien
                LEFT JOIN (
                    SELECT CASE WHEN bo_id IS NOT NULL THEN bo_id ELSE dung_cu_id END as id_goc,
                           CASE WHEN bo_id IS NOT NULL THEN 'bo_dung_cu' ELSE 'do_dong_le' END as loai_goc,
                           SUM(so_luong) as total_distributed 
                    FROM lich_su_cap_phat WHERE IFNULL(loai_phieu, 'CAP_PHAT') IN ('CAP_PHAT', 'RESET_SACH')
                    GROUP BY id_goc, loai_goc
                ) T_DIST ON ct.id_goc = T_DIST.id_goc AND ct.loai_goc = T_DIST.loai_goc
                WHERE ls.trang_thai = 'COMPLETED' 
                GROUP BY ct.id_goc, ct.loai_goc, T_DIST.total_distributed
            ) sub WHERE available > 0
        """
        
        # 2. Chờ xử lý (Chưa hấp)
        sql_cho_xu_ly = """
            SELECT SUM(cho) as cnt FROM (
                SELECT (IFNULL(nhan.t, 0) - IFNULL(hap.t, 0)) as cho FROM (
                    SELECT CASE WHEN bo_id IS NOT NULL THEN bo_id ELSE dung_cu_id END as id_goc,
                           CASE WHEN bo_id IS NOT NULL THEN 'bo_dung_cu' ELSE 'do_dong_le' END as loai_goc,
                           SUM(so_luong) as t FROM lich_su_giao_nhan GROUP BY id_goc, loai_goc
                ) nhan
                LEFT JOIN (
                    SELECT ct.id_goc, ct.loai_goc, SUM(ct.so_luong) as t FROM chi_tiet_chu_trinh_van_hanh ct
                    JOIN lich_su_van_hanh ls ON ct.ma_phien_van_hanh = ls.ma_phien WHERE ls.trang_thai='COMPLETED'
                    GROUP BY ct.id_goc, ct.loai_goc
                ) hap ON nhan.id_goc = hap.id_goc AND nhan.loai_goc = hap.loai_goc
            ) sub WHERE cho > 0
        """
        
        try:
            nhan = self.fetch_all(sql_nhan, (date_str, date_str))
            cho = self.fetch_all(sql_cho_xu_ly)
            chay = self.fetch_all(sql_chay, (date_str,))
            kho = self.fetch_all(sql_kho_sach)
            
            # Plus thu thuat
            # Cho đơn giản, tính luôn đồ thủ thuật vào kho sạch nếu muốn, nhưng hiện tại query đã quá dài
            return {
                "nhan": nhan[0]['cnt'] if nhan else 0,
                "cho_xu_ly": int(cho[0]['cnt']) if cho and cho[0]['cnt'] else 0,
                "da_xu_ly": chay[0]['cnt'] if chay else 0,
                "kho_sach": int(kho[0]['cnt']) if kho and kho[0]['cnt'] else 0
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

    def get_traceability_timeline(self, keyword):
        """Truy xuất dòng thời gian của 1 dụng cụ (Bộ) và phân rã thành chu kỳ"""
        import unicodedata
        def remove_accents(input_str):
            nfkd_form = unicodedata.normalize('NFKD', input_str)
            return u"".join([c for c in nfkd_form if not unicodedata.combining(c)]).lower()
            
        if keyword.isdigit():
            # Nếu là số nguyên, tìm chính xác theo mã QR hoặc ID
            sql_find = "SELECT id, ma_qr, ten_bo, khoa, trang_thai FROM bo_dung_cu WHERE ma_qr = %s OR id = %s LIMIT 1"
            bos = self.fetch_all(sql_find, (keyword, keyword))
        else:
            # Tìm chính xác tương đối theo tên bộ
            kw_clean = remove_accents(keyword)
            sql_find = "SELECT id, ma_qr, ten_bo, khoa, trang_thai FROM bo_dung_cu WHERE ten_bo LIKE %s OR ten_bo_chuan_hoa LIKE %s LIMIT 1"
            bos = self.fetch_all(sql_find, (f"%{keyword}%", f"%{kw_clean}%"))
        
        if not bos: return None

        bo = bos[0]
        bo_id = bo['id']
        
        # 1. Nhận
        nhan = self.fetch_all("SELECT thoi_gian as dt, ma_phien, khoa, nguoi_nhan as nv, 'nhan' as stage FROM lich_su_giao_nhan WHERE bo_id = %s", (bo_id,)) or []
        # 2. Checklist
        chk = self.fetch_all("SELECT thoi_gian_checklist as dt, ma_phien, nv_kktk, nv_xu_ly, trang_thai_bo, ghi_chu_bo, 'checklist' as stage FROM lich_su_checklist WHERE id_bo = %s", (bo_id,)) or []
        # 3. Hấp
        hap = self.fetch_all("""SELECT v.thoi_gian as dt, v.ma_phien, v.ten_may, v.nhan_vien as nv, v.duong_dan_anh_online, 'hap' as stage 
            FROM lich_su_van_hanh v JOIN chi_tiet_chu_trinh_van_hanh c ON v.ma_phien = c.ma_phien_van_hanh 
            WHERE c.id_goc = %s AND (c.loai_goc = 'bo_dung_cu' OR UPPER(c.loai_goc) = 'BO' OR UPPER(c.loai_goc) = 'BỘ')""", (bo_id,)) or []
        # 4. Cấp
        cap = self.fetch_all("SELECT thoi_gian as dt, khoa, nguoi_cap as nv, 'cap' as stage FROM lich_su_cap_phat WHERE bo_id = %s", (bo_id,)) or []
        
        # Gộp và sort sự kiện
        all_events = nhan + chk + hap + cap
        for ev in all_events:
            if not ev['dt']: ev['dt'] = datetime.min
        all_events.sort(key=lambda x: x['dt'])
        
        # State machine phân tách Chu Kỳ
        cycles = []
        current_cycle = {"nhan": None, "checklist": None, "hap": None, "cap": None}
        
        for ev in all_events:
            stage = ev['stage']
            
            # Format time
            if ev['dt'] and ev['dt'] != datetime.min:
                ev['thoi_gian_str'] = ev['dt'].strftime('%d/%m/%Y %H:%M:%S')
            else:
                ev['thoi_gian_str'] = ''
                
            # Logic tách chu kỳ:
            # Nếu gặp Nhận hoặc Checklist MÀ chu kỳ hiện tại ĐÃ CÓ Hấp hoặc Cấp (hoặc đã có sẵn Nhận/Checklist trước đó)
            if stage in ('nhan', 'checklist'):
                if current_cycle['hap'] or current_cycle['cap'] or current_cycle[stage]:
                    cycles.append(current_cycle)
                    current_cycle = {"nhan": None, "checklist": None, "hap": None, "cap": None}
            
            current_cycle[stage] = ev
            
        if any(current_cycle.values()):
            cycles.append(current_cycle)
            
        return {"bo_info": bo, "cycles": cycles}

    def get_machine_batch_stats(self, date_str):
        sql = """
            SELECT ten_may, COUNT(*) as so_me 
            FROM lich_su_van_hanh 
            WHERE DATE(thoi_gian) = %s 
            GROUP BY ten_may
        """
        return self.fetch_all(sql, (date_str,)) or []

    def get_receiving_breakdown(self, date_str):
        sql = """
            SELECT khoa, COUNT(*) as tong 
            FROM lich_su_giao_nhan 
            WHERE DATE(thoi_gian) = %s 
            GROUP BY khoa 
            ORDER BY tong DESC
        """
        return self.fetch_all(sql, (date_str,)) or []

    def get_distribution_balance(self, date_str):
        sql = """
            SELECT 
                k.ten_khoa as khoa,
                IFNULL(nhan.cnt, 0) as da_nhan,
                IFNULL(tra.cnt, 0) as da_tra,
                IFNULL(ton.available_total, 0) as con_lai_trong_kho
            FROM 
                (SELECT DISTINCT ten_khoa FROM khoa_phau_thuat UNION SELECT DISTINCT ten_khoa FROM khoa_thu_thuat) k
            LEFT JOIN (
                SELECT khoa, SUM(so_luong) as cnt FROM lich_su_giao_nhan WHERE DATE(thoi_gian) = %s GROUP BY khoa
            ) nhan ON k.ten_khoa = nhan.khoa
            LEFT JOIN (
                SELECT khoa, SUM(so_luong) as cnt FROM lich_su_cap_phat WHERE DATE(thoi_gian) = %s GROUP BY khoa
            ) tra ON k.ten_khoa = tra.khoa
            LEFT JOIN (
                SELECT ct.khoa as khoa, (SUM(ct.so_luong) - IFNULL(T_DIST.total_distributed, 0)) as available_total
                FROM chi_tiet_chu_trinh_van_hanh ct 
                JOIN lich_su_van_hanh ls ON ct.ma_phien_van_hanh = ls.ma_phien
                LEFT JOIN (
                    SELECT khoa, SUM(so_luong) as total_distributed 
                    FROM lich_su_cap_phat WHERE IFNULL(loai_phieu, 'CAP_PHAT') IN ('CAP_PHAT', 'RESET_SACH')
                    GROUP BY khoa
                ) T_DIST ON ct.khoa = T_DIST.khoa
                WHERE ls.trang_thai = 'COMPLETED' 
                GROUP BY ct.khoa, T_DIST.total_distributed
            ) ton ON k.ten_khoa = ton.khoa
            WHERE IFNULL(nhan.cnt, 0) > 0 OR IFNULL(ton.available_total, 0) > 0
            ORDER BY con_lai_trong_kho DESC
        """
        return self.fetch_all(sql, (date_str, date_str)) or []

    def get_chart_data_7days(self, start_str, end_str):
        sql = """
            SELECT DATE(thoi_gian) as ngay, ten_may, COUNT(*) as so_me
            FROM lich_su_van_hanh WHERE thoi_gian BETWEEN %s AND %s
            GROUP BY DATE(thoi_gian), ten_may ORDER BY ngay
        """
        return self.fetch_all(sql, (start_str, end_str)) or []

    def get_realtime_machines(self):
        sql = "SELECT ten_may, trang_thai, thoi_gian_bat_dau, thoi_gian_du_kien, khu_vuc FROM danh_sach_may ORDER BY khu_vuc, ten_may"
        return self.fetch_all(sql) or []


    def get_universal_traceability(self, id_goc, loai_goc):
        # Giữ lại hàm này phòng khi cần gọi đơn lẻ
        trace = {"nhan": None, "hap": None, "cap": None}
        
        loai_goc_str = str(loai_goc).upper()
        if 'THU_THUAT' in loai_goc_str:
            loai_goc_std = 'THU_THUAT'
        elif 'BO' == loai_goc_str or 'BỘ' in loai_goc_str:
            loai_goc_std = 'BO'
        else:
            loai_goc_std = 'DONG_LE'
            
        if loai_goc_std == 'BO':
            sql_nhan = "SELECT thoi_gian, khoa, nguoi_nhan as nhan_vien FROM lich_su_giao_nhan WHERE bo_id = %s ORDER BY thoi_gian DESC LIMIT 1"
        elif loai_goc_std == 'THU_THUAT':
            sql_nhan = "SELECT gio_giao as thoi_gian, khoa, nguoi_nhan as nhan_vien FROM lich_su_giao_nhan_thu_thuat WHERE dung_cu_id = %s ORDER BY gio_giao DESC LIMIT 1"
        else:
            sql_nhan = "SELECT thoi_gian, khoa, nguoi_nhan as nhan_vien FROM lich_su_giao_nhan WHERE dung_cu_id = %s ORDER BY thoi_gian DESC LIMIT 1"
        nhan = self.fetch_all(sql_nhan, (id_goc,))
        if nhan: trace["nhan"] = nhan[0]

        sql_hap = """
            SELECT v.ma_phien, v.ten_may, v.thoi_gian, v.nhan_vien, v.trang_thai 
            FROM lich_su_van_hanh v
            JOIN chi_tiet_chu_trinh_van_hanh c ON v.ma_phien = c.ma_phien_van_hanh
            WHERE c.id_goc = %s AND (c.loai_goc = %s OR UPPER(c.loai_goc) = %s)
            ORDER BY v.thoi_gian DESC LIMIT 1
        """
        hap = self.fetch_all(sql_hap, (id_goc, loai_goc, loai_goc_std))
        if hap: trace["hap"] = hap[0]

        if loai_goc_std == 'BO':
            sql_cap = "SELECT thoi_gian, khoa, nguoi_cap as nhan_vien FROM lich_su_cap_phat WHERE bo_id = %s ORDER BY thoi_gian DESC LIMIT 1"
        elif loai_goc_std == 'THU_THUAT':
            sql_cap = "SELECT gio_cap as thoi_gian, khoa, nguoi_cap as nhan_vien FROM lich_su_cap_phat_thu_thuat WHERE dung_cu_id = %s ORDER BY gio_cap DESC LIMIT 1"
        else:
            sql_cap = "SELECT thoi_gian, khoa, nguoi_cap as nhan_vien FROM lich_su_cap_phat WHERE dung_cu_id = %s ORDER BY thoi_gian DESC LIMIT 1"
        cap = self.fetch_all(sql_cap, (id_goc,))
        if cap: trace["cap"] = cap[0]
        
        for stage in trace:
            if trace[stage] and 'thoi_gian' in trace[stage] and trace[stage]['thoi_gian']:
                trace[stage]['thoi_gian'] = trace[stage]['thoi_gian'].strftime('%d/%m/%Y %H:%M:%S')
                
        return trace

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

    def get_kpi_received_drilldown(self, date_str):
        sql = """
            SELECT 
                'BO' as loai_goc,
                n.bo_id as id_goc, 
                b.ten_bo as ten,
                n.thoi_gian, n.khoa, n.so_luong, n.nguoi_nhan as nhan_vien, n.ma_phien
            FROM lich_su_giao_nhan n
            JOIN bo_dung_cu b ON n.bo_id = b.id
            WHERE DATE(n.thoi_gian) = %s AND n.bo_id IS NOT NULL
            
            UNION ALL
            
            SELECT 
                'DONG_LE' as loai_goc,
                n.dung_cu_id as id_goc, 
                d.ten_dung_cu as ten,
                n.thoi_gian, n.khoa, n.so_luong, n.nguoi_nhan as nhan_vien, n.ma_phien
            FROM lich_su_giao_nhan n
            JOIN do_dong_le d ON n.dung_cu_id = d.id
            WHERE DATE(n.thoi_gian) = %s AND n.dung_cu_id IS NOT NULL
            
            UNION ALL
            
            SELECT 
                'THU_THUAT' as loai_goc,
                n.dung_cu_id as id_goc, 
                d.ten_dung_cu as ten,
                n.gio_giao as thoi_gian, n.khoa, n.so_luong, n.nguoi_nhan as nhan_vien, n.ma_phien
            FROM lich_su_giao_nhan_thu_thuat n
            JOIN danh_muc_dung_cu_thu_thuat d ON n.dung_cu_id = d.id
            WHERE DATE(n.gio_giao) = %s
            
            ORDER BY thoi_gian DESC
        """
        items = self.fetch_all(sql, (date_str, date_str, date_str)) or []
        
        # Tối ưu Bulk map
        hap_map, cap_map = self._get_bulk_trace(date_str)
        
        for item in items:
            key = (item['id_goc'], item['loai_goc'])
            item_dt = item['thoi_gian']
            nhan = {"thoi_gian": item_dt.strftime('%d/%m/%Y %H:%M:%S') if item_dt else "", "khoa": item['khoa'], "nhan_vien": item['nhan_vien']}
            
            # Find first hap AFTER nhan
            hap = None
            for h in hap_map.get(key, []):
                if h['dt'] >= item_dt:
                    hap = h
                    break
                    
            # Find first cap AFTER hap (or nhan if no hap)
            cap = None
            base_dt = hap['dt'] if hap else item_dt
            for c in cap_map.get(key, []):
                if c['dt'] >= base_dt:
                    cap = c
                    break
                    
            item['trace'] = {"nhan": nhan, "hap": hap, "cap": cap}
            if item['thoi_gian']:
                item['thoi_gian'] = item['thoi_gian'].strftime('%d/%m/%Y %H:%M:%S')
        return items

    def get_kpi_sterilized_drilldown(self, date_str):
        sql = """
            SELECT ma_phien, ten_may, thoi_gian, nhan_vien, trang_thai, cycle_type, ket_qua, mau_sac_chi_thi, ly_do_huy, duong_dan_anh_online
            FROM lich_su_van_hanh
            WHERE DATE(thoi_gian) = %s
            ORDER BY thoi_gian DESC
        """
        sessions = self.fetch_all(sql, (date_str,)) or []
        
        # Tối ưu: Lấy trước toàn bộ giao nhận hôm nay
        nhan_map = {}
        sql_nhan1 = "SELECT bo_id as id_goc, 'BO' as loai_goc, thoi_gian, khoa, nguoi_nhan as nhan_vien FROM lich_su_giao_nhan WHERE DATE(thoi_gian) = %s AND bo_id IS NOT NULL"
        sql_nhan2 = "SELECT dung_cu_id as id_goc, 'DONG_LE' as loai_goc, thoi_gian, khoa, nguoi_nhan as nhan_vien FROM lich_su_giao_nhan WHERE DATE(thoi_gian) = %s AND dung_cu_id IS NOT NULL"
        sql_nhan3 = "SELECT dung_cu_id as id_goc, 'THU_THUAT' as loai_goc, gio_giao as thoi_gian, khoa, nguoi_nhan as nhan_vien FROM lich_su_giao_nhan_thu_thuat WHERE DATE(gio_giao) = %s"
        
        for c in (self.fetch_all(sql_nhan1, (date_str,)) or []):
            key = (c['id_goc'], c['loai_goc'])
            if key not in nhan_map: nhan_map[key] = []
            nhan_map[key].append({"thoi_gian": c['thoi_gian'].strftime('%d/%m/%Y %H:%M:%S') if c['thoi_gian'] else "", "dt": c['thoi_gian'], "khoa": c['khoa'], "nhan_vien": c['nhan_vien']})
        for c in (self.fetch_all(sql_nhan2, (date_str,)) or []):
            key = (c['id_goc'], c['loai_goc'])
            if key not in nhan_map: nhan_map[key] = []
            nhan_map[key].append({"thoi_gian": c['thoi_gian'].strftime('%d/%m/%Y %H:%M:%S') if c['thoi_gian'] else "", "dt": c['thoi_gian'], "khoa": c['khoa'], "nhan_vien": c['nhan_vien']})
        for c in (self.fetch_all(sql_nhan3, (date_str,)) or []):
            key = (c['id_goc'], c['loai_goc'])
            if key not in nhan_map: nhan_map[key] = []
            nhan_map[key].append({"thoi_gian": c['thoi_gian'].strftime('%d/%m/%Y %H:%M:%S') if c['thoi_gian'] else "", "dt": c['thoi_gian'], "khoa": c['khoa'], "nhan_vien": c['nhan_vien']})
            
        for k in nhan_map: nhan_map[k].sort(key=lambda x: x['dt'])
            
        _, cap_map = self._get_bulk_trace(date_str)
        
        for s in sessions:
            hap_dt = s['thoi_gian']
            hap = {"thoi_gian": hap_dt.strftime('%d/%m/%Y %H:%M:%S') if hap_dt else "", "ten_may": s['ten_may'], "nhan_vien": s['nhan_vien']}
            if s['thoi_gian']:
                s['thoi_gian'] = s['thoi_gian'].strftime('%d/%m/%Y %H:%M:%S')
            
            sql_details = """
                SELECT c.id_goc, c.loai_goc, c.ten_dung_cu as ten, c.so_luong, c.khoa
                FROM chi_tiet_chu_trinh_van_hanh c
                WHERE c.ma_phien_van_hanh = %s
            """
            details = self.fetch_all(sql_details, (s['ma_phien'],)) or []
            for d in details:
                lg = 'THU_THUAT' if 'THU_THUAT' in str(d['loai_goc']).upper() else ('BO' if 'BO' in str(d['loai_goc']).upper() or 'BỘ' in str(d['loai_goc']).upper() else 'DONG_LE')
                key = (d['id_goc'], lg)
                
                # Find last nhan BEFORE or EQUAL to hap
                nhan = None
                for n in reversed(nhan_map.get(key, [])):
                    if n['dt'] <= hap_dt:
                        nhan = n
                        break
                        
                # Find first cap AFTER or EQUAL to hap
                cap = None
                for c in cap_map.get(key, []):
                    if c['dt'] >= hap_dt:
                        cap = c
                        break
                        
                d['trace'] = {"nhan": nhan, "hap": hap, "cap": cap}
            s['details'] = details
        return sessions

    def get_kpi_clean_inventory_drilldown(self):
        sql = """
            SELECT ct.loai_goc, ct.id_goc, ct.ten_dung_cu as ten, ct.khoa, 
                   (SUM(ct.so_luong) - IFNULL(T_DIST.total_distributed, 0)) as so_luong
            FROM chi_tiet_chu_trinh_van_hanh ct 
            JOIN lich_su_van_hanh ls ON ct.ma_phien_van_hanh = ls.ma_phien
            LEFT JOIN (
                SELECT CASE WHEN bo_id IS NOT NULL THEN bo_id ELSE dung_cu_id END as id_goc,
                       CASE WHEN bo_id IS NOT NULL THEN 'bo_dung_cu' ELSE 'do_dong_le' END as loai_goc,
                       SUM(so_luong) as total_distributed 
                FROM lich_su_cap_phat WHERE IFNULL(loai_phieu, 'CAP_PHAT') IN ('CAP_PHAT', 'RESET_SACH')
                GROUP BY id_goc, loai_goc
            ) T_DIST ON ct.id_goc = T_DIST.id_goc AND ct.loai_goc = T_DIST.loai_goc
            WHERE ls.trang_thai = 'COMPLETED' 
            GROUP BY ct.loai_goc, ct.id_goc, ct.ten_dung_cu, ct.khoa, T_DIST.total_distributed
            HAVING so_luong > 0
        """
        bos = self.fetch_all(sql) or []
        for item in bos:
            item['trace'] = self.get_universal_traceability(item['id_goc'], item['loai_goc'])
        return bos

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
