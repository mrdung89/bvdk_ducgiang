import sys

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\controllers\main_window_controller.py', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace(
    'self.idx_management = self.view.content_area.indexOf(self.page_management)',
    'self.idx_management = self.view.content_area.indexOf(self.page_management)\n        if hasattr(self.page_management, "set_user_data"):\n            self.page_management.set_user_data(self.user_data)'
)

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\controllers\main_window_controller.py', 'w', encoding='utf-8') as f:
    f.write(c)
