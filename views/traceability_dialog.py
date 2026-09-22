import json
from datetime import datetime
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                               QListWidget, QListWidgetItem, QTreeWidget, QTreeWidgetItem,
                               QPushButton, QHeaderView, QMessageBox, QFrame)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor
from models.db_manager import DBManager

def resolve_item(db, ma_do):
    """Trả về (ten, loai) từ mã đồ hoặc QR code"""
    # 1. Parse JSON QR: {"id":...,"loai":"DOVAI"} hoặc {"loai":"BO",...}
    try:
        obj = json.loads(ma_do)
        item_id = obj.get('id', '')
        loai = obj.get('loai', '').upper()
        if 'DOVAI' in loai:
            r = db.fetch_one('SELECT ten_do_vai FROM danh_muc_do_vai WHERE id=%s OR ma_do_vai=%s', (item_id, str(item_id)))
            if r: return r['ten_do_vai'], 'ĐỒ VẢI'
        if 'DOLE' in loai or 'DC' in loai:
            r = db.fetch_one('SELECT ten_dc FROM danh_muc_dung_cu WHERE id=%s OR ma_dc=%s', (item_id, str(item_id)))
            if r: return r['ten_dc'], 'DỤNG CỤ'
        if 'BO' in loai:
            r = db.fetch_one('SELECT ten_bo FROM danh_muc_bo_dung_cu WHERE id=%s OR ma_bo=%s', (item_id, str(item_id)))
            if r: return r['ten_bo'], 'BỘ DỤNG CỤ'
    except Exception:
        pass
    
    # 2. Số nguyên -> bộ dụng cụ
    if str(ma_do).isdigit():
        r = db.fetch_one('SELECT ten_bo FROM danh_muc_bo_dung_cu WHERE id=%s', (int(ma_do),))
        if r: return r['ten_bo'], 'BỘ DỤNG CỤ'
    
    # 3. Tìm theo mã text trong cả 3 bảng
    r = db.fetch_one('SELECT ten_bo FROM danh_muc_bo_dung_cu WHERE ma_bo=%s', (ma_do,))
    if r: return r['ten_bo'], 'BỘ DỤNG CỤ'
    
    r = db.fetch_one('SELECT ten_do_vai FROM danh_muc_do_vai WHERE ma_do_vai=%s', (ma_do,))
    if r: return r['ten_do_vai'], 'ĐỒ VẢI'
    
    r = db.fetch_one('SELECT ten_dc FROM danh_muc_dung_cu WHERE ma_dc=%s', (ma_do,))
    if r: return r['ten_dc'], 'DỤNG CỤ'
    
    return ma_do, 'KHÔNG XÁC ĐỊNH'

def get_full_timeline(db, ma_do):
    """Truy vết xuôi đầy đủ cho 1 ma_do"""
    # Giao nhận
    giao_nhan = db.fetch_all(
        'SELECT id, khoa_giao, so_luong, trang_thai, thoi_gian, thoi_gian_duyet, ma_phieu '
        'FROM lich_su_giao_nhan WHERE ma_do=%s ORDER BY thoi_gian ASC', (ma_do,)
    ) or []
    
    # Khử nhiễm
    khu_nhiem = db.fetch_all(
        'SELECT id, nguoi_thuc_hien, phuong_phap, thoi_gian '
        'FROM nhat_ky_khu_nhiem WHERE ma_do=%s ORDER BY thoi_gian ASC', (ma_do,)
    ) or []
    
    # Tiệt khuẩn (qua chi_tiet_tiep_nhan + phieu_tiep_nhan)
    tiet_khuan = []
    ct = db.fetch_all("SHOW COLUMNS FROM chi_tiet_tiep_nhan")
    if ct and any(x['Field'] == 'ma_do' for x in ct):
        tiet_khuan = db.fetch_all(
            'SELECT pt.ma_phieu, pt.thoi_gian, pt.nguoi_nhan, pt.khoa_giao, ctt.so_luong '
            'FROM chi_tiet_tiep_nhan ctt '
            'JOIN phieu_tiep_nhan pt ON ctt.ma_phieu=pt.ma_phieu '
            'WHERE ctt.ma_do=%s ORDER BY pt.thoi_gian ASC', (ma_do,)
        ) or []
    
    # Cấp phát
    cap_phat = []
    ct2 = db.fetch_all("SHOW COLUMNS FROM chi_tiet_cap_phat")
    if ct2 and any(x['Field'] == 'ma_do' for x in ct2):
        cap_phat = db.fetch_all(
            'SELECT pcp.ma_phieu, pcp.thoi_gian, pcp.khoa_nhan, pcp.nguoi_giao, ctcp.so_luong '
            'FROM chi_tiet_cap_phat ctcp '
            'JOIN phieu_cap_phat pcp ON ctcp.ma_phieu=pcp.ma_phieu '
            'WHERE ctcp.ma_do=%s ORDER BY pcp.thoi_gian ASC', (ma_do,)
        ) or []
        
    return {
        'giao_nhan': giao_nhan,
        'khu_nhiem': khu_nhiem,
        'tiet_khuan': tiet_khuan,
        'cap_phat': cap_phat
    }

class TraceabilityDialog(QDialog):
    def __init__(self, db=None, parent=None, initial_keyword=None):
        super().__init__(parent)
        self.db = db or DBManager()
        self.setWindowTitle("🔍 Truy Vết Dụng Cụ — Xuôi & Ngược")
        self.resize(1100, 750)
        
        self._suggest_map = []
        self._current_ma_do = None
        
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._on_search_debounce)
        
        self._build_ui()
        
        if initial_keyword:
            self.txt_search.setText(initial_keyword)
            self._do_trace()
            
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # Title
        lbl = QLabel("TRUY VẾT DỤNG CỤ — LỊCH SỬ TOÀN TRÌNH")
        lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; padding: 6px;")
        layout.addWidget(lbl)
        
        # Search bar
        search_frame = QFrame()
        search_frame.setStyleSheet("background:#f0f4f8; border-radius:6px; padding:4px;")
        sh = QHBoxLayout(search_frame)
        
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Nhập tên đồ, mã đồ hoặc quét QR...")
        self.txt_search.setStyleSheet("font-size: 14px; padding: 8px; border:1px solid #bdc3c7; border-radius:4px;")
        self.txt_search.textChanged.connect(self._on_text_changed)
        self.txt_search.returnPressed.connect(self._do_trace)
        
        btn_trace = QPushButton("🔍 Truy vết")
        btn_trace.setStyleSheet("background:#e67e22; color:white; font-weight:bold; padding:8px 16px; border-radius:4px;")
        btn_trace.clicked.connect(self._do_trace)
        
        sh.addWidget(self.txt_search)
        sh.addWidget(btn_trace)
        layout.addWidget(search_frame)
        
        # Autocomplete list
        self.list_suggest = QListWidget()
        self.list_suggest.setMaximumHeight(180)
        self.list_suggest.setStyleSheet("font-size: 13px;")
        self.list_suggest.hide()
        self.list_suggest.itemClicked.connect(self._on_suggest_clicked)
        layout.addWidget(self.list_suggest)
        
        # Result label
        self.lbl_result = QLabel("")
        self.lbl_result.setStyleSheet("font-size: 14px; font-weight: bold; color:#2980b9; padding:4px;")
        layout.addWidget(self.lbl_result)
        
        # Timeline TreeWidget
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Giai Đoạn / Chi Tiết", "Thời Gian", "Người Thực Hiện", "Thông Tin Thêm", "Trạng Thái"])
        self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree.setStyleSheet("font-size: 13px;")
        layout.addWidget(self.tree)
        
        # Bottom buttons
        bl = QHBoxLayout()
        btn_reverse = QPushButton("🔄 Truy vết NGƯỢC (từ phiếu cấp phát → nguồn gốc)")
        btn_reverse.setStyleSheet("background:#8e44ad; color:white; font-weight:bold; padding:8px;")
        btn_reverse.clicked.connect(self._do_reverse_trace)
        
        btn_close = QPushButton("ĐÓNG")
        btn_close.clicked.connect(self.accept)
        
        bl.addWidget(btn_reverse)
        bl.addStretch()
        bl.addWidget(btn_close)
        layout.addLayout(bl)
        
    def _on_text_changed(self, text):
        self._timer.stop()
        self._timer.start(400)
        
    def _on_search_debounce(self):
        keyword = self.txt_search.text().strip()
        self._do_autocomplete(keyword)
        
    def _do_autocomplete(self, keyword):
        self.list_suggest.clear()
        self._suggest_map = []
        if len(keyword) < 2:
            self.list_suggest.hide()
            return
            
        results = []
        # Bo
        rows = self.db.fetch_all("SELECT ma_bo as ma, ten_bo as ten FROM danh_muc_bo_dung_cu WHERE ten_bo LIKE %s OR ma_bo LIKE %s LIMIT 5", (f"%{keyword}%", f"%{keyword}%"))
        for r in rows: results.append({'ma': r['ma'], 'ten': r['ten'], 'loai': 'BỘ DỤNG CỤ'})
        # Vai
        rows = self.db.fetch_all("SELECT ma_do_vai as ma, ten_do_vai as ten FROM danh_muc_do_vai WHERE ten_do_vai LIKE %s OR ma_do_vai LIKE %s LIMIT 5", (f"%{keyword}%", f"%{keyword}%"))
        for r in rows: results.append({'ma': r['ma'], 'ten': r['ten'], 'loai': 'ĐỒ VẢI'})
        # Dung cu
        rows = self.db.fetch_all("SELECT ma_dc as ma, ten_dc as ten FROM danh_muc_dung_cu WHERE ten_dc LIKE %s OR ma_dc LIKE %s LIMIT 5", (f"%{keyword}%", f"%{keyword}%"))
        for r in rows: results.append({'ma': r['ma'], 'ten': r['ten'], 'loai': 'DỤNG CỤ'})
        
        if results:
            self._suggest_map = results
            for r in results:
                self.list_suggest.addItem(f"[{r['loai']}] {r['ten']} | Mã: {r['ma']}")
            self.list_suggest.show()
        else:
            self.list_suggest.hide()
            
    def _on_suggest_clicked(self, item):
        idx = self.list_suggest.row(item)
        if 0 <= idx < len(self._suggest_map):
            chosen = self._suggest_map[idx]
            self.txt_search.setText(chosen['ma'])
        self.list_suggest.hide()
        self._do_trace()
        
    def _do_trace(self):
        keyword = self.txt_search.text().strip()
        if not keyword: return
        self.list_suggest.hide()
        self.tree.clear()
        self._current_ma_do = keyword
        
        ten, loai = resolve_item(self.db, keyword)
        self.lbl_result.setText(f"📦 {loai}: {ten}  |  Mã: {keyword}")
        
        timeline = get_full_timeline(self.db, keyword)
        self._render_tree(timeline)
        
    def _fmt_time(self, val):
        if not val: return "—"
        if hasattr(val, 'strftime'): return val.strftime("%d/%m/%Y %H:%M")
        return str(val)[:16]
        
    def _render_tree(self, tl):
        self.tree.clear()
        
        STAGES = [
            ("📥 GIAO NHẬN", "giao_nhan", "#1a7fc1"),
            ("🧹 KHỬ NHIỄM", "khu_nhiem", "#e67e22"),
            ("🔬 TIỆT KHUẨN", "tiet_khuan", "#8e44ad"),
            ("📤 CẤP PHÁT", "cap_phat", "#27ae60"),
        ]
        
        for stage_label, key, color in STAGES:
            rows = tl.get(key, [])
            count = len(rows)
            root = QTreeWidgetItem([f"{stage_label}  ({count} lần)", "", "", "", ""])
            font = root.font(0)
            font.setBold(True)
            font.setPointSize(12)
            root.setFont(0, font)
            root.setForeground(0, QColor(color))
            self.tree.addTopLevelItem(root)
            
            if not rows:
                empty = QTreeWidgetItem(["  (Chưa có dữ liệu)", "—", "—", "—", "—"])
                empty.setForeground(0, QColor("#95a5a6"))
                root.addChild(empty)
                continue
                
            for i, r in enumerate(rows, 1):
                if key == 'giao_nhan':
                    tg = self._fmt_time(r.get('thoi_gian'))
                    tg_duyet = self._fmt_time(r.get('thoi_gian_duyet'))
                    child = QTreeWidgetItem([
                        f"  #{i}  Khoa: {r.get('khoa_giao','')}",
                        tg,
                        "Khoa Lâm Sàng",
                        f"SL: {r.get('so_luong','')} | Phiếu: {r.get('ma_phieu','')}",
                        r.get('trang_thai', '')
                    ])
                    if r.get('thoi_gian_duyet'):
                        child2 = QTreeWidgetItem(["    → KSNK Duyệt", tg_duyet, "KSNK", f"Phiếu: {r.get('ma_phieu','')}", "ĐÃ DUYỆT"])
                        child2.setForeground(4, QColor("#27ae60"))
                        child.addChild(child2)
                        
                elif key == 'khu_nhiem':
                    tg = self._fmt_time(r.get('thoi_gian'))
                    child = QTreeWidgetItem([
                        f"  #{i}  Phương pháp: {r.get('phuong_phap','')}",
                        tg,
                        r.get('nguoi_thuc_hien', ''),
                        "",
                        "ĐÃ KHỬ NHIỄM"
                    ])
                    
                elif key == 'tiet_khuan':
                    tg = self._fmt_time(r.get('thoi_gian'))
                    child = QTreeWidgetItem([
                        f"  #{i}  Phiếu: {r.get('ma_phieu','')}",
                        tg,
                        r.get('nguoi_nhan', ''),
                        f"SL: {r.get('so_luong','')}",
                        "ĐÃ TIỆT KHUẨN"
                    ])
                    
                elif key == 'cap_phat':
                    tg = self._fmt_time(r.get('thoi_gian'))
                    child = QTreeWidgetItem([
                        f"  #{i}  Khoa nhận: {r.get('khoa_nhan','')}",
                        tg,
                        r.get('nguoi_giao', ''),
                        f"SL: {r.get('so_luong','')} | Phiếu: {r.get('ma_phieu','')}",
                        "ĐÃ CẤP PHÁT"
                    ])
                    
                root.addChild(child)
                
        self.tree.expandAll()
        
    def _do_reverse_trace(self):
        if not self._current_ma_do:
            QMessageBox.information(self, "Thông báo", "Hãy tìm kiếm & chọn đồ cần truy ngược trước.")
            return
            
        cap_rows = self.db.fetch_all(
            "SELECT pcp.ma_phieu, pcp.thoi_gian, pcp.khoa_nhan, pcp.nguoi_giao, ctcp.so_luong "
            "FROM chi_tiet_cap_phat ctcp "
            "JOIN phieu_cap_phat pcp ON ctcp.ma_phieu=pcp.ma_phieu "
            "WHERE ctcp.ma_do=%s ORDER BY pcp.thoi_gian DESC LIMIT 1", (self._current_ma_do,)
        ) or []
        
        if not cap_rows:
            QMessageBox.information(self, "Truy Vết Ngược", f"Mã [{self._current_ma_do}] chưa từng được cấp phát.")
            return
            
        last_cap = cap_rows[0]
        msg = f"🔄 TRUY VẾT NGƯỢC — Mã: {self._current_ma_do}\n\n"
        msg += f"📤 Cấp phát gần nhất:\n   → Khoa nhận: {last_cap.get('khoa_nhan')}\n   → Thời gian: {self._fmt_time(last_cap.get('thoi_gian'))}\n   → Người giao: {last_cap.get('nguoi_giao')}\n\n"
        
        khu = self.db.fetch_all("SELECT nguoi_thuc_hien, phuong_phap, thoi_gian FROM nhat_ky_khu_nhiem WHERE ma_do=%s ORDER BY thoi_gian DESC LIMIT 1", (self._current_ma_do,))
        if khu:
            msg += f"🧹 Khử nhiễm gần nhất:\n   → Người: {khu[0].get('nguoi_thuc_hien')}\n   → Phương pháp: {khu[0].get('phuong_phap')}\n   → Lúc: {self._fmt_time(khu[0].get('thoi_gian'))}\n\n"
        else:
            msg += "🧹 Khử nhiễm: Không có dữ liệu\n\n"
            
        giao = self.db.fetch_all("SELECT khoa_giao, so_luong, thoi_gian, ma_phieu FROM lich_su_giao_nhan WHERE ma_do=%s ORDER BY thoi_gian DESC LIMIT 1", (self._current_ma_do,))
        if giao:
            msg += f"📥 Nguồn gốc giao nhận:\n   → Khoa gửi: {giao[0].get('khoa_giao')}\n   → Số lượng: {giao[0].get('so_luong')}\n   → Thời gian nhận: {self._fmt_time(giao[0].get('thoi_gian'))}\n   → Mã phiếu: {giao[0].get('ma_phieu')}"
        else:
            msg += "📥 Giao nhận: Không có dữ liệu"
            
        QMessageBox.information(self, "🔄 Kết quả Truy Vết Ngược", msg)
