import sys
import json
import os

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\views\settings.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Add a 3rd tab
start_tabs = c.find('        # Tab 2: Mapping')
new_tab_init = '''        # Tab 2: Mapping
        self.tab_mapping = QWidget()
        self.setup_mapping_tab()
        self.tabs.addTab(self.tab_mapping, "Mapping Form -> Ma Do")

        # Tab 3: Print Settings
        self.tab_print = QWidget()
        self.setup_print_tab()
        self.tabs.addTab(self.tab_print, "Cài Đặt In Tem")
'''
if '# Tab 3: Print Settings' not in c:
    c = c.replace('''        # Tab 2: Mapping
        self.tab_mapping = QWidget()
        self.setup_mapping_tab()
        self.tabs.addTab(self.tab_mapping, "Mapping Form -> Ma Do")''', new_tab_init)

# Add setup_print_tab function
new_print_tab = '''
    # -------- PRINT SETTINGS TAB --------
    def setup_print_tab(self):
        from PySide6.QtWidgets import QSpinBox, QGroupBox, QGridLayout
        from PySide6.QtGui import QPainter, QImage, QFont, QPixmap, QColor
        import qrcode
        import io
        from datetime import datetime
        
        layout = QHBoxLayout(self.tab_print)
        
        # Left side: Form controls
        left_layout = QVBoxLayout()
        group = QGroupBox("Thông số căn chỉnh Tem (mm)")
        grid = QGridLayout(group)
        
        self.print_cfg = {
            'width': 50, 'height': 30, 'qr_size': 20, 'qr_x': 2, 'qr_y': 5,
            'text_x': 25, 'ma_y': 8, 'ma_size': 12,
            'ten_y': 15, 'ten_size': 10,
            'nsx_y': 22, 'nsx_size': 8
        }
        self.cfg_file = 'print_config.json'
        if __import__('os').path.exists(self.cfg_file):
            import json
            try:
                self.print_cfg.update(json.load(open(self.cfg_file)))
            except: pass
            
        self.spinboxes = {}
        row = 0
        for key, val in self.print_cfg.items():
            lbl = QLabel(key)
            spin = QSpinBox()
            spin.setRange(1, 200)
            spin.setValue(val)
            spin.valueChanged.connect(self.update_print_preview)
            self.spinboxes[key] = spin
            grid.addWidget(lbl, row, 0)
            grid.addWidget(spin, row, 1)
            row += 1
            
        btn_save = QPushButton("Lưu Cài Đặt In")
        btn_save.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        btn_save.clicked.connect(self.save_print_settings)
        grid.addWidget(btn_save, row, 0, 1, 2)
        
        left_layout.addWidget(group)
        left_layout.addStretch()
        
        # Right side: Preview
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("<b>Xem trước (Trực quan):</b>"))
        self.lbl_preview = QLabel()
        self.lbl_preview.setStyleSheet("background-color: white; border: 1px solid black;")
        self.lbl_preview.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.lbl_preview)
        right_layout.addStretch()
        
        layout.addLayout(left_layout, 1)
        layout.addLayout(right_layout, 2)
        
        self.update_print_preview()

    def update_print_preview(self):
        from PySide6.QtGui import QPainter, QImage, QFont, QPixmap, QColor
        from PySide6.QtCore import Qt
        import qrcode
        import io
        from datetime import datetime
        
        cfg = {k: v.value() for k, v in self.spinboxes.items()}
        
        # 1 mm ~ 3.78 pixels (at 96 DPI screen)
        # Let's scale up for preview (e.g., 1mm = 10 pixels for sharp preview)
        scale = 8
        w_px = cfg['width'] * scale
        h_px = cfg['height'] * scale
        
        img = QImage(w_px, h_px, QImage.Format_RGB32)
        img.fill(QColor("white"))
        
        painter = QPainter(img)
        
        # Draw QR
        qr = qrcode.QRCode(version=1, box_size=10, border=1)
        qr.add_data("BO-TEST")
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        byte_array = io.BytesIO()
        qr_img.save(byte_array, format='PNG')
        qimg_qr = QImage.fromData(byte_array.getvalue())
        
        qr_size_px = cfg['qr_size'] * scale
        painter.drawImage(cfg['qr_x'] * scale, cfg['qr_y'] * scale, qimg_qr.scaled(qr_size_px, qr_size_px, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        
        # Draw Text
        x_px = cfg['text_x'] * scale
        
        font = QFont("Arial", cfg['ma_size'])
        font.setBold(True)
        # Tweak pixel size for preview matching
        font.setPixelSize(int(cfg['ma_size'] * scale * 0.35)) 
        painter.setFont(font)
        painter.setPen(QColor("black"))
        painter.drawText(x_px, cfg['ma_y'] * scale, "MÃ: BO-TEST")
        
        font.setBold(False)
        font.setPixelSize(int(cfg['ten_size'] * scale * 0.35))
        painter.setFont(font)
        painter.drawText(x_px, cfg['ten_y'] * scale, "TÊN: Bộ Xét Nghiệm")
        
        font.setPixelSize(int(cfg['nsx_size'] * scale * 0.35))
        painter.setFont(font)
        now_str = datetime.now().strftime("%d/%m/%Y")
        painter.drawText(x_px, cfg['nsx_y'] * scale, f"NSX: {now_str}")
        
        painter.end()
        self.lbl_preview.setPixmap(QPixmap.fromImage(img))

    def save_print_settings(self):
        import json
        cfg = {k: v.value() for k, v in self.spinboxes.items()}
        try:
            with open(self.cfg_file, 'w') as f:
                json.dump(cfg, f, indent=4)
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Lưu xong", "Đã lưu cài đặt in tem!")
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Lỗi", f"Không thể lưu file: {e}")
'''
if 'def setup_print_tab' not in c:
    c += new_print_tab

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\views\settings.py', 'w', encoding='utf-8') as f:
    f.write(c)
