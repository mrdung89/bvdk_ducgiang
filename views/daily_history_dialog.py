from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QTreeWidget, QTreeWidgetItem, QPushButton, 
                               QInputDialog, QMessageBox, QHeaderView)
from PySide6.QtCore import Qt

class DailyHistoryDialog(QDialog):
    def __init__(self, parent_view, db, mode, date_str):
        super().__init__(parent_view)
        self.parent_view = parent_view
        self.db = db
        self.mode = mode # 'GUI', 'DUYET', 'CAP_PHAT'
        self.date_str = date_str
        
        if mode == 'GUI': title = "Lịch sử Khoa Gửi đồ dơ"
        elif mode == 'DUYET': title = "Lịch sử KSNK Đã Duyệt đồ dơ"
        else: title = "Lịch sử KSNK Đã Cấp Phát đồ sạch"
            
        self.setWindowTitle(f"{title} - Ngày: {date_str}")
        self.resize(1100, 700)
        
        layout = QVBoxLayout(self)
        
        lbl = QLabel(f"{title.upper()} ({date_str})")
        lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(lbl)
        
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Khoa / Tên Đồ", "Thời Gian", "Số Lượng", "Trạng Thái", "Người Gửi/Duyệt", "Thao Tác"])
        self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree.setColumnWidth(1, 150)
        self.tree.setColumnWidth(2, 100)
        self.tree.setColumnWidth(3, 150)
        self.tree.setColumnWidth(4, 150)
        layout.addWidget(self.tree)
        
        btn_close = QPushButton("ĐÓNG")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignRight)
        
        self.load_data()

    def load_data(self):
        self.tree.clear()
        
        if self.mode == 'GUI':
            sql = """SELECT id, khoa_giao as khoa, ma_do, so_luong, trang_thai, thoi_gian, 'Điều dưỡng khoa' as nguoi_thuc_hien 
                     FROM lich_su_giao_nhan WHERE DATE(thoi_gian)=%s ORDER BY khoa_giao, thoi_gian DESC"""
        elif self.mode == 'DUYET':
            sql = """SELECT id, khoa_giao as khoa, ma_do, so_luong, trang_thai, thoi_gian, 'NV KSNK' as nguoi_thuc_hien 
                     FROM lich_su_giao_nhan WHERE DATE(thoi_gian)=%s AND trang_thai != 'CHO_TIEP_NHAN' ORDER BY khoa_giao, thoi_gian DESC"""
        else:
            sql = """SELECT c.id, p.khoa_nhan as khoa, c.ma_do, c.so_luong, 'Đã cấp' as trang_thai, p.thoi_gian, p.nguoi_giao as nguoi_thuc_hien 
                     FROM chi_tiet_cap_phat c 
                     JOIN phieu_cap_phat p ON c.ma_phieu = p.ma_phieu
                     WHERE DATE(p.thoi_gian)=%s ORDER BY p.khoa_nhan, p.thoi_gian DESC"""
                     
        try:
            rows = self.db.fetch_all(sql, (self.date_str,))
            if not rows: return
            
            from collections import defaultdict
            grouped = defaultdict(list)
            for r in rows:
                grouped[r['khoa']].append(r)
                
            for khoa, items in grouped.items():
                root = QTreeWidgetItem([khoa, "", f"Tổng: {sum(i['so_luong'] for i in items)}", "", "", ""])
                for col in range(6):
                    font = root.font(col)
                    font.setBold(True)
                    root.setFont(col, font)
                    
                self.tree.addTopLevelItem(root)
                
                btn_print = QPushButton("🖨️ In Phiếu Tổng")
                btn_print.setStyleSheet("background-color: #27ae60; color: white;")
                btn_print.clicked.connect(lambda ch, k=khoa, it=items: self.reprint_excel(k, it))
                self.tree.setItemWidget(root, 5, btn_print)
                
                for r in items:
                    ma_do = r['ma_do']
                    ten_do = ma_do
                    b = self.db.fetch_one("SELECT ten_bo FROM danh_muc_bo_dung_cu WHERE ma_bo=%s", (ma_do,))
                    if b: ten_do = b['ten_bo']
                    else:
                        v = self.db.fetch_one("SELECT ten_do_vai FROM danh_muc_do_vai WHERE ma_do_vai=%s", (ma_do,))
                        if v: ten_do = v['ten_do_vai']
                        else:
                            d = self.db.fetch_one("SELECT ten_dc FROM danh_muc_dung_cu WHERE ma_dc=%s", (ma_do,))
                            if d: ten_do = d['ten_dc']
                            
                    tg_str = r['thoi_gian'].strftime('%H:%M:%S') if hasattr(r['thoi_gian'], 'strftime') else str(r['thoi_gian'])
                    nguoi = r['nguoi_thuc_hien'] or 'Hệ thống'
                    
                    child = QTreeWidgetItem([f"  [{ma_do}] {ten_do}", tg_str, str(r['so_luong']), r['trang_thai'], str(nguoi), ""])
                    root.addChild(child)
                    
                    btn_edit = QPushButton("Sửa SL")
                    btn_edit.setStyleSheet("background-color: #f39c12; color: white;")
                    btn_edit.clicked.connect(lambda ch, pid=r['id'], cur_sl=r['so_luong']: self.edit_qty(pid, cur_sl))
                    self.tree.setItemWidget(child, 5, btn_edit)
                    
            self.tree.expandAll()
            
        except Exception as e:
            QMessageBox.critical(self, "Lỗi load_data", str(e))
            
    def edit_qty(self, pid, current_sl):
        new_sl, ok = QInputDialog.getInt(self, "Sửa số lượng", "Nhập số lượng thực tế:", current_sl, 0, 9999)
        if ok and new_sl != current_sl:
            try:
                if self.mode in ('GUI', 'DUYET'):
                    self.db.execute("UPDATE lich_su_giao_nhan SET so_luong=%s WHERE id=%s", (new_sl, pid))
                    self.db.execute("INSERT INTO lich_su_bien_dong (thoi_gian, nguoi_thuc_hien, bang_du_lieu, ma_item, noi_dung) VALUES (NOW(), 'KSNK', 'lich_su_giao_nhan', %s, %s)", 
                                    (pid, f"Sửa số lượng: {current_sl} -> {new_sl}"))
                else:
                    old_rec = self.db.fetch_one("SELECT so_luong, ma_do FROM chi_tiet_cap_phat WHERE id=%s", (pid,))
                    if old_rec:
                        self.db.execute("UPDATE chi_tiet_cap_phat SET so_luong=%s WHERE id=%s", (new_sl, pid))
                        self.db.execute("INSERT INTO lich_su_bien_dong (thoi_gian, nguoi_thuc_hien, bang_du_lieu, ma_item, noi_dung) VALUES (NOW(), 'KSNK', 'chi_tiet_cap_phat', %s, %s)", 
                                        (old_rec['ma_do'], f"Sửa số lượng: {current_sl} -> {new_sl}"))
                        diff = old_rec['so_luong'] - new_sl
                        if diff != 0:
                            self.db.execute("UPDATE danh_muc_do_vai SET cssd_ton_thuc_te = cssd_ton_thuc_te + %s WHERE ma_do_vai=%s", (diff, old_rec['ma_do']))
                
                QMessageBox.information(self, "Thành công", "Đã cập nhật số lượng và lưu vết!")
                self.load_data()
            except Exception as e:
                QMessageBox.warning(self, "Lỗi", str(e))

    def reprint_excel(self, khoa, items):
        data_list = []
        for r in items:
            ma_do = r['ma_do']
            ten_do = ma_do
            b = self.db.fetch_one("SELECT ten_bo FROM danh_muc_bo_dung_cu WHERE ma_bo=%s", (ma_do,))
            if b: ten_do = b['ten_bo']
            else:
                v = self.db.fetch_one("SELECT ten_do_vai FROM danh_muc_do_vai WHERE ma_do_vai=%s", (ma_do,))
                if v: ten_do = v['ten_do_vai']
                else:
                    d = self.db.fetch_one("SELECT ten_dc FROM danh_muc_dung_cu WHERE ma_dc=%s", (ma_do,))
                    if d: ten_do = d['ten_dc']
                    
            if r['so_luong'] > 0:
                data_list.append({
                    "ma_do": ma_do,
                    "ten_do": ten_do,
                    "so_luong": r['so_luong'],
                    "ghi_chu": "In lại"
                })
                
        if not data_list: return
        
        from utils.excel_reporter import ExcelReporter
        reporter = ExcelReporter(parent_view=self)
        ma_phieu = f"REPRINT-{self.date_str.replace('-','')}"
        reporter.create_distribution_receipt(khoa, ma_phieu, f"{self.date_str} 23:59", data_list, "NV KSNK (In Lại)")
