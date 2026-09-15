import sys
import json
import os

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\views\settings.py', 'r', encoding='utf-8') as f:
    c = f.read()

new_setup_print_tab = '''    def setup_print_tab(self):
        from PySide6.QtWidgets import QSpinBox, QGroupBox, QGridLayout, QComboBox
        from PySide6.QtGui import QPainter, QImage, QFont, QPixmap, QColor
        from PySide6.QtPrintSupport import QPrinterInfo
        import qrcode
        import io
        from datetime import datetime
        
        layout = QHBoxLayout(self.tab_print)
        
        # Left side: Form controls
        left_layout = QVBoxLayout()
        group = QGroupBox("Thông số Tem (mm)")
        grid = QGridLayout(group)
        
        self.print_cfg = {
            'printer_name': '',
            'width': 50, 'height': 30, 'qr_size': 18, 'qr_x': 2, 'qr_y': 5,
            'text_x': 22, 'ma_y': 5, 'ma_size': 10,
            'ten_y': 10, 'ten_size': 8,
            'pptk_y': 15, 'pptk_size': 8,
            'ntk_y': 20, 'ntk_size': 8,
            'hsd_y': 25, 'hsd_size': 8,
            'nv_y': 28, 'nv_size': 8
        }
        self.cfg_file = 'print_config.json'
        if __import__('os').path.exists(self.cfg_file):
            try:
                import json
                self.print_cfg.update(json.load(open(self.cfg_file)))
            except: pass
            
        row = 0
        grid.addWidget(QLabel("Máy in:"), row, 0)
        self.cb_printers = QComboBox()
        self.cb_printers.addItem("--- Chọn mỗi lần in ---", "")
        for pname in QPrinterInfo.availablePrinterNames():
            self.cb_printers.addItem(pname, pname)
        # set current
        idx = self.cb_printers.findData(self.print_cfg.get('printer_name', ''))
        if idx >= 0: self.cb_printers.setCurrentIndex(idx)
        grid.addWidget(self.cb_printers, row, 1)
        row += 1
            
        self.spinboxes = {}
        # Only spinboxes for numeric keys
        for key, val in self.print_cfg.items():
            if key == 'printer_name': continue
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
        from datetime import datetime, timedelta
        
        cfg = {k: v.value() for k, v in self.spinboxes.items()}
        
        scale = 8
        w_px = cfg['width'] * scale
        h_px = cfg['height'] * scale
        
        img = QImage(w_px, h_px, QImage.Format_RGB32)
        img.fill(QColor("white"))
        
        painter = QPainter(img)
        
        qr = qrcode.QRCode(version=1, box_size=10, border=1)
        qr.add_data("BO-TEST")
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        byte_array = io.BytesIO()
        qr_img.save(byte_array, format='PNG')
        qimg_qr = QImage.fromData(byte_array.getvalue())
        
        qr_size_px = cfg['qr_size'] * scale
        painter.drawImage(cfg['qr_x'] * scale, cfg['qr_y'] * scale, qimg_qr.scaled(qr_size_px, qr_size_px, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        
        x_px = cfg['text_x'] * scale
        
        def draw_txt(y_mm, size_mm, text, bold=False):
            font = QFont("Arial")
            font.setBold(bold)
            font.setPixelSize(int(size_mm * scale * 0.35))
            painter.setFont(font)
            painter.setPen(QColor("black"))
            painter.drawText(x_px, y_mm * scale, text)
            
        draw_txt(cfg['ma_y'], cfg['ma_size'], "MÃ: BO-TEST", True)
        draw_txt(cfg['ten_y'], cfg['ten_size'], "TÊN: Bộ Kéo Răng")
        draw_txt(cfg['pptk_y'], cfg['pptk_size'], "PPTK: STEAM")
        
        now = datetime.now()
        draw_txt(cfg['ntk_y'], cfg['ntk_size'], f"NTK: {now.strftime('%d/%m/%y %H:%M')}")
        draw_txt(cfg['hsd_y'], cfg['hsd_size'], f"HSD: {(now+timedelta(days=30)).strftime('%d/%m/%y')}")
        draw_txt(cfg['nv_y'], cfg['nv_size'], f"NV: Nguyễn Văn A")
        
        painter.end()
        self.lbl_preview.setPixmap(QPixmap.fromImage(img))

    def save_print_settings(self):
        import json
        cfg = {k: v.value() for k, v in self.spinboxes.items()}
        cfg['printer_name'] = self.cb_printers.currentData()
        try:
            with open(self.cfg_file, 'w') as f:
                json.dump(cfg, f, indent=4)
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Lưu xong", "Đã lưu cài đặt in tem!")
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Lỗi", f"Không thể lưu file: {e}")
'''

start_tab = c.find('    # -------- PRINT SETTINGS TAB --------')
if start_tab != -1:
    c = c[:start_tab] + new_setup_print_tab
else:
    print("Could not find start_tab")

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\views\settings.py', 'w', encoding='utf-8') as f:
    f.write(c)
