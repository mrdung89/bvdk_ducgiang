from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                               QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QDialog, QSpinBox, QDateEdit)
from PySide6.QtCore import Qt, QDate
from datetime import datetime

class HistoryTab(QWidget):
    def __init__(self, db_manager, mode, parent_page=None):
        super().__init__()
        self.db = db_manager
        self.mode = mode # 'RECEIVE' or 'ISSUE'
        self.parent_page = parent_page
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Table
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Mã Phiếu", "Thời Gian", "Khoa", "Tổng Món", "Người Tạo"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.itemDoubleClicked.connect(self.show_detail)
        layout.addWidget(self.table)
        
    def load_data(self, target_date_str):
        self.table.setRowCount(0)
        
        if self.mode == 'RECEIVE':
            sql = """
                SELECT ma_phieu, khoa_giao as khoa, MAX(thoi_gian) as thoi_gian, COUNT(id) as tong_mon, MAX(IFNULL(nguoi_tao, 'Wards')) as nguoi_tao
                FROM lich_su_giao_nhan 
                WHERE DATE(thoi_gian) = %s AND ma_phieu IS NOT NULL
                GROUP BY ma_phieu, khoa_giao
                ORDER BY thoi_gian DESC
            """
        else:
            sql = """
                SELECT p.ma_phieu, p.khoa_nhan as khoa, MAX(p.thoi_gian) as thoi_gian, COUNT(id) as tong_mon, 'KSNK' as nguoi_tao
                FROM phieu_cap_phat p
                WHERE DATE(p.thoi_gian) = %s AND ma_phieu IS NOT NULL
                GROUP BY p.ma_phieu, p.khoa_nhan
                ORDER BY thoi_gian DESC
            """
            
        try:
            rows = self.db.fetch_all(sql, (target_date_str,))
            if not rows: return
            for r in rows:
                row_idx = self.table.rowCount()
                self.table.insertRow(row_idx)
                
                c_ma = QTableWidgetItem(str(r.get('ma_phieu', '')))
                self.table.setItem(row_idx, 0, c_ma)
                
                tg = r.get('thoi_gian')
                tg_str = tg.strftime('%H:%M:%S') if hasattr(tg, 'strftime') else str(tg)
                self.table.setItem(row_idx, 1, QTableWidgetItem(tg_str))
                
                self.table.setItem(row_idx, 2, QTableWidgetItem(str(r.get('khoa', ''))))
                self.table.setItem(row_idx, 3, QTableWidgetItem(str(r.get('tong_mon', ''))))
                self.table.setItem(row_idx, 4, QTableWidgetItem(str(r.get('nguoi_tao', ''))))
        except Exception as e:
            print(f"Error loading history: {e}")

    def show_detail(self, item):
        row = item.row()
        ma_phieu = self.table.item(row, 0).text()
        khoa = self.table.item(row, 2).text()
        
        dlg = HistoryDetailDialog(self.db, self.mode, ma_phieu, khoa, self)
        dlg.exec()


class HistoryDetailDialog(QDialog):
    def __init__(self, db, mode, ma_phieu, khoa, parent=None):
        super().__init__(parent)
        self.db = db
        self.mode = mode
        self.ma_phieu = ma_phieu
        self.khoa = khoa
        
        self.setWindowTitle(f"Chi Tiết Lịch Sử - {ma_phieu}")
        self.resize(800, 600)
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        h = QHBoxLayout()
        h.addWidget(QLabel(f"<b>Mã Phiếu:</b> {self.ma_phieu}"))
        h.addWidget(QLabel(f"<b>Khoa:</b> {self.khoa}"))
        layout.addLayout(h)
        
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID Record", "Mã Đồ / Tên", "Số Lượng", "Trạng Thái"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        layout.addWidget(self.table)
        
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Lưu Chỉnh Sửa SL")
        btn_save.setStyleSheet("background-color: #f39c12; color: white; font-weight: bold; padding: 8px;")
        btn_save.clicked.connect(self.save_edits)
        btn_layout.addWidget(btn_save)
        
        btn_print = QPushButton("In Lại Phiếu")
        btn_print.setStyleSheet("background-color: #2980b9; color: white; font-weight: bold; padding: 8px;")
        btn_print.clicked.connect(self.reprint)
        btn_layout.addWidget(btn_print)
        
        layout.addLayout(btn_layout)
        
    def load_data(self):
        self.table.setRowCount(0)
        if self.mode == 'RECEIVE':
            sql = """
                SELECT n.id, n.ma_do as code, n.so_luong as qty, n.trang_thai as status,
                       IFNULL(b.ten_bo, IFNULL(v.ten_do_vai, d.ten_dc)) as name
                FROM lich_su_giao_nhan n
                LEFT JOIN danh_muc_bo_dung_cu b ON n.ma_do = b.ma_bo
                LEFT JOIN danh_muc_do_vai v ON n.ma_do = v.ma_do_vai
                LEFT JOIN danh_muc_dung_cu d ON n.ma_do = d.ma_dc
                WHERE n.ma_phieu = %s
            """
        else:
            sql = """
                SELECT p.id, p.ma_do as code, p.so_luong as qty, 'DA_CAP_PHAT' as status,
                       IFNULL(b.ten_bo, IFNULL(v.ten_do_vai, d.ten_dc)) as name
                FROM phieu_cap_phat p
                LEFT JOIN danh_muc_bo_dung_cu b ON p.ma_do = b.ma_bo
                LEFT JOIN danh_muc_do_vai v ON p.ma_do = v.ma_do_vai
                LEFT JOIN danh_muc_dung_cu d ON p.ma_do = d.ma_dc
                WHERE p.ma_phieu = %s
            """
            
        rows = self.db.fetch_all(sql, (self.ma_phieu,))
        if not rows: return
        
        for r in rows:
            row_idx = self.table.rowCount()
            self.table.insertRow(row_idx)
            
            c_id = QTableWidgetItem(str(r['id']))
            c_id.setFlags(c_id.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row_idx, 0, c_id)
            
            c_name = QTableWidgetItem(f"[{r['code']}] {r['name']}")
            c_name.setFlags(c_name.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row_idx, 1, c_name)
            
            spin = QSpinBox()
            spin.setRange(0, 1000)
            spin.setValue(int(r['qty']))
            self.table.setItemWidget(row_idx, 2, spin)
            
            c_stat = QTableWidgetItem(str(r['status']))
            c_stat.setFlags(c_stat.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row_idx, 3, c_stat)

    def save_edits(self):
        try:
            for row in range(self.table.rowCount()):
                record_id = int(self.table.item(row, 0).text())
                spin = self.table.cellWidget(row, 2)
                if not spin: continue
                new_qty = spin.value()
                
                if self.mode == 'RECEIVE':
                    old_rec = self.db.fetch_one("SELECT so_luong, ma_do FROM lich_su_giao_nhan WHERE id=%s", (record_id,))
                    if old_rec and old_rec['so_luong'] != new_qty:
                        self.db.execute("UPDATE lich_su_giao_nhan SET so_luong=%s WHERE id=%s", (new_qty, record_id))
                        self.db.execute("INSERT INTO lich_su_bien_dong (thoi_gian, nguoi_thuc_hien, bang_du_lieu, ma_item, noi_dung) VALUES (NOW(), 'KSNK', 'lich_su_giao_nhan', %s, %s)", 
                                        (old_rec['ma_do'], f"Sửa phiếu {self.ma_phieu}: SL từ {old_rec['so_luong']} thành {new_qty}"))
                else:
                    old_rec = self.db.fetch_one("SELECT so_luong, ma_do FROM phieu_cap_phat WHERE id=%s", (record_id,))
                    if old_rec and old_rec['so_luong'] != new_qty:
                        self.db.execute("UPDATE phieu_cap_phat SET so_luong=%s WHERE id=%s", (new_qty, record_id))
                        self.db.execute("INSERT INTO lich_su_bien_dong (thoi_gian, nguoi_thuc_hien, bang_du_lieu, ma_item, noi_dung) VALUES (NOW(), 'KSNK', 'phieu_cap_phat', %s, %s)", 
                                        (old_rec['ma_do'], f"Sửa phiếu {self.ma_phieu}: SL từ {old_rec['so_luong']} thành {new_qty}"))
                        diff = old_rec['so_luong'] - new_qty
                        if diff != 0:
                            self.db.execute("UPDATE danh_muc_do_vai SET cssd_ton_thuc_te = cssd_ton_thuc_te + %s WHERE ma_do_vai=%s", (diff, old_rec['ma_do']))
            
            QMessageBox.information(self, "OK", "Đã lưu thay đổi!")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", str(e))

    def reprint(self):
        data_list = []
        for row in range(self.table.rowCount()):
            name_full = self.table.item(row, 1).text()
            ma_do = name_full.split(']')[0].replace('[', '')
            ten_do = name_full.split(']')[1].strip() if ']' in name_full else name_full
            
            spin = self.table.cellWidget(row, 2)
            qty = spin.value() if spin else 0
            
            if qty > 0:
                data_list.append({
                    "ma_do": ma_do,
                    "ten_do": ten_do,
                    "so_luong": qty,
                    "ghi_chu": "In lại"
                })
                
        if not data_list: return
        
        from utils.excel_reporter import ExcelReporter
        reporter = ExcelReporter(parent_view=self)
        
        thoi_gian = datetime.now().strftime("%d/%m/%Y %H:%M")
        title = "KSNK (Bản Sao)" if self.mode == 'RECEIVE' else "KSNK (Bản Sao Cấp Phát)"
        reporter.create_distribution_receipt(self.khoa, self.ma_phieu, thoi_gian, data_list, title)
