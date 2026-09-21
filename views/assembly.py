from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                               QComboBox, QRadioButton, QButtonGroup, QScrollArea, QFrame,
                               QGridLayout, QSpinBox, QMessageBox, QLineEdit, QCheckBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
from models.db_manager import DBManager
import utils.intem_backend as backend
from datetime import datetime, timedelta

class AssemblyPage(QWidget):
    def __init__(self, user_data=None):
        super().__init__()
        self.user_data = user_data or {}
        self.user_fullname = self.user_data.get("full_name", "NV KSNK")
        self.db = DBManager()
        self.list_items = []
        self.map_ma_phien = {}
        
        self.setup_ui()
        backend.CURRENT_PRINTER_NAME = None
        backend.CURRENT_USER_FULLNAME = self.user_fullname
        self.refresh_session_cb()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("ĐÓNG GÓI & KIỂM TRA CHẤT LƯỢNG (ASSEMBLY)")
        header.setFont(QFont("Arial", 22, QFont.Bold))
        header.setStyleSheet("color: #2c3e50;")
        layout.addWidget(header)
        
        # Filters
        fr_body = QFrame()
        fr_body.setStyleSheet("background-color: #ecf0f1; border-radius: 8px;")
        body_layout = QVBoxLayout(fr_body)
        
        # Search & Dropdowns
        fr_top = QHBoxLayout()
        fr_top.addWidget(QLabel("Mã/Tên đồ:"))
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Quét mã QR / Barcode...")
        self.txt_search.returnPressed.connect(self.on_scan)
        fr_top.addWidget(self.txt_search)
        
        fr_top.addWidget(QLabel("Hạn (Ngày):"))
        self.cb_h = QComboBox()
        self.cb_h.setEditable(True)
        self.cb_h.addItems(["", "7", "30", "90", "180"])
        fr_top.addWidget(self.cb_h)
        
        fr_top.addWidget(QLabel("Phương pháp:"))
        self.cb_p = QComboBox()
        self.cb_p.addItems(["", "EO", "Plasma", "Hơi nước"])
        fr_top.addWidget(self.cb_p)
        body_layout.addLayout(fr_top)
        
        # Chọn Phiên chờ đóng gói
        fr_ph = QHBoxLayout()
        fr_ph.addWidget(QLabel("Chọn phiên chờ Đóng gói (Đã Khử nhiễm):"))
        self.cb_ph_display = QComboBox()
        self.cb_ph_display.setMinimumWidth(300)
        fr_ph.addWidget(self.cb_ph_display)
        
        btn_tai = QPushButton("TẢI DANH SÁCH")
        btn_tai.setStyleSheet("background-color: #2980b9; color: white; font-weight: bold; padding: 6px 15px;")
        btn_tai.clicked.connect(self.tai_ds_phien)
        fr_ph.addWidget(btn_tai)
        fr_ph.addStretch()
        body_layout.addLayout(fr_ph)
        
        # Nút đóng gói hàng loạt
        fr_act = QHBoxLayout()
        btn_bulk = QPushButton("ĐÓNG GÓI & IN TEM HÀNG LOẠT (Tất cả trên màn hình)")
        btn_bulk.setStyleSheet("background-color: #8e44ad; color: white; font-weight: bold; padding: 6px;")
        btn_bulk.clicked.connect(self.pack_bulk)
        fr_act.addWidget(btn_bulk)
        fr_act.addStretch()
        body_layout.addLayout(fr_act)
        
        # Scroll Area for items
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.scroll_layout.setSpacing(10)
        self.scroll.setWidget(self.scroll_content)
        body_layout.addWidget(self.scroll)
        
        # Status
        fr_b = QHBoxLayout()
        self.lbl_status = QLabel("Sẵn sàng...")
        self.lbl_status.setStyleSheet("color: #7f8c8d; font-style: italic; font-weight: bold;")
        fr_b.addWidget(self.lbl_status)
        fr_b.addStretch()
        
        btn_thu_cong = QPushButton("TẠO TEM THỦ CÔNG")
        btn_thu_cong.setStyleSheet("background-color: #e67e22; color: white; font-weight: bold; padding: 6px 15px;")
        btn_thu_cong.clicked.connect(self.show_manual_print)
        fr_b.addWidget(btn_thu_cong)
        body_layout.addLayout(fr_b)
        
        layout.addWidget(fr_body)

    def refresh_session_cb(self):
        try:
            self.cb_ph_display.clear()
            self.map_ma_phien.clear()
            
            # Kéo các đồ ĐÃ KHỬ NHIỄM
            q = "SELECT ma_phieu, MAX(khoa_giao) as khoa, MAX(thoi_gian) as thoi_gian FROM lich_su_giao_nhan WHERE trang_thai='DA_KHU_NHIEM' GROUP BY ma_phieu ORDER BY thoi_gian DESC"
            rows = self.db.fetch_all(q)
            for r in rows:
                ma = r.get('ma_phieu', '')
                khoa = r.get('khoa', '')
                tg = r.get('thoi_gian', '')
                tg_str = tg.strftime('%H:%M - %d/%m') if hasattr(tg, 'strftime') else str(tg)[:16]
                disp = f"{khoa} : {tg_str}"
                if disp in self.map_ma_phien:
                    disp = f"{khoa} : {tg_str} ({str(ma)[-4:]})"
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
                QMessageBox.information(self, "TB", "Phiên trống hoặc đã được đóng gói hết!")
        except Exception as e:
            print("Error tai ds:", e)

    def render_table(self, ds):
        # Xóa items cũ
        for i in reversed(range(self.scroll_layout.count())): 
            w = self.scroll_layout.itemAt(i).widget()
            if w: w.setParent(None)
            
        self.list_items = []
        
        for idx, r in enumerate(ds):
            try:
                id_item = r.get('id')
                ma_do = r.get('ma_do', '')
                t = r.get('ten_do', '')
                sl_goc = r.get('so_luong', 1)
                k_ten = r.get('khoa_giao', '')
                
                is_le = False
                pp = "STEAM"
                h = 30
                
                is_digit = str(ma_do).isdigit()
                try:
                    res1 = self.db.fetch_one("SELECT ten_bo, phuong_phap_tiet_khuan, han_tiet_khuan FROM danh_muc_bo_dung_cu WHERE ma_bo=%s" + (" OR id=%s" if is_digit else ""), ((ma_do, ma_do) if is_digit else (ma_do,)))
                    if res1:
                        t = res1.get('ten_bo') or t
                        pp = res1.get('phuong_phap_tiet_khuan') or "STEAM"
                        h = res1.get('han_tiet_khuan') or 30
                    else:
                        res2 = self.db.fetch_one("SELECT ten_do_vai, han_tiet_khuan FROM danh_muc_do_vai WHERE ma_do_vai=%s" + (" OR id=%s" if is_digit else ""), ((ma_do, ma_do) if is_digit else (ma_do,)))
                        if res2:
                            t = res2.get('ten_do_vai') or t
                            h = res2.get('han_tiet_khuan') or 30
                            is_le = True
                        else:
                            res3 = self.db.fetch_one("SELECT ten_dc, phuong_phap_tiet_khuan, han_tiet_khuan FROM danh_muc_dung_cu WHERE ma_dc=%s" + (" OR id=%s" if is_digit else ""), ((ma_do, ma_do) if is_digit else (ma_do,)))
                            if res3:
                                t = res3.get('ten_dc') or t
                                pp = res3.get('phuong_phap_tiet_khuan') or "STEAM"
                                h = res3.get('han_tiet_khuan') or 30
                                is_le = True
                except: pass
                
                # Card giao diện cho từng món đồ
                fr = QFrame()
                fr.setStyleSheet("background-color: white; border: 1px solid #bdc3c7; border-radius: 5px;")
                v_card = QVBoxLayout(fr)
                
                # Hàng 1: Tên đồ
                lbl = QLabel(f"<b>[{ma_do}] {t}</b> — (Khoa: {k_ten} | Hạn: {h} ngày | PP: {pp})")
                lbl.setStyleSheet("border: none; font-size: 15px;")
                v_card.addWidget(lbl)
                
                # Hàng 2: Controls
                h_controls = QHBoxLayout()
                
                chk_qc = QCheckBox("✔ Đã kiểm tra Sạch & Sắc bén")
                chk_qc.setStyleSheet("border: none; color: #d35400; font-weight: bold;")
                chk_qc.setChecked(True)
                h_controls.addWidget(chk_qc)
                h_controls.addStretch()
                
                h_controls.addWidget(QLabel("SL Gói:"))
                spin = QSpinBox()
                spin.setRange(1, int(sl_goc))
                spin.setValue(int(sl_goc))
                spin.setStyleSheet("font-size: 16px; border: 1px solid #bdc3c7;")
                h_controls.addWidget(spin)
                
                btn = QPushButton("ĐÓNG GÓI & IN TEM")
                btn.setStyleSheet("background-color: #27ae60; color: white; border: none; font-weight: bold; padding: 6px 12px; border-radius: 4px;")
                btn.clicked.connect(lambda ch, i=id_item, l=is_le, ten=t, kt=k_ten, hn=h, pt=pp, sp=spin, f=fr, b=btn, qc=chk_qc, slg=sl_goc: 
                                    self.on_pack_and_print(i, l, ten, kt, hn, pt, sp, f, b, qc, slg))
                h_controls.addWidget(btn)
                
                v_card.addLayout(h_controls)
                self.scroll_layout.addWidget(fr)
                
                self.list_items.append({
                    'id': id_item, 'is_le': is_le, 'ten': t, 'sl_goc': int(sl_goc),
                    'khoa_ten': k_ten, 'han': h, 'pp': pp, 'spin': spin, 'chk_qc': chk_qc, 
                    'frame': fr, 'btn': btn, 'packed': False
                })
            except Exception as e:
                print("Error rendering row:", e)

    def on_pack_and_print(self, item_id, is_le, ten, khoa, han, pp, spin_widget, frame, btn_widget, chk_qc, sl_goc):
        if not chk_qc.isChecked():
            QMessageBox.warning(self, "Cảnh báo QC", f"Vui lòng xác nhận dụng cụ [{ten}] đã đạt chuẩn Sạch & Sắc bén trước khi đóng gói!")
            return
            
        sl_dong_goi = spin_widget.value()
        if sl_dong_goi <= 0: return
        
        # 1. Gọi hàm in tem thực tế
        today = datetime.today()
        user_h = self.cb_h.currentText().strip()
        han_days = user_h if user_h.isdigit() else (han if str(han).isdigit() else 30)
        han_date = today + timedelta(days=int(han_days))
        pp_in = self.cb_p.currentText() if self.cb_p.currentText() else pp
        loai_str = "thu_thuat" if str(is_le) == "thu_thuat" else ("LẺ" if is_le else "BỘ")
        
        try:
            path = backend.tao_anh_tem(item_id, ten, khoa, khoa, today.strftime('%d/%m/%Y'), han_date.strftime('%d/%m/%Y'), loai_str, self.user_fullname, pp_in)
            for _ in range(sl_dong_goi):
                backend.thuc_hien_in(path)
        except Exception as e:
            QMessageBox.warning(self, "Lỗi in", f"Không thể in tem: {e}")
            return # Dừng nếu máy in lỗi

        # 2. Xử lý Database & Tách Phiếu
        try:
            req = self.db.fetch_one("SELECT * FROM lich_su_giao_nhan WHERE id=%s", (item_id,))
            if req:
                if sl_dong_goi < sl_goc:
                    sl_con_lai = sl_goc - sl_dong_goi
                    # Clone phiếu mới cho số thừa (giữ lại trạng thái DA_KHU_NHIEM)
                    self.db.execute("""INSERT INTO lich_su_giao_nhan 
                        (khoa_giao, ma_do, so_luong, trang_thai, thoi_gian, ma_phieu) 
                        VALUES (%s, %s, %s, %s, %s, %s)""", 
                        (req['khoa_giao'], req['ma_do'], sl_con_lai, req['trang_thai'], req['thoi_gian'], req['ma_phieu']))
                    # Cập nhật phiếu hiện tại thành DA_DONG_GOI
                    self.db.execute("UPDATE lich_su_giao_nhan SET so_luong=%s, trang_thai='DA_DONG_GOI' WHERE id=%s", (sl_dong_goi, item_id))
                else:
                    # Chọn hết thì chỉ cần update trạng thái
                    self.db.execute("UPDATE lich_su_giao_nhan SET trang_thai='DA_DONG_GOI' WHERE id=%s", (item_id,))
                
                # Ghi Audit Log
                self.db.execute("INSERT INTO lich_su_bien_dong (thoi_gian, nguoi_thuc_hien, bang_du_lieu, ma_item, noi_dung) VALUES (NOW(), %s, %s, %s, %s)", 
                       (self.user_fullname, 'lich_su_giao_nhan', item_id, f"Đóng gói & QC (SL: {sl_dong_goi})"))

            # Update UI
            frame.setStyleSheet("background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 5px;")
            btn_widget.setStyleSheet("background-color: #7f8c8d; color: white; border: none; font-weight: bold; padding: 6px;")
            btn_widget.setText("ĐÃ ĐÓNG GÓI")
            btn_widget.setEnabled(False)
            spin_widget.setEnabled(False)
            chk_qc.setEnabled(False)
            
            for item in self.list_items:
                if item['id'] == item_id: item['packed'] = True
                
            self.lbl_status.setText(f"Đã đóng gói thành công {sl_dong_goi} x [{ten}]")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi Database", str(e))

    def on_scan(self):
        qr = self.txt_search.text().strip()
        if not qr: return
        self.txt_search.clear()
        
        # Nếu quét mã mà đồ nằm trên màn hình, tự động check và click
        for item in self.list_items:
            if not item['packed'] and str(item['id']) == qr or str(item['ten']).startswith(qr):
                item['chk_qc'].setChecked(True)
                item['btn'].click()
                return
                
        self.lbl_status.setText(f"Không tìm thấy đồ khớp với mã: {qr} trong phiên này!")

    def pack_bulk(self):
        c = 0
        for i in self.list_items:
            if i.get('packed', False): continue
            # Tự động gán tick QC nếu bấm đóng gói hàng loạt
            i['chk_qc'].setChecked(True)
            i['btn'].click()
            c += 1
        if c > 0:
            self.lbl_status.setText(f"Đã đóng gói hàng loạt xong!")
            # Sau khi làm xong tự động refresh danh sách
            self.refresh_session_cb()

    def show_manual_print(self):
        from PySide6.QtWidgets import QDialog
        class ManualPrintDialog(QDialog):
            def __init__(self, parent):
                super().__init__(parent)
                self.setWindowTitle("Tạo Tem Thủ Công")
                self.resize(400, 300)
                layout = QVBoxLayout(self)
                
                layout.addWidget(QLabel("Tên dụng cụ/bộ:"))
                self.t_ten = QLineEdit()
                layout.addWidget(self.t_ten)
                
                layout.addWidget(QLabel("Khoa:"))
                self.t_khoa = QLineEdit()
                layout.addWidget(self.t_khoa)
                
                layout.addWidget(QLabel("Hạn (ngày):"))
                self.t_han = QSpinBox()
                self.t_han.setRange(1, 365)
                self.t_han.setValue(30)
                layout.addWidget(self.t_han)
                
                layout.addWidget(QLabel("Loại:"))
                self.cb_loai = QComboBox()
                self.cb_loai.addItems(["Bộ", "Đồ Lẻ", "Thủ thuật"])
                layout.addWidget(self.cb_loai)
                
                layout.addWidget(QLabel("Phương pháp:"))
                self.cb_pp = QComboBox()
                self.cb_pp.addItems(["STEAM", "EO", "PLASMA"])
                layout.addWidget(self.cb_pp)
                
                layout.addWidget(QLabel("Số lượng tem:"))
                self.t_sl = QSpinBox()
                self.t_sl.setRange(1, 100)
                self.t_sl.setValue(1)
                layout.addWidget(self.t_sl)
                
                btn_in = QPushButton("IN NGAY")
                btn_in.setStyleSheet("background-color: #e67e22; color: white; font-weight: bold; padding: 10px;")
                btn_in.clicked.connect(self.accept)
                layout.addWidget(btn_in)

        dlg = ManualPrintDialog(self)
        if dlg.exec():
            ten = dlg.t_ten.text().strip()
            khoa = dlg.t_khoa.text().strip()
            han = dlg.t_han.value()
            loai = dlg.cb_loai.currentText()
            pp = dlg.cb_pp.currentText()
            sl = dlg.t_sl.value()
            
            if not ten: return
            
            is_le = False
            if loai == "Đồ Lẻ": is_le = True
            elif loai == "Thủ thuật": is_le = "thu_thuat"
            
            today = datetime.today()
            han_date = today + timedelta(days=int(han))
            loai_str = "thu_thuat" if str(is_le) == "thu_thuat" else ("LẺ" if is_le else "BỘ")
            
            try:
                path = backend.tao_anh_tem("MANUAL", ten, khoa, khoa, today.strftime('%d/%m/%Y'), han_date.strftime('%d/%m/%Y'), loai_str, self.user_fullname, pp)
                for _ in range(sl): backend.thuc_hien_in(path)
                self.lbl_status.setText(f"Đã in {sl} tem thủ công: {ten}")
            except Exception as e:
                QMessageBox.warning(self, "Lỗi in", str(e))
