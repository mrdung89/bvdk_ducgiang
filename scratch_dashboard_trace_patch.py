import sys

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\controllers\dashboard_controller.py', 'r', encoding='utf-8') as f:
    c = f.read()

import re

c = c.replace(
    'SELECT loai_do, ma_do, so_luong, thoi_gian FROM lich_su_giao_nhan WHERE DATE(thoi_gian) = %s AND LOWER(khoa) LIKE %s',
    'SELECT ma_do, so_luong, thoi_gian FROM lich_su_giao_nhan WHERE DATE(thoi_gian) = %s AND LOWER(khoa_giao) LIKE %s'
)

c = c.replace(
    'f"- {row[\'loai_do\']} - {row[\'ma_do\']} (SL: {row[\'so_luong\']}) - {row[\'thoi_gian\']}\\n"',
    'f"- {row[\'ma_do\']} (SL: {row[\'so_luong\']}) - {row[\'thoi_gian\']}\\n"'
)

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\controllers\dashboard_controller.py', 'w', encoding='utf-8') as f:
    f.write(c)
