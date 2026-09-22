from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QLabel, QLineEdit, QMessageBox, QDialog, QComboBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from models.db_manager import DBManager

class RegisterDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Đăng ký tài khoản")
        self.setFixedSize(400, 450)
        
        layout = QVBoxLayout(self)
        
        lbl_title = QLabel("ĐĂNG KÝ TÀI KHOẢN")
        lbl_title.setFont(QFont("Arial", 19, QFont.Bold))
        lbl_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_title)
        
        self.txt_full_name = QLineEdit()
        self.txt_full_name.setPlaceholderText("Họ và tên...")
        layout.addWidget(QLabel("Họ và tên:"))
        layout.addWidget(self.txt_full_name)
        
        self.txt_user = QLineEdit()
        self.txt_user.setPlaceholderText("Tên đăng nhập...")
        layout.addWidget(QLabel("Tên đăng nhập:"))
        layout.addWidget(self.txt_user)
        
        self.txt_pass = QLineEdit()
        self.txt_pass.setEchoMode(QLineEdit.Password)
        self.txt_pass.setPlaceholderText("Mật khẩu...")
        layout.addWidget(QLabel("Mật khẩu:"))
        layout.addWidget(self.txt_pass)
        
        self.cb_khoa = QComboBox()
        self.cb_khoa.setStyleSheet("padding: 5px; font-size: 14px;")
        layout.addWidget(QLabel("Khoa trực thuộc:"))
        layout.addWidget(self.cb_khoa)
        
        # Load Khoa
        self.khoa_list = []
        if self.db.connect():
            # Add KSNK as a virtual option (if not in db)
            self.cb_khoa.addItem("Khoa Kiểm Soát Nhiễm Khuẩn (CSSD)", -1)
            
            khoas = self.db.get_danh_muc_khoa()
            for k in khoas:
                self.cb_khoa.addItem(k['ten_khoa'], k['id'])
        
        btn_register = QPushButton("Đăng Ký")
        btn_register.setObjectName("PrimaryButton")
        btn_register.clicked.connect(self.do_register)
        layout.addSpacing(20)
        layout.addWidget(btn_register)
        
    def do_register(self):
        user = self.txt_user.text().strip()
        pwd = self.txt_pass.text().strip()
        name = self.txt_full_name.text().strip()
        khoa_id = self.cb_khoa.currentData()
        
        if not user or not pwd or not name:
            QMessageBox.warning(self, "Lỗi", "Vui lòng điền đủ thông tin!")
            return
            
        is_ksnk = (khoa_id == -1)
        k_id = None if is_ksnk else khoa_id
        
        success = self.db.register_user(user, pwd, name, k_id, is_ksnk)
        if success:
            QMessageBox.information(self, "Thành công", "Đăng ký thành công!\n(Quyền lãnh đạo khoa chỉ do Admin cấp riêng).")
            self.accept()
        else:
            QMessageBox.critical(self, "Lỗi", "Tên đăng nhập đã tồn tại hoặc có lỗi xảy ra.")

class LoginWindow(QWidget):
    login_successful = Signal(dict)
    register_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Đăng nhập - Quản lý CSSD")
        self.setFixedSize(400, 500)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        
        lbl_title = QLabel("CSSD MASTER")
        font_title = QFont()
        font_title.setPointSize(27)
        font_title.setBold(True)
        lbl_title.setFont(font_title)
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setStyleSheet("color: #2c3e50; margin-bottom: 30px;")
        layout.addWidget(lbl_title)
        
        lbl_user = QLabel("Tên đăng nhập:")
        self.txt_user = QLineEdit()
        self.txt_user.setPlaceholderText("Nhập tên đăng nhập...")
        layout.addWidget(lbl_user)
        layout.addWidget(self.txt_user)
        
        layout.addSpacing(10)
        
        lbl_pass = QLabel("Mật khẩu:")
        self.txt_pass = QLineEdit()
        self.txt_pass.setEchoMode(QLineEdit.Password)
        self.txt_pass.setPlaceholderText("Nhập mật khẩu...")
        layout.addWidget(lbl_pass)
        layout.addWidget(self.txt_pass)
        
        layout.addSpacing(30)
        
        self.btn_login = QPushButton(" Đăng Nhập")
        self.btn_login.setObjectName("PrimaryButton")
        layout.addWidget(self.btn_login)
        
        self.btn_register = QPushButton("Tạo tài khoản mới")
        self.btn_register.setStyleSheet("background-color: transparent; color: #3498db; text-decoration: underline; font-weight: normal;")
        self.btn_register.clicked.connect(self.register_requested.emit)
        layout.addWidget(self.btn_register)
        
        layout.addStretch()

    def show_warning(self, title, message):
        QMessageBox.warning(self, title, message)
        
    def show_error(self, title, message):
        QMessageBox.critical(self, title, message)

    def show_register_dialog(self, db):
        dlg = RegisterDialog(db, self)
        dlg.exec()
