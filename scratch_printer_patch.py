import sys
import json
import os

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\utils\printer.py', 'r', encoding='utf-8') as f:
    c = f.read()

new_printer_func = '''def print_assembly_label(parent_widget, ma_bo, ten_bo, nguoi_dong_goi=""):
    """In tem mã vạch/QR cho bộ dụng cụ với cài đặt tùy chỉnh."""
    import json
    import os
    cfg = {
        'width': 50, 'height': 30, 'qr_size': 20, 'qr_x': 2, 'qr_y': 5,
        'text_x': 25, 'ma_y': 8, 'ma_size': 12,
        'ten_y': 15, 'ten_size': 10,
        'nsx_y': 22, 'nsx_size': 8
    }
    if os.path.exists('print_config.json'):
        try: cfg.update(json.load(open('print_config.json')))
        except: pass
        
    qr = qrcode.QRCode(version=1, box_size=10, border=1)
    qr.add_data(ma_bo)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    byte_array = io.BytesIO()
    img.save(byte_array, format='PNG')
    qimg = QImage.fromData(byte_array.getvalue())
    qpixmap = QPixmap.fromImage(qimg)
    
    printer = QPrinter(QPrinter.HighResolution)
    dialog = QPrintDialog(printer, parent_widget)
    if dialog.exec() == QPrintDialog.Accepted:
        painter = QPainter()
        painter.begin(printer)
        
        dpi_x = printer.logicalDpiX()
        dpi_y = printer.logicalDpiY()
        
        # Hàm chuyển đổi mm sang pixels trên giấy in
        def mm_to_px(mm, dpi):
            return int((mm / 25.4) * dpi)
            
        qr_size_px = mm_to_px(cfg['qr_size'], dpi_x)
        qr_x_px = mm_to_px(cfg['qr_x'], dpi_x)
        qr_y_px = mm_to_px(cfg['qr_y'], dpi_y)
        painter.drawPixmap(qr_x_px, qr_y_px, qr_size_px, qr_size_px, qpixmap)
        
        text_x_px = mm_to_px(cfg['text_x'], dpi_x)
        
        # MÃ
        font = QFont("Arial", cfg['ma_size'])
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(text_x_px, mm_to_px(cfg['ma_y'], dpi_y), f"MÃ: {ma_bo}")
        
        # TÊN
        font.setPointSize(cfg['ten_size'])
        font.setBold(False)
        painter.setFont(font)
        painter.drawText(text_x_px, mm_to_px(cfg['ten_y'], dpi_y), f"TÊN: {ten_bo}")
        
        # NSX & NGƯỜI ĐÓNG GÓI
        font.setPointSize(cfg['nsx_size'])
        painter.setFont(font)
        now_str = datetime.now().strftime("%d/%m/%Y")
        painter.drawText(text_x_px, mm_to_px(cfg['nsx_y'], dpi_y), f"NSX: {now_str}")
        if nguoi_dong_goi:
            painter.drawText(text_x_px, mm_to_px(cfg['nsx_y'] + 5, dpi_y), f"NĐG: {nguoi_dong_goi}")
            
        painter.end()
        return True
    return False'''

start = c.find('def print_assembly_label')
end = c.find('def print_handover_receipt')
c = c[:start] + new_printer_func + '\n\n' + c[end:]

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\utils\printer.py', 'w', encoding='utf-8') as f:
    f.write(c)
