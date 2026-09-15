import sys

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\utils\printer.py', 'r', encoding='utf-8') as f:
    c = f.read()

new_printer_func = '''def print_assembly_label(parent_widget, ma_bo, ten_bo, nguoi_dong_goi="", pptk="", han_tiet_khuan_days=30):
    """In tem mã vạch/QR cho bộ dụng cụ với cài đặt tùy chỉnh."""
    import json
    import os
    from PySide6.QtPrintSupport import QPrinterInfo, QPrinter, QPrintDialog
    from PySide6.QtGui import QPainter, QImage, QFont, QPixmap
    from PySide6.QtCore import Qt
    import qrcode
    import io
    from datetime import datetime, timedelta
    
    cfg = {
        'printer_name': '',
        'width': 50, 'height': 30, 'qr_size': 18, 'qr_x': 2, 'qr_y': 5,
        'text_x': 22, 'ma_y': 5, 'ma_size': 10,
        'ten_y': 10, 'ten_size': 8,
        'pptk_y': 15, 'pptk_size': 8,
        'ntk_y': 20, 'ntk_size': 8,
        'hsd_y': 25, 'hsd_size': 8,
        'nv_y': 28, 'nv_size': 8
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
    
    # Check if we should bypass dialog
    target_printer_name = cfg.get('printer_name', '')
    
    printer = QPrinter(QPrinter.HighResolution)
    accepted = False
    
    if target_printer_name:
        for p in QPrinterInfo.availablePrinters():
            if p.printerName() == target_printer_name:
                printer.setPrinterName(target_printer_name)
                accepted = True
                break
                
    if not accepted:
        dialog = QPrintDialog(printer, parent_widget)
        if dialog.exec() == QPrintDialog.Accepted:
            accepted = True
            
    if accepted:
        painter = QPainter()
        painter.begin(printer)
        
        dpi_x = printer.logicalDpiX()
        dpi_y = printer.logicalDpiY()
        
        def mm_to_px(mm, dpi):
            return int((mm / 25.4) * dpi)
            
        qr_size_px = mm_to_px(cfg['qr_size'], dpi_x)
        qr_x_px = mm_to_px(cfg['qr_x'], dpi_x)
        qr_y_px = mm_to_px(cfg['qr_y'], dpi_y)
        painter.drawPixmap(qr_x_px, qr_y_px, qr_size_px, qr_size_px, qpixmap)
        
        text_x_px = mm_to_px(cfg['text_x'], dpi_x)
        
        def draw_txt(y_mm, size_mm, text, bold=False):
            font = QFont("Arial")
            font.setBold(bold)
            # Rough conversion for point size. DPI / 72 * point = px
            # Since we just want relative sizes, we can use point size directly:
            font.setPointSize(size_mm) 
            painter.setFont(font)
            painter.drawText(text_x_px, mm_to_px(y_mm, dpi_y), text)
            
        draw_txt(cfg['ma_y'], cfg['ma_size'], f"MÃ: {ma_bo}", True)
        draw_txt(cfg['ten_y'], cfg['ten_size'], f"TÊN: {ten_bo}")
        draw_txt(cfg['pptk_y'], cfg['pptk_size'], f"PPTK: {pptk}")
        
        now = datetime.now()
        draw_txt(cfg['ntk_y'], cfg['ntk_size'], f"NTK: {now.strftime('%d/%m/%y %H:%M')}")
        
        # Calculate HSD
        try: days = int(han_tiet_khuan_days)
        except: days = 30
        hsd_date = now + timedelta(days=days)
        draw_txt(cfg['hsd_y'], cfg['hsd_size'], f"HSD: {hsd_date.strftime('%d/%m/%y')}")
        
        draw_txt(cfg['nv_y'], cfg['nv_size'], f"NV: {nguoi_dong_goi}")
            
        painter.end()
        return True
    return False'''

start = c.find('def print_assembly_label')
end = c.find('def print_handover_receipt')
c = c[:start] + new_printer_func + '\n\n' + c[end:]

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\utils\printer.py', 'w', encoding='utf-8') as f:
    f.write(c)
