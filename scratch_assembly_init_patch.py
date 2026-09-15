import sys

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\views\assembly.py', 'r', encoding='utf-8') as f:
    c = f.read()

import re
c = re.sub(r'self\.user_fullname = self\.user_data\.get\("ho_ten", self\.user_fullname\)', 'self.user_fullname = self.user_data.get("ho_ten", "NV KSNK")', c)
# also super().__init__() needs to be first
c = re.sub(r'    def __init__\(self, user_data=None\):\n        self\.user_data = user_data or \{\}\n        self\.user_fullname = self\.user_data\.get\("ho_ten", "NV KSNK"\)\n        super\(\)\.__init__\(\)', '    def __init__(self, user_data=None):\n        super().__init__()\n        self.user_data = user_data or {}\n        self.user_fullname = self.user_data.get("ho_ten", "NV KSNK")', c)

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\views\assembly.py', 'w', encoding='utf-8') as f:
    f.write(c)
