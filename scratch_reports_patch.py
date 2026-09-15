import sys

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\views\reports.py', 'r', encoding='utf-8') as f:
    c = f.read()

new_do_trace = '''    def do_trace(self):
        keyword = self.txt_search.text().strip()
        if not keyword: return
        
        # Bóc tách ID nếu chuỗi có dạng "ID:123, KHOA:..., LOAI:..."
        if keyword.startswith("ID:"):
            parts = keyword.split(",")
            keyword = parts[0].replace("ID:", "").strip()
            
        search_type = self.cb_search_type.currentText()'''

import re
c = re.sub(r'    def do_trace\(self\):\s*keyword = self\.txt_search\.text\(\)\.strip\(\)\s*if not keyword: return\s*search_type = self\.cb_search_type\.currentText\(\)', new_do_trace, c, flags=re.MULTILINE)

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\views\reports.py', 'w', encoding='utf-8') as f:
    f.write(c)
