import sys

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\views\distribution.py', 'r', encoding='utf-8') as f:
    c = f.read()

import re

new_grouping = '''            # Group by Khoa -> Loại -> Items
            tree_data = {}
            for row in reqs:
                khoa_goc = row['khoa_giao']
                tg = row['thoi_gian']
                
                if hasattr(tg, 'strftime'):
                    tg_str = tg.strftime('%H:%M %d/%m')
                else:
                    tg_str = str(tg)[:16]
                    
                khoa = f"{khoa_goc} - {tg_str}"
                
                ma_do = row['ma_do']
                if ma_do in dict_vai: loai = "Đồ Vải"
                elif ma_do in dict_bo: loai = "Bộ Dụng Cụ"
                elif ma_do in dict_le: loai = "Dụng Cụ Lẻ"
                else: loai = "Khác"
                
                if khoa not in tree_data:
                    tree_data[khoa] = {}
                if loai not in tree_data[khoa]:
                    tree_data[khoa][loai] = []
                tree_data[khoa][loai].append(row)'''

c = re.sub(r'            # Group by Khoa -> Loại -> Items\n            tree_data = \{\}\n            for row in reqs:\n                khoa = row\[\'khoa_giao\'\]\n.*?tree_data\[khoa\]\[loai\]\.append\(row\)', new_grouping, c, flags=re.DOTALL)

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\views\distribution.py', 'w', encoding='utf-8') as f:
    f.write(c)
