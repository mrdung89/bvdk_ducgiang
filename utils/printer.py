from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from PySide6.QtGui import QPainter, QImage, QFont, QPixmap, QTextDocument
from PySide6.QtCore import Qt
import qrcode
from datetime import datetime
import io

def print_assembly_label(parent_widget, ma_bo, ten_bo, nguoi_dong_goi=""):
    """In tem mAc v!ch/QR cho bA' dM-ng cM- cA"ng cA!c thA#ng tin c?? bA#n."""
    # Generate QR Code image
    qr = qrcode.QRCode(version=1, box_size=10, border=1)
    qr.add_data(ma_bo)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert PIL Image to QPixmap
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
        
        # QR Code size ~ 1.5 inches
        qr_size = int(dpi_x * 1.5)
        painter.drawPixmap(0, 0, qr_size, qr_size, qpixmap)
        
        # Text layout
        font = QFont("Arial", 12, QFont.Bold)
        painter.setFont(font)
        x_text = qr_size + int(dpi_x * 0.2)
        y_text = int(dpi_y * 0.4)
        
        painter.drawText(x_text, y_text, f"Mã: {ma_bo}")
        
        font.setPointSize(10)
        font.setBold(False)
        painter.setFont(font)
        painter.drawText(x_text, y_text + int(dpi_y * 0.3), f"Tên: {ten_bo}")
        
        now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
        painter.drawText(x_text, y_text + int(dpi_y * 0.6), f"NSX: {now_str}")
        if nguoi_dong_goi:
            painter.drawText(x_text, y_text + int(dpi_y * 0.9), f"Người ĐG: {nguoi_dong_goi}")
        
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
