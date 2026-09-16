from models.db_manager import DBManager

class LoginController:
    def __init__(self, view):
        self.view = view
        self.db = DBManager()
        
        # Connect view signals to controller slots
        self.view.btn_login.clicked.connect(self.do_login)
        self.view.txt_pass.returnPressed.connect(self.do_login)
        self.view.register_requested.connect(self.show_register)

    def do_login(self):
        user = self.view.txt_user.text().strip()
        pwd = self.view.txt_pass.text().strip()
        
        if not user or not pwd:
            self.view.show_warning("Lỗi", "Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu!")
            return
            
        if not self.db.connect():
            self.view.show_error("Lỗi kết nối", "Không thể kết nối đến máy chủ CSDL XAMPP.")
            return
            
        user_data = self.db.authenticate(user, pwd)
        
        if user_data:
            if user_data.get('is_active', 1) == 0:
                self.view.show_warning("Tài khoản bị khóa", "Tài khoản của bạn đã bị khóa. Vui lòng liên hệ Admin.")
                return
            self.view.login_successful.emit(user_data)
        else:
            self.view.show_warning("Sai thông tin", "Tên đăng nhập hoặc mật khẩu không chính xác.")
            
    def show_register(self):
        # We pass the db instance for now so RegisterDialog still works,
        # but in a full MVC, RegisterDialog would have its own controller.
        self.view.show_register_dialog(self.db)
