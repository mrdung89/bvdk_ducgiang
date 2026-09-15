import sys

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\views\assembly.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Modify __init__
c = c.replace('    def __init__(self):', '    def __init__(self, user_data=None):\n        self.user_data = user_data or {}\n        self.user_fullname = self.user_data.get("ho_ten", "NV KSNK")')
c = c.replace("backend.CURRENT_USER_FULLNAME = 'NV KSNK'", 'backend.CURRENT_USER_FULLNAME = self.user_fullname')
c = c.replace('"NV KSNK"', 'self.user_fullname')

# Second issue: IN THỦ CÔNG
# Find "IN THỦ CÔNG" button and connect it
import re
match = re.search(r'btn_thu_cong = QPushButton\("IN THỦ CÔNG"\).*?fr_b\.addWidget\(btn_thu_cong\)', c, re.DOTALL)
if match:
    old_btn = match.group(0)
    new_btn = old_btn + '\n        btn_thu_cong.clicked.connect(self.show_manual_print)'
    c = c.replace(old_btn, new_btn)

# Add show_manual_print method
manual_method = '''    def show_manual_print(self):
        from PySide6.QtWidgets import QDialog
        class ManualPrintDialog(QDialog):
            def __init__(self, parent):
                super().__init__(parent)
                self.setWindowTitle("In Tem Thủ Công")
                self.resize(400, 300)
                layout = QVBoxLayout(self)
                
                layout.addWidget(QLabel("Tên dụng cụ/bộ:"))
                self.t_ten = QLineEdit()
                layout.addWidget(self.t_ten)
                
                layout.addWidget(QLabel("Khoa:"))
                self.t_khoa = QLineEdit()
                layout.addWidget(self.t_khoa)
                
                layout.addWidget(QLabel("Hạn (ngày):"))
                self.t_han = QSpinBox()
                self.t_han.setRange(1, 365)
                self.t_han.setValue(30)
                layout.addWidget(self.t_han)
                
                layout.addWidget(QLabel("Loại:"))
                self.cb_loai = QComboBox()
                self.cb_loai.addItems(["Bộ", "Đồ Lẻ", "Thủ thuật"])
                layout.addWidget(self.cb_loai)
                
                layout.addWidget(QLabel("Phương pháp:"))
                self.cb_pp = QComboBox()
                self.cb_pp.addItems(["STEAM", "EO", "PLASMA"])
                layout.addWidget(self.cb_pp)
                
                layout.addWidget(QLabel("Số lượng in:"))
                self.t_sl = QSpinBox()
                self.t_sl.setRange(1, 100)
                self.t_sl.setValue(1)
                layout.addWidget(self.t_sl)
                
                btn_in = QPushButton("IN NGAY")
                btn_in.setStyleSheet("background-color: #e67e22; color: white; font-weight: bold; padding: 10px;")
                btn_in.clicked.connect(self.accept)
                layout.addWidget(btn_in)

        dlg = ManualPrintDialog(self)
        if dlg.exec():
            ten = dlg.t_ten.text().strip()
            khoa = dlg.t_khoa.text().strip()
            han = dlg.t_han.value()
            loai = dlg.cb_loai.currentText()
            pp = dlg.cb_pp.currentText()
            sl = dlg.t_sl.value()
            
            if not ten:
                QMessageBox.warning(self, "Lỗi", "Vui lòng nhập tên đồ cần in!")
                return
                
            is_le = False
            if loai == "Đồ Lẻ": is_le = True
            elif loai == "Thủ thuật": is_le = "thu_thuat"
            
            # Use dummy ID for manual print
            item_id = "MANUAL"
            self.do_print(item_id, is_le, ten, khoa, han, pp, sl)'''

c = c + '\n' + manual_method + '\n'

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\views\assembly.py', 'w', encoding='utf-8') as f:
    f.write(c)
