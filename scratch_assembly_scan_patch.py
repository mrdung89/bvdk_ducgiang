import sys

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\views\assembly.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Add connection
c = c.replace('self.txt_search.setPlaceholderText("Gõ mã đồ để tìm nhanh...")', 'self.txt_search.setPlaceholderText("Quét mã hoặc gõ mã đồ rồi Enter...")\n        self.txt_search.returnPressed.connect(self.on_scan)')

new_on_scan = '''    def on_scan(self):
        qr = self.txt_search.text().strip()
        if not qr: return
        self.txt_search.clear()
        
        item_id = None
        khoa = ""
        loai = ""
        
        if qr.startswith("ID:"):
            parts = [p.strip() for p in qr.split(",")]
            for p in parts:
                if p.startswith("ID:"): item_id = p.replace("ID:", "").strip()
                elif p.startswith("KHOA:"): khoa = p.replace("KHOA:", "").strip()
                elif p.startswith("LOAI:"): loai = p.replace("LOAI:", "").strip()
        
        try:
            if loai == "LE" or loai == "THU_THUAT":
                res = self.db.fetch_one("SELECT ten_dc, COALESCE(han_tiet_khuan, 90) as h, COALESCE(phuong_phap_tiet_khuan, 'EO') as p FROM danh_muc_dung_cu WHERE id = %s", (item_id,))
                if res:
                    is_le = "thu_thuat" if loai == "THU_THUAT" else True
                    self.do_print(item_id, is_le, res['ten_dc'], khoa, res['h'], res['p'], 1)
                    return
            
            is_digit = str(qr).isdigit()
            if is_digit:
                # id = int -> bộ dụng cụ
                res = self.db.fetch_one("SELECT id, ten_bo, khoa_su_dung, COALESCE(han_tiet_khuan, 30) as h, COALESCE(phuong_phap_tiet_khuan, 'STEAM') as p FROM danh_muc_bo_dung_cu WHERE id=%s OR ma_bo=%s LIMIT 1", (qr, qr))
                if res:
                    self.do_print(res['id'], False, res['ten_bo'], res.get('khoa_su_dung', ''), res['h'], res['p'], 1)
                    return
                # Fallback cho đồ lẻ nếu không thấy bộ
                res2 = self.db.fetch_one("SELECT id, ten_dc as ten_bo, '' as khoa_su_dung, COALESCE(han_tiet_khuan, 90) as h, COALESCE(phuong_phap_tiet_khuan, 'EO') as p FROM danh_muc_dung_cu WHERE id=%s OR ma_dc=%s LIMIT 1", (qr, qr))
                if res2:
                    self.do_print(res2['id'], True, res2['ten_bo'], '', res2['h'], res2['p'], 1)
                    return
            else:
                # String -> Tìm tên bộ
                res = self.db.fetch_one("SELECT id, ten_bo, khoa_su_dung, COALESCE(han_tiet_khuan, 30) as h, COALESCE(phuong_phap_tiet_khuan, 'STEAM') as p FROM danh_muc_bo_dung_cu WHERE LOWER(ten_bo) = LOWER(%s) LIMIT 1", (qr,))
                if res:
                    self.do_print(res['id'], False, res['ten_bo'], res.get('khoa_su_dung', ''), res['h'], res['p'], 1)
                    return
                
            self.lbl_status.setText(f"Không tìm thấy dữ liệu cho mã: {qr}")
            
        except Exception as e:
            print("Lỗi quét QR:", e)

    def do_print(self,'''

c = c.replace('    def do_print(self,', new_on_scan)

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\views\assembly.py', 'w', encoding='utf-8') as f:
    f.write(c)
