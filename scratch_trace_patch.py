import sys

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\models\db_manager.py', 'r', encoding='utf-8') as f:
    c = f.read()

import re

new_trace = '''    def get_traceability_timeline(self, keyword):
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
        }'''

c = re.sub(r'    def get_traceability_timeline\(self, keyword\):.*?return trace', new_trace, c, flags=re.DOTALL)

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\models\db_manager.py', 'w', encoding='utf-8') as f:
    f.write(c)
