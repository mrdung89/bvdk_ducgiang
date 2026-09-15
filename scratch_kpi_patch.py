import sys

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\models\db_manager.py', 'r', encoding='utf-8') as f:
    c = f.read()

import re

new_kpi = '''    def get_kpi_summary_v2(self, date_str):
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
            return {"nhan": 0, "cho_xu_ly": 0, "da_xu_ly": 0, "kho_sach": 0}'''

c = re.sub(r'    def get_kpi_summary_v2\(self, date_str\):.*?return \{"nhan": 0, "cho_xu_ly": 0, "da_xu_ly": 0, "kho_sach": 0\}', new_kpi, c, flags=re.DOTALL)

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\models\db_manager.py', 'w', encoding='utf-8') as f:
    f.write(c)
