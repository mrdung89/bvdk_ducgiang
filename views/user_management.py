from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, 
    QTableWidgetItem, QHeaderView, QMessageBox, QLabel
)
from PySide6.QtCore import Qt

class UserManagementWidget(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.init_ui()
        self.load_data()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QHBoxLayout()
        lbl = QLabel("Quản trị tài khoản nhân viên (Chỉ Admin)")
        lbl.setStyleSheet("font-size: 16px; font-weight: bold;")
        toolbar.addWidget(lbl)
        toolbar.addStretch()
        
        self.btn_refresh = QPushButton("Làm mới")
        self.btn_refresh.clicked.connect(self.load_data)
        toolbar.addWidget(self.btn_refresh)
        
        layout.addLayout(toolbar)
        
        # Table
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Username", "Họ Tên", "Role", "Trạng Thái"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)
        
        # Action Buttons
        actions = QHBoxLayout()
        
        self.btn_change_role = QPushButton("Đổi Quyền")
        self.btn_change_role.clicked.connect(self.change_role)
        actions.addWidget(self.btn_change_role)
        
        self.btn_toggle_status = QPushButton("Khóa / Mở Khóa")
        self.btn_toggle_status.clicked.connect(self.toggle_status)
        actions.addWidget(self.btn_toggle_status)
        
        self.btn_reset_pwd = QPushButton("Reset Mật Khẩu (123456)")
        self.btn_reset_pwd.clicked.connect(self.reset_password)
        actions.addWidget(self.btn_reset_pwd)
        
        actions.addStretch()
        layout.addLayout(actions)
        
    def load_data(self):
        self.table.setRowCount(0)
        rows = self.db.fetch_all("SELECT id, username, full_name, role, is_active FROM employees")
        if not rows: return
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            self.table.setItem(r, 0, QTableWidgetItem(str(row['id'])))
            self.table.setItem(r, 1, QTableWidgetItem(row['username']))
            self.table.setItem(r, 2, QTableWidgetItem(row['full_name']))
            self.table.setItem(r, 3, QTableWidgetItem(row['role']))
            status = "Hoạt động" if row.get('is_active', 1) else "Bị Khóa"
            self.table.setItem(r, 4, QTableWidgetItem(status))
            
    def get_selected_user_id(self):
        row = self.table.currentRow()
        if row < 0: return None
        return self.table.item(row, 0).text()
        
    def change_role(self):
        uid = self.get_selected_user_id()
        if not uid: return
        # Simple cycle: ADMIN -> LANH_DAO -> NV_KSNK -> KHOA_LAM_SANG -> ADMIN
        current_role = self.table.item(self.table.currentRow(), 3).text()
        roles = ['ADMIN', 'LANH_DAO', 'NV_KSNK', 'KHOA_LAM_SANG']
        try:
            nxt = roles[(roles.index(current_role) + 1) % len(roles)]
        except:
            nxt = 'NV_KSNK'
        self.db.execute("UPDATE employees SET role=%s WHERE id=%s", (nxt, uid))
        self.load_data()
        
    def toggle_status(self):
        uid = self.get_selected_user_id()
        if not uid: return
        current = self.table.item(self.table.currentRow(), 4).text()
        new_val = 0 if current == "Hoạt động" else 1
        self.db.execute("UPDATE employees SET is_active=%s WHERE id=%s", (new_val, uid))
        self.load_data()
        
    def reset_password(self):
        uid = self.get_selected_user_id()
        if not uid: return
        import hashlib
        h = hashlib.sha256("123456".encode()).hexdigest()
        self.db.execute("UPDATE employees SET password_hash=%s WHERE id=%s", (h, uid))
        QMessageBox.information(self, "Thành công", "Đã reset mật khẩu về 123456")
