import sys

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\views\assembly.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Make it editable
c = c.replace('self.cb_h.addItems(["", "7", "30", "90", "180"])', 'self.cb_h.setEditable(True)\n        self.cb_h.addItems(["", "7", "30", "90", "180"])')

# Fix do_print to read self.cb_h
new_logic = '''    def do_print(self, item_id, is_le, t, k_ten, h_db, pp_db, n):
        if n <= 0: return
        today = datetime.today()
        user_h = self.cb_h.currentText().strip()
        han_days = user_h if user_h.isdigit() else (h_db if str(h_db).isdigit() else 30)
        han = today + timedelta(days=int(han_days))'''

import re
c = re.sub(r'    def do_print.*?han = today \+ timedelta\(days=int\(han_days\)\)', new_logic, c, flags=re.DOTALL)

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\views\assembly.py', 'w', encoding='utf-8') as f:
    f.write(c)
