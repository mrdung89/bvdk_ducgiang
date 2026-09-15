import sys

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\views\distribution.py', 'r', encoding='utf-8') as f:
    c = f.read()

import re
new_tree = '''        self.tree_multi.setHeaderLabels(["Khoa / Loại / Mã Đồ", "SL Dơ", "Tiếp Nhận", "Từ Chối"])
        self.tree_multi.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree_multi.setColumnWidth(1, 100)
        self.tree_multi.setColumnWidth(2, 200)
        self.tree_multi.setColumnWidth(3, 200)
        self.tree_multi.itemDoubleClicked.connect(self.show_receive_detail)'''

c = re.sub(r'        self\.tree_multi\.setHeaderLabels\(\["Khoa / Lo.i / M. .*", "SL D.", "Ti.p Nh.n", "T. Ch.i"\]\)\n        self\.tree_multi\.header\(\)\.setSectionResizeMode\(0, QHeaderView\.Stretch\)\n        self\.tree_multi\.itemDoubleClicked\.connect\(self\.show_receive_detail\)', new_tree, c)

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\views\distribution.py', 'w', encoding='utf-8') as f:
    f.write(c)
