from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                               QComboBox, QRadioButton, QButtonGroup, QScrollArea, QFrame,
                               QGridLayout, QSpinBox, QMessageBox, QLineEdit)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
from models.db_manager import DBManager
import utils.intem_backend as backend
from datetime import datetime, timedelta
import math
import os

class AssemblyPage(QWidget):
    def __init__(self):
        super().__init__()
        self.db = DBManager()
        self.list_items = []
        self.map_ma_phien = {}
        
        self.setup_ui()
        backend.CURRENT_PRINTER_NAME = None
        backend.CURRENT_USER_FULLNAME = 'NV KSNK'
        self.refresh_session_cb()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("IN TEM TỰ ĐỘNG (THAY THẾ ĐÓNG GÓI)")
        header.setFont(QFont("Arial", 22, QFont.Bold))
        layout.addWidget(header)
        
        # Filters
        fr_body = QFrame()
        fr_body.setStyleSheet("background-color: #ecf0f1;")
        body_layout = QVBoxLayout(fr_body)
        
        # Search
        fr_qr = QHBoxLayout()
        fr_qr.addWidget(QLabel("Quét Mã / Nhập Tên:"))
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Gõ mã đồ để tìm nhanh...")
        fr_qr.addWidget(self.txt_search)
        body_layout.addLayout(fr_qr)
        
        # Dropdowns
        fr_opt = QHBoxLayout()
        fr_opt.addWidget(QLabel("Hạn:"))
        self.cb_h = QComboBox()
        self.cb_h.addItems(["", "7", "30", "90", "180"])
        fr_opt.addWidget(self.cb_h)
        
        fr_opt.addWidget(QLabel("PP:"))
        self.cb_p = QComboBox()
        self.cb_p.addItems(["", "EO", "Plasma", "Hơi nước"])
        fr_opt.addWidget(self.cb_p)
        fr_opt.addStretch()
        body_layout.addLayout(fr_opt)
        
        # Radios
        fr_ph = QHBoxLayout()
        fr_ph.addWidget(QLabel("Lọc:"))
        self.radio_group = QButtonGroup()
        
        self.r_all = QRadioButton("Tất cả")
        self.r_all.setChecked(True)
        self.r_pt = QRadioButton("Phẫu thuật")
        self.r_tt = QRadioButton("Thủ thuật")
        
        self.radio_group.addButton(self.r_all, 1)
        self.radio_group.addButton(self.r_pt, 2)
        self.radio_group.addButton(self.r_tt, 3)
        
        self.r_all.toggled.connect(self.refresh_session_cb)
        self.r_pt.toggled.connect(self.refresh_session_cb)
        self.r_tt.toggled.connect(self.refresh_session_cb)
        
        fr_ph.addWidget(self.r_all)
        fr_ph.addWidget(self.r_pt)
        fr_ph.addWidget(self.r_tt)
        
        fr_ph.addWidget(QLabel("Chọn Phiên:"))
        self.cb_ph_display = QComboBox()
        self.cb_ph_display.setMinimumWidth(300)
        fr_ph.addWidget(self.cb_ph_display)
        
        btn_tai = QPushButton("TẢI DS")
        btn_tai.setStyleSheet("background-color: #2980b9; color: white; font-weight: bold;")
        btn_tai.clicked.connect(self.tai_ds_phien)
        fr_ph.addWidget(btn_tai)
        fr_ph.addStretch()
        body_layout.addLayout(fr_ph)
        
        # Actions
        fr_act = QHBoxLayout()
        
        def mk_act(txt, color):
            b = QPushButton(txt)
            b.setStyleSheet(f"background-color: {color}; color: white; font-weight: bold; padding: 5px;")
            b.clicked.connect(lambda: self.print_bulk(txt))
            fr_act.addWidget(b)
            
        mk_act("TOÀN BỘ", "#2980b9")
        mk_act("BỘ", "#16a085")
        mk_act("ĐỒ LẺ", "#d35400")
        mk_act("Hơi nước", "#27ae60")
        mk_act("EO", "#f39c12")
        mk_act("Plasma", "#8e44ad")
        fr_act.addStretch()
        body_layout.addLayout(fr_act)
        
        # Scroll Area for items
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(self.scroll_content)
        body_layout.addWidget(self.scroll)
        
        # Status
        fr_b = QHBoxLayout()
        self.lbl_status = QLabel("Sẵn sàng...")
        self.lbl_status.setStyleSheet("color: gray; font-style: italic;")
        fr_b.addWidget(self.lbl_status)
        fr_b.addStretch()
        
        btn_thu_cong = QPushButton("IN THỦ CÔNG")
        btn_thu_cong.setStyleSheet("background-color: #e67e22; color: white; font-weight: bold;")
        fr_b.addWidget(btn_thu_cong)
        body_layout.addLayout(fr_b)
        
        layout.addWidget(fr_body)

    def refresh_session_cb(self):
        try:
            self.cb_ph_display.clear()
            self.map_ma_phien.clear()
            
            q = "SELECT ma_phieu, MAX(khoa_nhan) as khoa, MAX(thoi_gian) as thoi_gian FROM lich_su_giao_nhan WHERE trang_thai='DA_KHU_NHIEM' GROUP BY ma_phieu ORDER BY thoi_gian DESC"
            rows = self.db.fetch_all(q)
            for r in rows:
                ma = r.get('ma_phieu', '')
                khoa = r.get('khoa', '')
                tg = r.get('thoi_gian', '')
                tg_str = tg.strftime('%H:%M %d/%m') if hasattr(tg, 'strftime') else str(tg)
                disp = f"{ma} - {khoa} - {tg_str}"
                self.map_ma_phien[disp] = ma
                self.cb_ph_display.addItem(disp)
        except Exception as e:
            print("Error refresh_session_cb:", e)

    def tai_ds_phien(self):
        d_str = self.cb_ph_display.currentText()
        if not d_str: return
        real_ma = self.map_ma_phien.get(d_str)
        if not real_ma: return
        
        try:
            ds = self.db.fetch_all("SELECT * FROM lich_su_giao_nhan WHERE ma_phieu=%s AND trang_thai='DA_KHU_NHIEM'", (real_ma,))
            if ds:
                self.render_table(ds)
            else:
                QMessageBox.information(self, "TB", "Phiên trống hoặc đã đóng gói")
        except Exception as e:
            print("Error tai ds:", e)

    def render_table(self, ds):
        # Clear old items
        for i in reversed(range(self.scroll_layout.count())): 
            w = self.scroll_layout.itemAt(i).widget()
            if w: w.setParent(None)
            
        self.list_items = []
        
        for idx, r in enumerate(ds):
            try:
                id_item = r.get('id')
                ma_do = r.get('ma_do', '')
                t = r.get('ten_do', '')
                sl_tong = r.get('so_luong', 1)
                k_ten = r.get('khoa_nhan', '')
                
                is_le = False
                pp = "STEAM"
                h = 30
                
                is_digit = str(ma_do).isdigit()
                try:
                    res1 = self.db.fetch_one("SELECT phuong_phap_tiet_khuan, han_tiet_khuan FROM danh_muc_bo_dung_cu WHERE ma_bo=%s" + (" OR id=%s" if is_digit else ""), ((ma_do, ma_do) if is_digit else (ma_do,)))
                    if res1:
                        pp = res1.get('phuong_phap_tiet_khuan') or "STEAM"
                        h = res1.get('han_tiet_khuan') or 30
                    else:
                        res2 = self.db.fetch_one("SELECT han_tiet_khuan FROM danh_muc_do_vai WHERE ma_do_vai=%s" + (" OR id=%s" if is_digit else ""), ((ma_do, ma_do) if is_digit else (ma_do,)))
                        if res2:
                            h = res2.get('han_tiet_khuan') or 30
                            is_le = True
                        else:
                            res3 = self.db.fetch_one("SELECT phuong_phap_tiet_khuan, han_tiet_khuan FROM danh_muc_dung_cu WHERE ma_dc=%s" + (" OR id=%s" if is_digit else ""), ((ma_do, ma_do) if is_digit else (ma_do,)))
                            if res3:
                                pp = res3.get('phuong_phap_tiet_khuan') or "STEAM"
                                h = res3.get('han_tiet_khuan') or 30
                                is_le = True
                except: pass
                
                fr = QFrame()
                fr.setStyleSheet("background-color: white; border: 1px solid #bdc3c7;")
                l = QHBoxLayout(fr)
                
                lbl = QLabel(f"[{ma_do}] {t} (Hạn: {h} ngày - PP: {pp})")
                lbl.setStyleSheet("border: none;")
                l.addWidget(lbl)
                
                spin = QSpinBox()
                spin.setRange(0, 999)
                spin.setValue(int(sl_tong))
                l.addWidget(spin)
                
                btn = QPushButton("IN")
                btn.setStyleSheet("background-color: #3498db; color: white; border: none; padding: 5px;")
                btn.clicked.connect(lambda ch, i=id_item, l=is_le, ten=t, kt=k_ten, hn=h, pt=pp, sp=spin: self.do_print(i, l, ten, kt, hn, pt, sp.value()))
                l.addWidget(btn)
                
                self.scroll_layout.addWidget(fr)
                
                self.list_items.append({
                    'id': id_item, 'is_le': is_le, 'ten': t,
                    'khoa_ten': k_ten, 'han': h, 'pp': pp, 'spin': spin
                })
            except Exception as e:
                print("Error rendering row:", e)

    def do_print(self, item_id, is_le, t, k_ten, h_db, pp_db, n):
        if n <= 0: return
        today = datetime.today()
        han_days = h_db if str(h_db).isdigit() else 30
        han = today + timedelta(days=int(han_days))
        
        pp = self.cb_p.currentText() if self.cb_p.currentText() else pp_db
        loai_str = "thu_thuat" if str(is_le) == "thu_thuat" else ("LẺ" if is_le else "BỘ")
        
        try:
            path = backend.tao_anh_tem(item_id, t, k_ten, k_ten, today.strftime('%d/%m/%Y'), han.strftime('%d/%m/%Y'), loai_str, "NV KSNK", pp)
            # Fetch default printer
            for _ in range(n):
                backend.thuc_hien_in(path)
            
            # Update DB to DA_DONG_GOI
            self.db.execute("UPDATE lich_su_giao_nhan SET trang_thai='DA_DONG_GOI' WHERE id=%s", (item_id,))
            
            self.lbl_status.setText(f"Đã in tem {t}")
        except Exception as e:
            QMessageBox.warning(self, "Lỗi in", str(e))

    def print_bulk(self, mode):
        c = 0
        for i in self.list_items:
            n = i['spin'].value()
            if n > 0:
                should_print = False
                if mode == "TOÀN BỘ": should_print = True
                elif mode == "BỘ" and not i['is_le']: should_print = True
                elif mode == "ĐỒ LẺ" and i['is_le']: should_print = True
                elif i['pp'] == mode: should_print = True
                
                if should_print:
                    self.do_print(i['id'], i['is_le'], i['ten'], i['khoa_ten'], i['han'], i['pp'], n)
                    c += n
        self.lbl_status.setText(f"Đã in xong {c} tem ({mode})")
