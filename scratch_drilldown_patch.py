import sys

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\models\db_manager.py', 'r', encoding='utf-8') as f:
    c = f.read()

import re

new_drilldowns = '''    def get_kpi_received_drilldown(self, date_str):
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
        return items'''

c = re.sub(r'    def get_kpi_received_drilldown\(self, date_str\):.*?return items', new_drilldowns, c, flags=re.DOTALL)

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\models\db_manager.py', 'w', encoding='utf-8') as f:
    f.write(c)
