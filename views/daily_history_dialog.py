import os
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QTreeWidget, QTreeWidgetItem, QPushButton, 
                               QInputDialog, QMessageBox, QHeaderView, QDateEdit, QLineEdit, QCompleter, QWidget)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont

class DailyHistoryDialog(QDialog):
    def __init__(self, parent_view, db, mode, date_str):
        super().__init__(parent_view)
        self.parent_view = parent_view
        self.db = db
        self.mode = mode # 'GUI', 'DUYET', 'CAP_PHAT'
        
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
        
        if mode == 'GUI': title = "LỊCH SỬ KHOA GỬI ĐỒ DƠ"
        elif mode == 'DUYET': title = "LỊCH SỬ KSNK ĐÃ DUYỆT ĐỒ DƠ"
        else: title = "LỊCH SỬ KSNK ĐÃ CẤP PHÁT ĐỒ SẠCH"
            
        self.setWindowTitle(title)
        self.resize(1200, 750)
        
        layout = QVBoxLayout(self)
        
        # --- Top Filter Area ---
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("Từ ngày:"))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("dd/MM/yyyy")
        filter_layout.addWidget(self.date_from)
        
        filter_layout.addWidget(QLabel("Đến ngày:"))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("dd/MM/yyyy")
        filter_layout.addWidget(self.date_to)
        
        # Set default dates
        try:
            cur_d = QDate.fromString(date_str, "yyyy-MM-dd")
            if not cur_d.isValid():
                cur_d = QDate.currentDate()
        except:
            cur_d = QDate.currentDate()
            
        self.date_to.setDate(cur_d)
        if mode == 'GUI':
            self.date_from.setDate(cur_d.addDays(-7))
        else:
            self.date_from.setDate(cur_d)
            
        filter_layout.addWidget(QLabel("Khoa:"))
        self.txt_khoa = QLineEdit()
        self.txt_khoa.setPlaceholderText("Nhập tên khoa...")
        
        # Setup completer for Khoa
        khoas = [r['ten_khoa'] for r in self.db.fetch_all("SELECT ten_khoa FROM danh_muc_khoa")]
        completer = QCompleter(khoas)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        self.txt_khoa.setCompleter(completer)
        filter_layout.addWidget(self.txt_khoa)
        
        btn_filter = QPushButton("🔍 Lọc Dữ Liệu")
        btn_filter.setStyleSheet("background-color: #2980b9; color: white; font-weight: bold; padding: 6px 12px;")
        btn_filter.clicked.connect(self.load_data)
        filter_layout.addWidget(btn_filter)
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)
        # --- End Filter Area ---
        
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Mã Phiếu / Tên Đồ", "Thời Gian", "Số Lượng", "Trạng Thái", "Người Thực Hiện/Duyệt", "Thao Tác"])
        self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree.setColumnWidth(1, 160)
        self.tree.setColumnWidth(2, 90)
        self.tree.setColumnWidth(3, 160)
        self.tree.setColumnWidth(4, 200)
        self.tree.setColumnWidth(5, 120)
        layout.addWidget(self.tree)
        
        btn_close = QPushButton("ĐÓNG")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignRight)
        
        self.load_data()

    def load_data(self):
        self.tree.clear()
        
        d_from = self.date_from.date().toString("yyyy-MM-dd")
        d_to = self.date_to.date().toString("yyyy-MM-dd")
        khoa_filter = self.txt_khoa.text().strip()
        
        params = [d_from, d_to]
        
        if self.mode == 'GUI':
            sql = """SELECT id, khoa_giao as khoa, ma_do, so_luong, trang_thai, thoi_gian, 'NV KSNK' as nguoi_duyet, thoi_gian_duyet, ma_phieu 
                     FROM lich_su_giao_nhan 
                     WHERE DATE(thoi_gian) >= %s AND DATE(thoi_gian) <= %s """
        elif self.mode == 'DUYET':
            sql = """SELECT id, khoa_giao as khoa, ma_do, so_luong, trang_thai, thoi_gian, 'NV KSNK' as nguoi_thuc_hien, thoi_gian_duyet, ma_phieu 
                     FROM lich_su_giao_nhan 
                     WHERE DATE(thoi_gian) >= %s AND DATE(thoi_gian) <= %s AND trang_thai != 'CHO_TIEP_NHAN' """
        else:
            sql = """SELECT c.id, p.khoa_nhan as khoa, c.ma_do, c.so_luong, 'Đã cấp' as trang_thai, p.thoi_gian, 'KSNK' as nguoi_thuc_hien, p.ma_phieu 
                     FROM chi_tiet_cap_phat c 
                     JOIN phieu_cap_phat p ON c.ma_phieu = p.ma_phieu
                     WHERE DATE(p.thoi_gian) >= %s AND DATE(p.thoi_gian) <= %s """
        
        if khoa_filter:
            if self.mode in ('GUI', 'DUYET'):
                sql += " AND khoa_giao LIKE %s"
            else:
                sql += " AND p.khoa_nhan LIKE %s"
            params.append(f"%{khoa_filter}%")
            
        sql += " ORDER BY thoi_gian DESC"
                     
        try:
            rows = self.db.fetch_all(sql, params)
            if not rows: return
            
            from collections import defaultdict
            grouped = defaultdict(list)
            for r in rows:
                k = r.get('ma_phieu')
                if not k:
                    tg_format = r['thoi_gian'].strftime('%Y%m%d_%H%M') if hasattr(r['thoi_gian'], 'strftime') else str(r['thoi_gian'])[:16]
                    k = f'FORM_{r["khoa"]}_{tg_format}'
                grouped[k].append(r)
                
            for ma_phieu, items in grouped.items():
                khoa = items[0]['khoa']
                tg = items[0]['thoi_gian']
                tg_str = tg.strftime('%d/%m/%Y %H:%M') if hasattr(tg, 'strftime') else str(tg)
                
                disp_phieu = "Đồng bộ từ Google Form" if str(ma_phieu).startswith("FORM") else ma_phieu
                root = QTreeWidgetItem([f"📁 Phiên: {disp_phieu} (Khoa: {khoa})", tg_str, f"Tổng: {sum(i['so_luong'] for i in items)}", "", "", ""])
                for col in range(6):
                    font = root.font(col)
                    font.setBold(True)
                    root.setFont(col, font)
                    
                self.tree.addTopLevelItem(root)
                
                btn_print = QPushButton("🖨️ In Phiếu Tổng")
                btn_print.setStyleSheet("background-color: #27ae60; color: white;")
                btn_print.clicked.connect(lambda ch, k=khoa, it=items: self.reprint_excel(k, it))
                
                # Cần 1 widget container để margin nút
                w = QWidget()
                l = QHBoxLayout(w)
                l.setContentsMargins(0, 0, 0, 0)
                l.addWidget(btn_print)
                self.tree.setItemWidget(root, 5, w)
                
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
                            
                    tg_item = r['thoi_gian'].strftime('%H:%M:%S') if hasattr(r['thoi_gian'], 'strftime') else str(r['thoi_gian'])
                    
                    if self.mode == 'GUI':
                        ng_duyet = r.get('nguoi_duyet')
                        tg_duyet = r.get('thoi_gian_duyet')
                        tt = r['trang_thai']
                        if tt == 'CHO_TIEP_NHAN':
                            tt_str = 'Chưa duyệt'
                            nguoi = 'Khoa gửi (chờ KSNK duyệt)'
                        else:
                            tt_str = f"Đã duyệt ({tt})"
                            tgd_str = tg_duyet.strftime('%d/%m %H:%M') if hasattr(tg_duyet, 'strftime') else (str(tg_duyet) if tg_duyet else "--")
                            nguoi = f"KSNK duyệt lúc {tgd_str}"
                    else:
                        nguoi = r.get('nguoi_thuc_hien') or 'Hệ thống'
                        tt_str = r['trang_thai']
                        
                    child = QTreeWidgetItem([f"    [{ma_do}] {ten_do}", tg_item, str(r['so_luong']), tt_str, str(nguoi), ""])
                    root.addChild(child)
                    
                    btn_edit = QPushButton("Sửa SL")
                    btn_edit.setStyleSheet("background-color: #f39c12; color: white;")
                    btn_edit.clicked.connect(lambda ch, pid=r['id'], cur_sl=r['so_luong']: self.edit_qty(pid, cur_sl))
                    
                    cw = QWidget()
                    cl = QHBoxLayout(cw)
                    cl.setContentsMargins(0, 0, 0, 0)
                    cl.addWidget(btn_edit)
                    self.tree.setItemWidget(child, 5, cw)
                    
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
        ma_phieu = items[0].get('ma_phieu') or f"REPRINT-{self.date_to.date().toString('yyyyMMdd')}"
        reporter.create_distribution_receipt(khoa, ma_phieu, f"{self.date_to.date().toString('yyyy-MM-dd')} 23:59", data_list, "NV KSNK (In Lại)")
