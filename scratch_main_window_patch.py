import sys

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\controllers\main_window_controller.py', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace('self.page_assembly = AssemblyPage()', 'self.page_assembly = AssemblyPage(self.user_data)')

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\controllers\main_window_controller.py', 'w', encoding='utf-8') as f:
    f.write(c)
