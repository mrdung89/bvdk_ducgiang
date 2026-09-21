import os
import openpyxl
from datetime import datetime
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.worksheet.page import PageMargins
from openpyxl.drawing.image import Image as ExcelImage
import subprocess
import platform
from PySide6.QtWidgets import QMessageBox

# Cấu hình đường dẫn lưu trữ mặc định
BASE_REPORT_DIR = os.path.join(os.getcwd(), "BaoCao_Xuat")
LOGO_PATH = os.path.join(os.getcwd(), "assets", "logo.png") # Đảm bảo bạn có file logo này

class ExcelReporter:
    def __init__(self, parent_view=None):
        self.parent_view = parent_view
        
    def _get_safe_name(self, name):
        """Làm sạch chuỗi để làm tên file/thư mục an toàn trên mọi HĐH"""
        if not name: return "Unknown"
        return "".join([c for c in str(name) if c.isalnum() or c in (' ', '_', '-')]).strip()

    def _view_file(self, filepath):
        """Tự động mở file Excel sau khi tạo xong"""
        if not os.path.exists(filepath):
            if self.parent_view:
                QMessageBox.warning(self.parent_view, "Lỗi", "Không tìm thấy file để mở.")
            return

        try:
            if platform.system() == "Windows":
                os.startfile(filepath)
            elif platform.system() == "Darwin":
                subprocess.call(["open", filepath])
            else:
                subprocess.call(["xdg-open", filepath])
        except Exception as e:
            if self.parent_view:
                QMessageBox.warning(self.parent_view, "Lỗi mở file", str(e))

    def _setup_common_styles(self):
        """Khởi tạo các định dạng (font, border) dùng chung"""
        self.font_title = Font(name='Times New Roman', size=16, bold=True)
        self.font_header = Font(name='Times New Roman', size=12, bold=True)
        self.font_normal = Font(name='Times New Roman', size=11)
        self.border_thin = Border(
            left=Side(style='thin'), right=Side(style='thin'),
            top=Side(style='thin'), bottom=Side(style='thin')
        )
        self.align_center = Alignment(horizontal='center', vertical='center', wrap_text=True)
        self.align_left = Alignment(horizontal='left', vertical='center', wrap_text=True)

    # =====================================================================
    # MẪU 1: PHIẾU CẤP PHÁT (Dùng thay thế cho hàm export_issue_csv hiện tại)
    # Tương tự hàm create_receipt của BV Nhi
    # =====================================================================
    def create_distribution_receipt(self, khoa_nhan, ma_phieu, thoi_gian, data_list, nguoi_lap):
        self._setup_common_styles()
        
        # 1. Xử lý đường dẫn lưu
        safe_khoa = self._get_safe_name(khoa_nhan)
        safe_phieu = self._get_safe_name(ma_phieu)
        now = datetime.now()
        folder_path = os.path.join(BASE_REPORT_DIR, "CapPhat", safe_khoa, str(now.year), f"{now.month:02d}", f"{now.day:02d}")
        os.makedirs(folder_path, exist_ok=True)
        
        filepath = os.path.join(folder_path, f"{safe_phieu}.xlsx")
        
        # 2. Tạo Workbook
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = safe_phieu

        # 3. Cấu hình trang in (A5 dọc)
        ws.page_setup.paperSize = ws.PAPERSIZE_A5
        ws.page_setup.orientation = ws.ORIENTATION_PORTRAIT
        ws.sheet_properties.pageSetUpPr.fitToPage = True 
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0
        ws.page_margins = PageMargins(left=0.25, right=0.25, top=0.2, bottom=0.2)
        
        # 4. Tiêu đề & Logo
        if os.path.exists(LOGO_PATH):
            try:
                img = ExcelImage(LOGO_PATH)
                img.width, img.height = 60, 50
                ws.add_image(img, 'A1')
            except: pass

        ws.merge_cells('A1:E1'); ws['A1'] = "BỆNH VIỆN ĐA KHOA ĐỨC GIANG"
        ws['A1'].font = self.font_header; ws['A1'].alignment = self.align_center
        ws.merge_cells('A2:E2'); ws['A2'] = "KHOA KIỂM SOÁT NHIỄM KHUẨN"
        ws['A2'].font = self.font_header; ws['A2'].alignment = self.align_center
        
        ws.merge_cells('A4:E4'); ws['A4'] = "PHIẾU GIAO NHẬN / CẤP PHÁT ĐỒ SẠCH"
        ws['A4'].font = self.font_title; ws['A4'].alignment = self.align_center
        
        ws['A6'] = f"Khoa nhận: {khoa_nhan}"; ws['A6'].font = self.font_header
        ws.merge_cells('D6:E6'); ws['D6'] = f"Mã phiếu: {ma_phieu}"; ws['D6'].alignment = Alignment(horizontal='right')
        ws['A7'] = f"Thời gian: {thoi_gian}"; ws['A7'].font = Font(italic=True)

        # 5. Header Bảng
        headers = ["STT", "Mã Đồ", "Tên Đồ", "Số Lượng", "Ghi Chú"]
        widths = [5, 15, 30, 10, 15]
        start_row = 9
        for col_idx, header in enumerate(headers, 1):
            c = ws.cell(row=start_row, column=col_idx, value=header)
            c.font = self.font_header; c.border = self.border_thin; c.alignment = self.align_center
            c.fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
            ws.column_dimensions[openpyxl.utils.get_column_letter(col_idx)].width = widths[col_idx-1]

        # 6. Dữ liệu bảng
        current_row = start_row
        tong_sl = 0
        for i, item in enumerate(data_list, 1):
            current_row += 1
            ws.cell(row=current_row, column=1, value=i).border = self.border_thin
            ws.cell(row=current_row, column=1).alignment = self.align_center
            
            ws.cell(row=current_row, column=2, value=item.get('ma_do', '')).border = self.border_thin
            
            ws.cell(row=current_row, column=3, value=item.get('ten_do', '')).border = self.border_thin
            ws.cell(row=current_row, column=3).alignment = self.align_left
            
            sl = int(item.get('so_luong', 0))
            tong_sl += sl
            c_sl = ws.cell(row=current_row, column=4, value=sl)
            c_sl.border = self.border_thin; c_sl.font = self.font_header; c_sl.alignment = self.align_center
            
            ws.cell(row=current_row, column=5, value=item.get('ghi_chu', '')).border = self.border_thin

        # Tổng cộng
        current_row += 1
        ws.merge_cells(f'A{current_row}:C{current_row}')
        ws[f'A{current_row}'] = "TỔNG CỘNG"
        ws[f'A{current_row}'].font = self.font_header; ws[f'A{current_row}'].alignment = Alignment(horizontal='right')
        ws.cell(row=current_row, column=4, value=tong_sl).font = self.font_header
        
        # 7. Chữ ký
        current_row += 3
        ws.merge_cells(f'A{current_row}:B{current_row}'); ws[f'A{current_row}'] = "NGƯỜI GIAO\n(Ký và ghi rõ họ tên)"
        ws[f'A{current_row}'].font = self.font_header; ws[f'A{current_row}'].alignment = self.align_center
        
        ws.merge_cells(f'D{current_row}:E{current_row}'); ws[f'D{current_row}'] = "NGƯỜI NHẬN\n(Ký và ghi rõ họ tên)"
        ws[f'D{current_row}'].font = self.font_header; ws[f'D{current_row}'].alignment = self.align_center
        
        current_row += 4
        ws.merge_cells(f'A{current_row}:B{current_row}'); ws[f'A{current_row}'] = nguoi_lap.upper()
        ws[f'A{current_row}'].font = self.font_header; ws[f'A{current_row}'].alignment = self.align_center

        try:
            wb.save(filepath)
            self._view_file(filepath)
            return True
        except Exception as e:
            if self.parent_view:
                QMessageBox.critical(self.parent_view, "Lỗi Xuất File", str(e))
            return False

    # =====================================================================
    # MẪU 2: NHẬT KÝ HOẠT ĐỘNG (Dùng cho tab Reports)
    # =====================================================================
    def create_audit_log_report(self, data_list):
        self._setup_common_styles()
        # Tạo file
        now = datetime.now()
        folder_path = os.path.join(BASE_REPORT_DIR, "NhatKy", str(now.year), f"{now.month:02d}")
        os.makedirs(folder_path, exist_ok=True)
        filepath = os.path.join(folder_path, f"NhatKy_{now.strftime('%Y%m%d_%H%M%S')}.xlsx")
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "AuditLog"
        
        # Cấu hình A4 ngang
        ws.page_setup.paperSize = ws.PAPERSIZE_A4
        ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
        
        ws.merge_cells('A1:E1')
        ws['A1'] = "NHẬT KÝ HOẠT ĐỘNG HỆ THỐNG"
        ws['A1'].font = self.font_title; ws['A1'].alignment = self.align_center
        
        headers = ["ID", "Thời Gian", "Người Thực Hiện", "Bảng/Mã", "Nội Dung"]
        widths = [8, 20, 25, 30, 60]
        
        for i, h in enumerate(headers, 1):
            c = ws.cell(row=3, column=i, value=h)
            c.font = self.font_header; c.border = self.border_thin; c.alignment = self.align_center
            c.fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
            ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = widths[i-1]
            
        for i, item in enumerate(data_list, 1):
            r = 3 + i
            for j, val in enumerate([item['id'], item['thoi_gian'], item['nguoi_thuc_hien'], item['bang_ma'], item['noi_dung']], 1):
                c = ws.cell(row=r, column=j, value=str(val))
                c.border = self.border_thin
                c.alignment = self.align_left if j == 5 else self.align_center

        try:
            wb.save(filepath)
            self._view_file(filepath)
            return True
        except Exception as e:
            if self.parent_view: QMessageBox.critical(self.parent_view, "Lỗi Xuất File", str(e))
            return False
