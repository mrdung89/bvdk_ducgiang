import sys

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\views\assembly.py', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace('khoa_nhan', 'khoa_giao')

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\views\assembly.py', 'w', encoding='utf-8') as f:
    f.write(c)
