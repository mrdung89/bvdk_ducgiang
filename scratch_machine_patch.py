import sys

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\models\db_manager.py', 'r', encoding='utf-8') as f:
    c = f.read()

import re

new_method = '''    def get_realtime_machines(self):
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
        
    def get_universal_traceability'''

# Find get_universal_traceability and insert get_realtime_machines before it
# Actually get_universal_traceability doesn't exist anymore!
# I will just insert get_realtime_machines at the end of the file, before the last `def ` or just anywhere in the class.
c = c.replace('    def get_traceability_timeline', new_method.replace('    def get_universal_traceability', '    def get_traceability_timeline'))

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\models\db_manager.py', 'w', encoding='utf-8') as f:
    f.write(c)
