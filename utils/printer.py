from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from PySide6.QtGui import QPainter, QImage, QFont, QPixmap, QTextDocument
from PySide6.QtCore import Qt
import qrcode
from datetime import datetime
import io

def print_assembly_label(parent_widget, ma_bo, ten_bo, nguoi_dong_goi=""):
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
    return False

def print_handover_receipt(parent_widget, ma_phien, khoa_giao, khoa_nhan, items, nguoi_lap_phieu=""):
    """In phi?Hu giao nhA-n (Receipt) ra mA!y in A4/A5."""
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; font-size: 14pt; }}
            h2 {{ text-align: center; margin-bottom: 5px; }}
            h3 {{ text-align: center; margin-top: 0px; color: #555; }}
            .info-table {{ width: 100%; margin-bottom: 20px; }}
            .item-table {{ width: 100%; border-collapse: collapse; }}
            .item-table th, .item-table td {{ border: 1px solid #000; padding: 8px; text-align: left; }}
            .item-table th {{ background-color: #f2f2f2; }}
            .footer-table {{ width: 100%; margin-top: 50px; text-align: center; }}
        </style>
    </head>
    <body>
        <h2>PHIẾU GIAO NHẬN ĐỒ VẢI / DỤNG CỤ</h2>
        <h3>Bệnh viện Đa khoa Đức Giang</h3>
        
        <table class="info-table">
            <tr>
                <td><b>Mã Phiếu:</b> {ma_phien}</td>
                <td style="text-align: right;"><b>Ngày lập:</b> {datetime.now().strftime("%d/%m/%Y %H:%M")}</td>
            </tr>
            <tr>
                <td><b>Bên Giao:</b> {khoa_giao}</td>
                <td style="text-align: right;"><b>Bên Nhận:</b> {khoa_nhan}</td>
            </tr>
        </table>
        
        <table class="item-table">
            <thead>
                <tr>
                    <th>STT</th>
                    <th>Mã Đồ</th>
                    <th>Tên Đồ</th>
                    <th>Số Lượng</th>
                </tr>
            </thead>
            <tbody>
    """
    
    total = 0
    for i, item in enumerate(items):
        ma = item.get('ma_do', '')
        ten = item.get('ten_do', '')
        sl = item.get('so_luong', 0)
        total += sl
        html += f"""
                <tr>
                    <td>{i+1}</td>
                    <td>{ma}</td>
                    <td>{ten}</td>
                    <td>{sl}</td>
                </tr>
        """
        
    html += f"""
            </tbody>
        </table>
        <p><b>Tổng cộng:</b> {total} (món/bộ)</p>
        
        <table class="footer-table">
            <tr>
                <td><b>Người Giao</b><br><br><br><br>____________________</td>
                <td><b>Người Nhận</b><br><br><br><br>____________________</td>
            </tr>
            <tr>
                <td colspan="2" style="padding-top: 30px; text-align: left; font-size: 12pt;"><i>Người lập phiếu: {nguoi_lap_phieu}</i></td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    printer = QPrinter(QPrinter.HighResolution)
    dialog = QPrintDialog(printer, parent_widget)
    if dialog.exec() == QPrintDialog.Accepted:
        doc = QTextDocument()
        doc.setHtml(html)
        doc.print_(printer)
        return True
    return False
