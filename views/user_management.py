import json
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                               QTableWidget, QTableWidgetItem, QHeaderView, QDialog, 
                               QFormLayout, QCheckBox, QMessageBox)
from PySide6.QtCore import Qt

class UserEditDialog(QDialog):
    def __init__(self, user_data, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.setWindowTitle(f"Phân quyền: {user_data['full_name']} ({user_data['username']})")
        self.resize(400, 500)
        
        layout = QVBoxLayout(self)
        self.form = QFormLayout()
        
        # 1. Trạng thái chung
        self.chk_active = QCheckBox("Hoạt động (Cho phép đăng nhập)")
        self.chk_active.setChecked(bool(user_data.get('is_active', 1)))
        self.form.addRow(self.chk_active)
        
        self.chk_can_send = QCheckBox("Cho phép tạo phiếu GỬI ĐỒ DƠ")
        self.chk_can_send.setChecked(bool(user_data.get('can_send', 1)))
        
        # Dictionary lưu các checkbox màn hình (chỉ cho KSNK)
        self.screen_chks = {}
        
        role = user_data.get('role', '')
        if role == 'KHOA_LAM_SANG':
            self.form.addRow("Quyền Khoa L.Sàng:", self.chk_can_send)
        else:
            # NV_KSNK hoặc ADMIN -> Phân quyền màn hình
            lbl = QLabel("Tích chọn các màn hình được phép truy cập:")
            lbl.setStyleSheet("font-weight: bold; margin-top: 10px;")
            self.form.addRow(lbl)
            
            screens = {
                "dashboard": "Tổng quan (Dashboard)",
                "receive": "Giao Nhận",
                "decon": "Khử nhiễm",
                "assembly": "Đóng gói",
                "sterilize": "Tiệt khuẩn",
                "issue": "Cấp Phát",
                "reports": "Báo cáo",
                "inventory": "Kho & Nhập",
                "masterdata": "Danh Mục (Master Data)",
                "management": "Quản lý hệ thống",
                "settings": "Cài đặt"
            }
            
            # Load current perms
            current_perms = {}
            perms_str = user_data.get('screen_permissions')
            if perms_str and perms_str != 'ALL':
                try: current_perms = json.loads(perms_str)
                except: pass
            else:
                current_perms = {k: True for k in screens.keys()} # Mặc định ALL nếu trống
                
            for key, label in screens.items():
                chk = QCheckBox(label)
                chk.setChecked(bool(current_perms.get(key, False)))
                self.screen_chks[key] = chk
                self.form.addRow("", chk)
                
        layout.addLayout(self.form)
        
        # Buttons
        hl = QHBoxLayout()
        btn_save = QPushButton("LƯU PHÂN QUYỀN")
        btn_save.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        btn_save.clicked.connect(self.accept)
        btn_cancel = QPushButton("Hủy")
        btn_cancel.clicked.connect(self.reject)
        
        hl.addStretch()
        hl.addWidget(btn_save)
        hl.addWidget(btn_cancel)
        layout.addLayout(hl)

    def get_data(self):
        is_active = 1 if self.chk_active.isChecked() else 0
        can_send = 1 if self.chk_can_send.isChecked() else 0
        
        perms_json = 'ALL'
        if self.screen_chks:
            perms_dict = {key: chk.isChecked() for key, chk in self.screen_chks.items()}
            perms_json = json.dumps(perms_dict)
            
        return is_active, can_send, perms_json


class UserManagementWidget(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        
        layout = QVBoxLayout(self)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["ID", "Tên Đăng Nhập", "Họ Tên", "Khoa / Vai Trò", "Trạng Thái", "Thao Tác"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        layout.addWidget(self.table)
        
        self.load_users()

    def load_users(self):
        self.table.setRowCount(0)
        users = self.db.get_all_users()
        if not users: return
        
        self.table.setRowCount(len(users))
        for r, u in enumerate(users):
            self.table.setItem(r, 0, QTableWidgetItem(str(u['id'])))
            self.table.setItem(r, 1, QTableWidgetItem(u['username']))
            self.table.setItem(r, 2, QTableWidgetItem(u['full_name']))
            
            khoa_role = u.get('ten_khoa', '') if u['role'] == 'KHOA_LAM_SANG' else u['role']
            self.table.setItem(r, 3, QTableWidgetItem(khoa_role or ''))
            
            status = "Hoạt động" if u.get('is_active', 1) else "BỊ KHÓA"
            if u['role'] == 'KHOA_LAM_SANG' and not u.get('can_send', 1):
                status += " (Cấm gửi đồ)"
            
            it_stt = QTableWidgetItem(status)
            if "KHÓA" in status or "Cấm" in status: it_stt.setForeground(Qt.red)
            self.table.setItem(r, 4, it_stt)
            
            btn_edit = QPushButton("⚙️ Phân Quyền")
            btn_edit.setStyleSheet("background-color: #3498db; color: white;")
            btn_edit.clicked.connect(lambda ch, user=u: self.edit_user(user))
            self.table.setCellWidget(r, 5, btn_edit)

    def edit_user(self, user):
        dlg = UserEditDialog(user, self)
        if dlg.exec():
            is_active, can_send, perms_json = dlg.get_data()
            if self.db.update_user_permissions(user['id'], is_active, can_send, perms_json):
                QMessageBox.information(self, "Thành công", f"Đã cập nhật quyền cho {user['username']}")
                self.load_users()
