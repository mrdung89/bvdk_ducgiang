from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QTableWidget, QTableWidgetItem, QHeaderView, 
                               QFileDialog, QMessageBox, QTabWidget, QLineEdit, QComboBox, QDateEdit, QGridLayout)
from PySide6.QtCore import Qt, QDate
from models.db_manager import DBManager
import csv

class ReportsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.db = DBManager()
        layout = QVBoxLayout(self)
        
        lbl = QLabel("BÁO CÁO, THỐNG KÊ & TRUY VẾT")
        lbl.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(lbl)
        
        self.tabs = QTabWidget()
        
        # TAB 1: Truy vết
        self.tab_trace = QWidget()
        self.setup_trace_tab()
        self.tabs.addTab(self.tab_trace, "🔍 Truy Vết (Search)")
        
        # TAB 2: Thống kê
        self.tab_stats = QWidget()
        self.setup_stats_tab()
        self.tabs.addTab(self.tab_stats, "📊 Thống Kê (Dashboard)")
        
        # TAB 3: Audit Log
        self.tab_log = QWidget()
        self.setup_log_tab()
        self.tabs.addTab(self.tab_log, "📝 Nhật Ký Hoạt Động")
        
        layout.addWidget(self.tabs)
        
        self.load_logs()
        self.calculate_stats()

    # ================= TAB 1: TRUY VẾT =================
    def setup_trace_tab(self):
        layout = QVBoxLayout(self.tab_trace)
        
        search_layout = QHBoxLayout()
        self.cb_search_type = QComboBox()
        self.cb_search_type.addItems(["Theo Mã Đồ / Mã Bộ", "Theo Khoa"])
        search_layout.addWidget(self.cb_search_type)
        
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Nhập mã đồ, tên, hoặc tên khoa cần truy vết...")
        self.txt_search.returnPressed.connect(self.do_trace)
        search_layout.addWidget(self.txt_search)
        
        btn_search = QPushButton("Truy Vết")
        btn_search.setObjectName("PrimaryButton")
        btn_search.clicked.connect(self.do_trace)
        search_layout.addWidget(btn_search)
        
        layout.addLayout(search_layout)
        
        # Results area
        self.lbl_trace_summary = QLabel("Nhập thông tin và bấm Truy Vết để xem kết quả.")
        self.lbl_trace_summary.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(self.lbl_trace_summary)
        
        self.table_trace = QTableWidget(0, 3)
        self.table_trace.setHorizontalHeaderLabels(["Thời Gian", "Người / Nơi Thực Hiện", "Nội Dung"])
        self.table_trace.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        layout.addWidget(self.table_trace)

    def do_trace(self):
        keyword = self.txt_search.text().strip()
        if not keyword: return
        
        # Bóc tách ID nếu chuỗi có dạng "ID:123, KHOA:..., LOAI:..."
        if keyword.startswith("ID:"):
            parts = keyword.split(",")
            keyword = parts[0].replace("ID:", "").strip()
            
        search_type = self.cb_search_type.currentText()
        
        self.table_trace.setRowCount(0)
        
        if search_type == "Theo Mã Đồ / Mã Bộ":
            # 1. Summary
            ton_ksnk = 0
            ton_khoa = []
            try:
                # Cập nhật: Tìm tên đúng ở cả 3 bảng
                ten = "Không rõ"
                ton_ksnk = 0
                b = self.db.fetch_one("SELECT ten_bo FROM danh_muc_bo_dung_cu WHERE ma_bo=%s", (keyword,))
                if b: ten = b['ten_bo']
                else:
                    v = self.db.fetch_one("SELECT ten_do_vai, cssd_ton_thuc_te FROM danh_muc_do_vai WHERE ma_do_vai=%s", (keyword,))
                    if v: 
                        ten = v['ten_do_vai']
                        ton_ksnk = v.get('cssd_ton_thuc_te', 0)
                    else:
                        d = self.db.fetch_one("SELECT ten_dc FROM danh_muc_dung_cu WHERE ma_dc=%s", (keyword,))
                        if d: ten = d['ten_dc']
                    
                res_tu = self.db.fetch_all("SELECT khoa, so_luong FROM tu_truc_khoa WHERE ma_do=%s AND so_luong > 0", (keyword,))
                for r in res_tu: ton_khoa.append(f"{r['khoa']} ({r['so_luong']})")
                
                txt_summary = f"Mã: {keyword} - Tên: {ten} | Đang tồn ở KSNK: {ton_ksnk}"
                if ton_khoa:
                    txt_summary += f" | Tủ trực khoa: {', '.join(ton_khoa)}"
                self.lbl_trace_summary.setText(txt_summary)
                
                # 2. History
                history = self.db.fetch_all("SELECT * FROM lich_su_bien_dong WHERE ma_do LIKE %s ORDER BY thoi_gian DESC LIMIT 100", (f"%{keyword}%",))
                if history:
                    self.table_trace.setRowCount(len(history))
                    for r, row in enumerate(history):
                        self.table_trace.setItem(r, 0, QTableWidgetItem(str(row.get('thoi_gian', ''))))
                        self.table_trace.setItem(r, 1, QTableWidgetItem(str(row.get('nguoi_thuc_hien', ''))))
                        self.table_trace.setItem(r, 2, QTableWidgetItem(str(row.get('noi_dung', ''))))
                else:
                    self.table_trace.setRowCount(0)
            except Exception as e:
                self.lbl_trace_summary.setText(f"Lỗi: {str(e)}")
                
        else:
            # Theo Khoa
            try:
                res_tu = self.db.fetch_all("SELECT ma_do, so_luong, dang_su_dung FROM tu_truc_khoa WHERE khoa=%s", (keyword,))
                total_sach = sum([r['so_luong'] for r in res_tu])
                total_ban = sum([r['dang_su_dung'] for r in res_tu])
                self.lbl_trace_summary.setText(f"Khoa: {keyword} | Tổng đồ sạch đang giữ: {total_sach} | Tổng đồ đang sử dụng cho BN: {total_ban}")
                
                # 2. History (những phiếu gửi hoặc nhận của khoa này)
                history = self.db.fetch_all("SELECT * FROM lich_su_bien_dong WHERE noi_dung LIKE %s ORDER BY thoi_gian DESC LIMIT 100", (f"%{keyword}%",))
                self.table_trace.setRowCount(len(history))
                for r, row in enumerate(history):
                    self.table_trace.setItem(r, 0, QTableWidgetItem(str(row['thoi_gian'])))
                    self.table_trace.setItem(r, 1, QTableWidgetItem(row['nguoi_thuc_hien']))
                    self.table_trace.setItem(r, 2, QTableWidgetItem(row['noi_dung']))
            except Exception as e:
                self.lbl_trace_summary.setText(f"Lỗi: {str(e)}")

    # ================= TAB 2: THỐNG KÊ =================
    def setup_stats_tab(self):
        layout = QVBoxLayout(self.tab_stats)
        
        filter_layout = QHBoxLayout()
        self.dt_from = QDateEdit()
        self.dt_from.setCalendarPopup(True)
        self.dt_from.setDate(QDate.currentDate().addDays(-30)) # 30 ngày trước
        
        self.dt_to = QDateEdit()
        self.dt_to.setCalendarPopup(True)
        self.dt_to.setDate(QDate.currentDate())
        
        filter_layout.addWidget(QLabel("Từ ngày:"))
        filter_layout.addWidget(self.dt_from)
        filter_layout.addWidget(QLabel("Đến ngày:"))
        filter_layout.addWidget(self.dt_to)
        
        btn_calc = QPushButton("Cập nhật số liệu")
        btn_calc.clicked.connect(self.calculate_stats)
        filter_layout.addWidget(btn_calc)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Grid Dashboard
        self.grid = QGridLayout()
        
        self.lbl_total_nhan = QLabel("0")
        self.lbl_total_nhan.setStyleSheet("font-size: 24px; color: #e74c3c; font-weight: bold;")
        self.grid.addWidget(QLabel("Tổng đồ dơ (đã tiếp nhận):"), 0, 0)
        self.grid.addWidget(self.lbl_total_nhan, 1, 0)
        
        self.lbl_total_phat = QLabel("0")
        self.lbl_total_phat.setStyleSheet("font-size: 24px; color: #27ae60; font-weight: bold;")
        self.grid.addWidget(QLabel("Tổng đồ sạch (đã cấp phát):"), 0, 1)
        self.grid.addWidget(self.lbl_total_phat, 1, 1)
        
        layout.addLayout(self.grid)
        
        self.table_top_khoa = QTableWidget(0, 2)
        self.table_top_khoa.setHorizontalHeaderLabels(["Tên Khoa", "Số lượng giao dịch đồ"])
        self.table_top_khoa.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        layout.addWidget(QLabel("Top Khoa Giao Dịch:"))
        layout.addWidget(self.table_top_khoa)

    def calculate_stats(self):
        f_from = self.dt_from.date().toString("yyyy-MM-dd 00:00:00")
        f_to = self.dt_to.date().toString("yyyy-MM-dd 23:59:59")
        
        try:
            # Đồ dơ đã nhận
            res_nhan = self.db.fetch_one("SELECT SUM(so_luong) as total FROM lich_su_giao_nhan WHERE thoi_gian BETWEEN %s AND %s", (f_from, f_to))
            self.lbl_total_nhan.setText(str(res_nhan['total'] or 0))
            
            # Đồ sạch cấp phát
            res_phat = self.db.fetch_one("SELECT SUM(so_luong) as total FROM phieu_cap_phat WHERE thoi_gian BETWEEN %s AND %s", (f_from, f_to))
            self.lbl_total_phat.setText(str(res_phat['total'] or 0))
            
            # Top Khoa (từ phiếu gửi)
            top_khoa = self.db.fetch_all("SELECT khoa_giao, SUM(so_luong) as total FROM lich_su_giao_nhan WHERE thoi_gian BETWEEN %s AND %s GROUP BY khoa_giao ORDER BY total DESC", (f_from, f_to))
            self.table_top_khoa.setRowCount(len(top_khoa))
            for r, row in enumerate(top_khoa):
                self.table_top_khoa.setItem(r, 0, QTableWidgetItem(row['khoa_giao']))
                self.table_top_khoa.setItem(r, 1, QTableWidgetItem(str(row['total'])))
        except: pass

    # ================= TAB 3: AUDIT LOG =================
    def setup_log_tab(self):
        layout = QVBoxLayout(self.tab_log)
        hl = QHBoxLayout()
        btn_export = QPushButton("📥 Xuất Nhật Ký (Excel/CSV)")
        btn_export.setObjectName("SuccessButton")
        btn_export.clicked.connect(self.export_csv)
        hl.addStretch()
        hl.addWidget(btn_export)
        layout.addLayout(hl)
        
        self.table_log = QTableWidget(0, 5)
        self.table_log.setHorizontalHeaderLabels(["ID", "Thời Gian", "Người Thực Hiện", "Bảng/Mã", "Nội Dung"])
        self.table_log.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        layout.addWidget(self.table_log)

    def load_logs(self):
        try:
            logs = self.db.fetch_all("SELECT * FROM lich_su_bien_dong ORDER BY thoi_gian DESC LIMIT 500")
            self.table_log.setRowCount(len(logs))
            for r, row in enumerate(logs):
                self.table_log.setItem(r, 0, QTableWidgetItem(str(row['id'])))
                self.table_log.setItem(r, 1, QTableWidgetItem(str(row['thoi_gian'])))
                self.table_log.setItem(r, 2, QTableWidgetItem(row['nguoi_thuc_hien']))
                self.table_log.setItem(r, 3, QTableWidgetItem(f"{row.get('bang_du_lieu','')} / {row.get('ma_item','')}"))
                self.table_log.setItem(r, 4, QTableWidgetItem(row['noi_dung']))
        except Exception: pass

    def export_csv(self):
        if self.table_log.rowCount() == 0:
            QMessageBox.warning(self, "Lỗi", "Không có dữ liệu để xuất!")
            return
            
        data_list = []
        for row in range(self.table_log.rowCount()):
            data_list.append({
                'id': self.table_log.item(row, 0).text() if self.table_log.item(row, 0) else "",
                'thoi_gian': self.table_log.item(row, 1).text() if self.table_log.item(row, 1) else "",
                'nguoi_thuc_hien': self.table_log.item(row, 2).text() if self.table_log.item(row, 2) else "",
                'bang_ma': f"{self.table_log.item(row, 3).text() if self.table_log.item(row, 3) else ''} / {self.table_log.item(row, 4).text() if self.table_log.item(row, 4) else ''}",
                'noi_dung': self.table_log.item(row, 5).text() if self.table_log.item(row, 5) else ""
            })
            
        from utils.excel_reporter import ExcelReporter
        reporter = ExcelReporter(parent_view=self)
        reporter.create_audit_log_report(data_list)
