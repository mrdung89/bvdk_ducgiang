import sys

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\models\db_manager.py', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace(
    'return self.fetch_all("SELECT * FROM lich_su_giao_nhan WHERE trang_thai=\'CHO_TIEP_NHAN\'")',
    'return self.fetch_all("SELECT * FROM lich_su_giao_nhan WHERE trang_thai=\'CHO_TIEP_NHAN\' ORDER BY thoi_gian DESC, id DESC")'
)

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\models\db_manager.py', 'w', encoding='utf-8') as f:
    f.write(c)
