import sys

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\controllers\login_controller.py', 'r', encoding='utf-8') as f:
    c = f.read()

import re

new_auth = '''        user_data = self.db.authenticate(user, pwd)
        
        if user_data:
            if user_data.get('is_active', 1) == 0:
                self.view.show_warning("Tài khoản bị khóa", "Tài khoản của bạn đã bị khóa. Vui lòng liên hệ Admin.")
                return
            self.view.login_successful.emit(user_data)
        else:
            self.view.show_warning("Sai thông tin", "Tên đăng nhập hoặc mật khẩu không chính xác.")'''

c = re.sub(r'        user_data = self\.db\.authenticate\(user, pwd\)\s*if user_data:.*?Tên đăng nhập hoặc mật khẩu không chính xác."\)', new_auth, c, flags=re.DOTALL)

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\controllers\login_controller.py', 'w', encoding='utf-8') as f:
    f.write(c)
