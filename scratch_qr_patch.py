import sys

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\utils\intem_backend.py', 'r', encoding='utf-8') as f:
    c = f.read()

new_qr_logic = '''    if type_code == 'bo':
        qr_content = str(item_id)
    elif type_code == 'LE':
        khoa_str = khoa_id if khoa_id else remove_vn_accents(str(ten_khoa)).strip()
        qr_content = f"ID:{item_id}, KHOA:{khoa_str}, LOAI:LE"
    elif type_code == 'thu_thuat':
        khoa_str = khoa_id if khoa_id else remove_vn_accents(str(ten_khoa)).strip()
        qr_content = f"ID:{item_id}, KHOA:{khoa_str}, LOAI:THU_THUAT"
    else:
        qr_content = str(item_id)'''

import re
c = re.sub(r"    if type_code == 'bo':.*?    else:\s+qr_content = str\(item_id\)", new_qr_logic, c, flags=re.DOTALL)

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\utils\intem_backend.py', 'w', encoding='utf-8') as f:
    f.write(c)
