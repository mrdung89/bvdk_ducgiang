import sys

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\views\distribution.py', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace('FROM khoa_phong WHERE', 'FROM danh_muc_khoa WHERE')

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\views\distribution.py', 'w', encoding='utf-8') as f:
    f.write(c)
