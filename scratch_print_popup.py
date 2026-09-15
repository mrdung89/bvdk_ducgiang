import sys
import json
import os

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\views\settings.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Remove the Print Tab from Settings
c = c.replace('''        # Tab 3: Print Settings
        self.tab_print = QWidget()
        self.setup_print_tab()
        self.tabs.addTab(self.tab_print, "Cài Đặt In Tem")''', '')

start_tab = c.find('    # -------- PRINT SETTINGS TAB --------')
if start_tab != -1:
    c = c[:start_tab]

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\views\settings.py', 'w', encoding='utf-8') as f:
    f.write(c)

print_dialog_code = '''from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QSpinBox, QGroupBox, QGridLayout, QComboBox, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QImage, QFont, QPixmap, QColor
from PySide6.QtPrintSupport import QPrinterInfo, QPrinter
import qrcode
import io
import json
import os
from datetime import datetime, timedelta

class PrintLabelDialog(QDialog):
    def __init__(self, parent, items_to_print):
        super().__init__(parent)
        self.setWindowTitle("In Tem Đóng Gói (Tùy chỉnh)")
        self.resize(800, 500)
        
        self.items_to_print = items_to_print
        self.cfg_file = 'print_config.json'
        
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
        
        if os.path.exists(self.cfg_file):
            try: self.print_cfg.update(json.load(open(self.cfg_file)))
            except: pass
            
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        
        # Left side: Form controls
        left_layout = QVBoxLayout()
        group = QGroupBox("Thông số Tem (mm)")
        grid = QGridLayout(group)
        
        row = 0
        grid.addWidget(QLabel("Máy in:"), row, 0)
        self.cb_printers = QComboBox()
        self.cb_printers.addItem("--- Chọn Máy In ---", "")
        for pname in QPrinterInfo.availablePrinterNames():
            self.cb_printers.addItem(pname, pname)
            
        idx = self.cb_printers.findData(self.print_cfg.get('printer_name', ''))
        if idx >= 0: self.cb_printers.setCurrentIndex(idx)
        self.cb_printers.currentIndexChanged.connect(self.save_settings)
        grid.addWidget(self.cb_printers, row, 1)
        row += 1
            
        self.spinboxes = {}
        for key, val in self.print_cfg.items():
            if key == 'printer_name': continue
            lbl = QLabel(key)
            spin = QSpinBox()
            spin.setRange(1, 200)
            spin.setValue(val)
            spin.valueChanged.connect(self.update_preview_and_save)
            self.spinboxes[key] = spin
            grid.addWidget(lbl, row, 0)
            grid.addWidget(spin, row, 1)
            row += 1
            
        left_layout.addWidget(group)
        left_layout.addStretch()
        
        # Right side: Preview
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("<b>Xem trước Tem (Demo món đầu tiên):</b>"))
        self.lbl_preview = QLabel()
        self.lbl_preview.setStyleSheet("background-color: white; border: 1px solid black;")
        self.lbl_preview.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.lbl_preview)
        
        right_layout.addStretch()
        
        btn_print = QPushButton(f"🖨 IN {len(self.items_to_print)} TEM NGAY")
        btn_print.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; font-size: 16px; padding: 15px;")
        btn_print.clicked.connect(self.do_print)
        right_layout.addWidget(btn_print)
        
        layout.addLayout(left_layout, 1)
        layout.addLayout(right_layout, 2)
        
        self.update_preview_and_save()

    def update_preview_and_save(self):
        cfg = {k: v.value() for k, v in self.spinboxes.items()}
        cfg['printer_name'] = self.cb_printers.currentData()
        self.print_cfg = cfg
        
        # Save implicitly
        try:
            with open(self.cfg_file, 'w') as f:
                json.dump(cfg, f, indent=4)
        except: pass
        
        # Draw Preview
        scale = 8
        w_px = cfg['width'] * scale
        h_px = cfg['height'] * scale
        
        img = QImage(w_px, h_px, QImage.Format_RGB32)
        img.fill(QColor("white"))
        painter = QPainter(img)
        
        # Use first item for demo
        demo_item = self.items_to_print[0] if self.items_to_print else {}
        ma_do = demo_item.get('ma_do', 'BO-TEST')
        ten_do = demo_item.get('ten_do', 'Tên đồ test')
        pptk = demo_item.get('pptk', 'STEAM')
        hsd_days = demo_item.get('han_tiet_khuan', 30)
        nv = demo_item.get('nguoi_dong_goi', 'NV A')
        
        qr = qrcode.QRCode(version=1, box_size=10, border=1)
        qr.add_data(ma_do)
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
            
        draw_txt(cfg['ma_y'], cfg['ma_size'], f"MÃ: {ma_do}", True)
        draw_txt(cfg['ten_y'], cfg['ten_size'], f"TÊN: {ten_do}")
        draw_txt(cfg['pptk_y'], cfg['pptk_size'], f"PPTK: {pptk}")
        
        now = datetime.now()
        draw_txt(cfg['ntk_y'], cfg['ntk_size'], f"NTK: {now.strftime('%d/%m/%y %H:%M')}")
        draw_txt(cfg['hsd_y'], cfg['hsd_size'], f"HSD: {(now+timedelta(days=hsd_days)).strftime('%d/%m/%y')}")
        draw_txt(cfg['nv_y'], cfg['nv_size'], f"NV: {nv}")
        
        painter.end()
        self.lbl_preview.setPixmap(QPixmap.fromImage(img))
        
    def save_settings(self):
        self.update_preview_and_save()

    def do_print(self):
        target = self.cb_printers.currentData()
        if not target:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn máy in ở danh sách bên trái!")
            return
            
        printer = QPrinter(QPrinter.HighResolution)
        printer.setPrinterName(target)
        
        cfg = self.print_cfg
        
        try:
            for it in self.items_to_print:
                painter = QPainter()
                painter.begin(printer)
                
                dpi_x = printer.logicalDpiX()
                dpi_y = printer.logicalDpiY()
                
                def mm_to_px(mm, dpi):
                    return int((mm / 25.4) * dpi)
                    
                ma_do = it.get('ma_do', '')
                qr = qrcode.QRCode(version=1, box_size=10, border=1)
                qr.add_data(ma_do)
                qr.make(fit=True)
                qr_img = qr.make_image(fill_color="black", back_color="white")
                byte_array = io.BytesIO()
                qr_img.save(byte_array, format='PNG')
                qimg_qr = QImage.fromData(byte_array.getvalue())
                qpixmap = QPixmap.fromImage(qimg_qr)
                
                qr_size_px = mm_to_px(cfg['qr_size'], dpi_x)
                qr_x_px = mm_to_px(cfg['qr_x'], dpi_x)
                qr_y_px = mm_to_px(cfg['qr_y'], dpi_y)
                painter.drawPixmap(qr_x_px, qr_y_px, qr_size_px, qr_size_px, qpixmap)
                
                text_x_px = mm_to_px(cfg['text_x'], dpi_x)
                
                def draw_txt(y_mm, size_mm, text, bold=False):
                    font = QFont("Arial")
                    font.setBold(bold)
                    font.setPointSize(size_mm)
                    painter.setFont(font)
                    painter.drawText(text_x_px, mm_to_px(y_mm, dpi_y), text)
                    
                draw_txt(cfg['ma_y'], cfg['ma_size'], f"MÃ: {ma_do}", True)
                draw_txt(cfg['ten_y'], cfg['ten_size'], f"TÊN: {it.get('ten_do','')}")
                draw_txt(cfg['pptk_y'], cfg['pptk_size'], f"PPTK: {it.get('pptk','')}")
                
                now = datetime.now()
                draw_txt(cfg['ntk_y'], cfg['ntk_size'], f"NTK: {now.strftime('%d/%m/%y %H:%M')}")
                hsd_days = it.get('han_tiet_khuan', 30)
                draw_txt(cfg['hsd_y'], cfg['hsd_size'], f"HSD: {(now+timedelta(days=hsd_days)).strftime('%d/%m/%y')}")
                draw_txt(cfg['nv_y'], cfg['nv_size'], f"NV: {it.get('nguoi_dong_goi','')}")
                
                painter.end()
            
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi in", f"Lỗi: {e}")
'''

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\views\print_dialog.py', 'w', encoding='utf-8') as f:
    f.write(print_dialog_code)

# Now modify assembly.py to open this dialog
with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\views\assembly.py', 'r', encoding='utf-8') as f:
    c = f.read()

new_do_pack = '''    def do_pack(self):
        selected_items = []
        for i in range(self.tree.topLevelItemCount()):
            parent = self.tree.topLevelItem(i)
            for j in range(parent.childCount()):
                child = parent.child(j)
                if child.checkState(0) == Qt.Checked:
                    pid = child.data(0, Qt.UserRole)
                    selected_items.append({'id': pid, 'ma_do': child.text(0), 'ten_do': child.text(1)})
                    
        if not selected_items:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng tích chọn ít nhất 1 món đồ để đóng gói & in tem!")
            return
            
        # Fetch DB attributes for printing
        for it in selected_items:
            ma = it['ma_do']
            is_digit = str(ma).isdigit()
            pptk = "STEAM"
            han_tiet_khuan = 30
            try:
                q1 = "SELECT phuong_phap_tiet_khuan, han_tiet_khuan FROM danh_muc_bo_dung_cu WHERE ma_bo=%s" + (" OR id=%s" if is_digit else "")
                p1 = (ma, ma) if is_digit else (ma,)
                res1 = self.db.fetch_one(q1, p1)
                if res1:
                    pptk = res1.get('phuong_phap_tiet_khuan') or "STEAM"
                    han_tiet_khuan = res1.get('han_tiet_khuan') or 30
                else:
                    q2 = "SELECT han_tiet_khuan FROM danh_muc_do_vai WHERE ma_do_vai=%s" + (" OR id=%s" if is_digit else "")
                    p2 = (ma, ma) if is_digit else (ma,)
                    res2 = self.db.fetch_one(q2, p2)
                    if res2:
                        han_tiet_khuan = res2.get('han_tiet_khuan') or 30
                    else:
                        q3 = "SELECT phuong_phap_tiet_khuan, han_tiet_khuan FROM danh_muc_dung_cu WHERE ma_dc=%s" + (" OR id=%s" if is_digit else "")
                        p3 = (ma, ma) if is_digit else (ma,)
                        res3 = self.db.fetch_one(q3, p3)
                        if res3:
                            pptk = res3.get('phuong_phap_tiet_khuan') or "STEAM"
                            han_tiet_khuan = res3.get('han_tiet_khuan') or 30
            except: pass
            it['pptk'] = pptk
            it['han_tiet_khuan'] = han_tiet_khuan
            it['nguoi_dong_goi'] = "NV KSNK" # Có thể lấy từ phiên đăng nhập sau
            
        from views.print_dialog import PrintLabelDialog
        dlg = PrintLabelDialog(self, selected_items)
        if dlg.exec():
            # In thành công -> Đổi trạng thái
            success_count = 0
            for it in selected_items:
                try:
                    self.db.execute("UPDATE lich_su_giao_nhan SET trang_thai='DA_DONG_GOI' WHERE id=%s", (it['id'],))
                    success_count += 1
                except: pass
            QMessageBox.information(self, "Thành công", f"Đã in tem và chuyển trạng thái cho {success_count} đồ!")
            self.load_items()
'''
start = c.find('    def do_pack(self):')
c = c[:start] + new_do_pack

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\views\assembly.py', 'w', encoding='utf-8') as f:
    f.write(c)
