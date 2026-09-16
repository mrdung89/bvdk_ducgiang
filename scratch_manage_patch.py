import sys

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\views\management.py', 'r', encoding='utf-8') as f:
    c = f.read()

import re

# Insert import
c = c.replace('from models.db_manager import DBManager', 'from models.db_manager import DBManager\nfrom views.user_management import UserManagementWidget')

# Add tab
new_tab = '''        self.tab_may = QWidget()
        self.tabs.addTab(self.tab_may, "Máy Móc")
        
        self.tab_users = UserManagementWidget(self.db)
        self.idx_users = self.tabs.addTab(self.tab_users, "Quản Lý User")
        
    def set_user_data(self, user_data):
        if user_data.get('role') != 'ADMIN':
            self.tabs.setTabVisible(self.idx_users, False)
        else:
            self.tabs.setTabVisible(self.idx_users, True)'''

c = re.sub(r'        self\.tab_may = QWidget\(\)\n        self\.tabs\.addTab\(self\.tab_may, "M[aAá]?y M[oOó]?c"\)', new_tab, c)

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\views\management.py', 'w', encoding='utf-8') as f:
    f.write(c)
