from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QTableWidget, QTableWidgetItem, QHeaderView, 
                               QMessageBox, QTabWidget, QInputDialog, QDialog, 
                               QLineEdit, QComboBox, QCheckBox, QAbstractItemView)
from PySide6.QtCore import Qt
from models.db_manager import DBManager


class LinkDialog(QDialog):
    def __init__(self, parent, title, link_data=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(500, 200)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Ten goi nho:"))
        self.txt_ten = QLineEdit()
        layout.addWidget(self.txt_ten)
        layout.addWidget(QLabel("Duong dan (URL):"))
        self.txt_url = QLineEdit()
        layout.addWidget(self.txt_url)
        layout.addWidget(QLabel("Loai Link:"))
        self.cb_loai = QComboBox()
        self.cb_loai.addItems(["Google Form Dong Bo", "Tai Lieu HDSD", "Khac"])
        layout.addWidget(self.cb_loai)
        if link_data:
            self.txt_ten.setText(link_data.get('ten_link', ''))
            self.txt_url.setText(link_data.get('url', ''))
            self.cb_loai.setCurrentText(link_data.get('loai_link', ''))
        hl = QHBoxLayout()
        btn_save = QPushButton("Luu")
        btn_save.clicked.connect(self.accept)
        btn_cancel = QPushButton("Huy")
        btn_cancel.clicked.connect(self.reject)
        hl.addWidget(btn_save)
        hl.addWidget(btn_cancel)
        layout.addLayout(hl)
    def get_data(self):
        return {"ten_link": self.txt_ten.text().strip(), "url": self.txt_url.text().strip(), "loai_link": self.cb_loai.currentText()}


class SettingsPage(QWidget):
    def __init__(self, user_data=None):
        super().__init__()
        self.user_data = user_data
        self.db = DBManager()
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Tab 1: Links
        self.tab_links = QWidget()
        self.setup_links_tab()
        self.tabs.addTab(self.tab_links, "Cau Hinh Links (GG Form/Drive)")
        
        # Tab 2: Mapping
        self.tab_mapping = QWidget()
        self.setup_mapping_tab()
        self.tabs.addTab(self.tab_mapping, "Mapping Form -> Ma Do")

        # Tab 3: Print Settings
        self.tab_print = QWidget()
        self.setup_print_tab()
        self.tabs.addTab(self.tab_print, "Cài Đặt In Tem")


    # -------- LINKS TAB --------
    def setup_links_tab(self):
        layout = QVBoxLayout(self.tab_links)
        hl = QHBoxLayout()
        btn_add = QPushButton("Them Link Moi")
        btn_add.clicked.connect(self.add_link)
        btn_edit = QPushButton("Sua Link")
        btn_edit.clicked.connect(self.edit_link)
        btn_delete = QPushButton("Xoa Link")
        btn_delete.clicked.connect(self.delete_link)
        hl.addWidget(btn_add); hl.addWidget(btn_edit); hl.addWidget(btn_delete); hl.addStretch()
        layout.addLayout(hl)
        self.table_links = QTableWidget(0, 4)
        self.table_links.setHorizontalHeaderLabels(["ID", "Ten Link", "Loai", "URL"])
        self.table_links.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table_links.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_links.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table_links)
        self.load_links()

    def load_links(self):
        try:
            links = self.db.get_links()
            self.table_links.setRowCount(len(links))
            for r, row in enumerate(links):
                self.table_links.setItem(r, 0, QTableWidgetItem(str(row['id'])))
                self.table_links.setItem(r, 1, QTableWidgetItem(row['ten_link']))
                self.table_links.setItem(r, 2, QTableWidgetItem(row['loai_link']))
                self.table_links.setItem(r, 3, QTableWidgetItem(row['url']))
        except Exception as e:
            print("Error loading links:", e)

    def add_link(self):
        dlg = LinkDialog(self, "Them Link Moi")
        if dlg.exec():
            data = dlg.get_data()
            if not data['ten_link'] or not data['url']:
                QMessageBox.warning(self, "Loi", "Vui long nhap du thong tin!")
                return
            self.db.add_link(data['ten_link'], data['url'], data['loai_link'])
            self.load_links()

    def edit_link(self):
        row = self.table_links.currentRow()
        if row < 0: return
        link_id = self.table_links.item(row, 0).text()
        link_data = {"ten_link": self.table_links.item(row, 1).text(), "loai_link": self.table_links.item(row, 2).text(), "url": self.table_links.item(row, 3).text()}
        dlg = LinkDialog(self, "Sua Link", link_data)
        if dlg.exec():
            data = dlg.get_data()
            self.db.update_link(link_id, data['ten_link'], data['url'], data['loai_link'])
            self.load_links()

    def delete_link(self):
        row = self.table_links.currentRow()
        if row < 0: return
        link_id = self.table_links.item(row, 0).text()
        if QMessageBox.question(self, "Xac nhan", "Xoa link nay?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.db.delete_link(link_id)
            self.load_links()

    # -------- MAPPING TAB --------
    def setup_mapping_tab(self):
        layout = QVBoxLayout(self.tab_mapping)
        
        info = QLabel("Mapping ten cot Google Form -> Ma do trong he thong.\nCac dong mau vang can kiem tra lai. Tick 'Da xac nhan' de dong bo chinh xac.")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        hl = QHBoxLayout()
        btn_auto = QPushButton("Tu dong match lai")
        btn_auto.clicked.connect(self.auto_remap)
        btn_confirm_all = QPushButton("Xac nhan tat ca")
        btn_confirm_all.clicked.connect(self.confirm_all)
        btn_save = QPushButton("Luu tat ca thay doi")
        btn_save.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        btn_save.clicked.connect(self.save_mappings)
        hl.addWidget(btn_auto); hl.addWidget(btn_confirm_all); hl.addStretch(); hl.addWidget(btn_save)
        layout.addLayout(hl)
        
        self.table_mapping = QTableWidget(0, 5)
        self.table_mapping.setHorizontalHeaderLabels(["Ten cot Form", "Ma Do DB", "Ten DB", "Loai", "Da xac nhan"])
        self.table_mapping.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table_mapping.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table_mapping.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table_mapping)
        
        self.load_mappings()

    def load_mappings(self):
        try:
            self.db.execute("""
                CREATE TABLE IF NOT EXISTS form_column_mapping (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    form_col VARCHAR(200) NOT NULL,
                    ma_do VARCHAR(100),
                    loai VARCHAR(20),
                    can_xet TINYINT DEFAULT 1,
                    UNIQUE KEY uq_form_col (form_col(100))
                )
            """)
            rows = self.db.fetch_all("SELECT * FROM form_column_mapping ORDER BY can_xet DESC, form_col")
            
            # Get DB items for autocomplete
            db_vai = self.db.fetch_all("SELECT ma_do_vai as ma, ten_do_vai as ten, 'vai' as loai FROM danh_muc_do_vai")
            db_bo = self.db.fetch_all("SELECT ma_bo as ma, ten_bo as ten, 'bo' as loai FROM danh_muc_bo_dung_cu")
            self.db_items = {r['ma']: r for r in db_vai + db_bo}
            
            self.table_mapping.setRowCount(len(rows))
            for r, row in enumerate(rows):
                it_form = QTableWidgetItem(row['form_col'])
                it_form.setData(Qt.UserRole, row['id'])
                self.table_mapping.setItem(r, 0, it_form)
                
                # Ma Do - editable combobox
                cb_ma = QComboBox()
                cb_ma.setEditable(True)
                cb_ma.addItem("")
                for ma, item in self.db_items.items():
                    cb_ma.addItem(f"{ma} - {item['ten']}", ma)
                if row['ma_do']:
                    # Find and set current
                    idx = cb_ma.findData(row['ma_do'])
                    if idx >= 0:
                        cb_ma.setCurrentIndex(idx)
                    else:
                        cb_ma.setCurrentText(row['ma_do'])
                self.table_mapping.setCellWidget(r, 1, cb_ma)
                
                # Ten DB (auto-fill based on ma_do)
                ten_db = self.db_items.get(row['ma_do'], {}).get('ten', '') if row['ma_do'] else ''
                self.table_mapping.setItem(r, 2, QTableWidgetItem(ten_db))
                
                loai = self.db_items.get(row['ma_do'], {}).get('loai', row.get('loai','') or '') if row['ma_do'] else ''
                self.table_mapping.setItem(r, 3, QTableWidgetItem(str(loai)))
                
                # Xac nhan checkbox
                chk = QCheckBox()
                chk.setChecked(not row['can_xet'])
                chk_widget = QWidget()
                chk_layout = QHBoxLayout(chk_widget)
                chk_layout.addWidget(chk)
                chk_layout.setAlignment(Qt.AlignCenter)
                chk_layout.setContentsMargins(0,0,0,0)
                self.table_mapping.setCellWidget(r, 4, chk_widget)
                
                # Color rows needing review
                if row['can_xet']:
                    for c in range(5):
                        it = self.table_mapping.item(r, c)
                        if it:
                            it.setBackground(Qt.yellow)
        except Exception as e:
            print("Error loading mappings:", e)

    def save_mappings(self):
        saved = 0
        for r in range(self.table_mapping.rowCount()):
            form_id = self.table_mapping.item(r, 0).data(Qt.UserRole)
            cb_ma = self.table_mapping.cellWidget(r, 1)
            ma_do = cb_ma.currentData() or cb_ma.currentText().split(' - ')[0].strip()
            if not ma_do:
                ma_do = None
            chk_widget = self.table_mapping.cellWidget(r, 4)
            chk = chk_widget.findChild(QCheckBox)
            can_xet = 0 if chk.isChecked() else 1
            
            loai = None
            if ma_do and ma_do in self.db_items:
                loai = self.db_items[ma_do].get('loai', None)
            
            self.db.execute("UPDATE form_column_mapping SET ma_do=%s, loai=%s, can_xet=%s WHERE id=%s",
                            (ma_do, loai, can_xet, form_id))
            saved += 1
        
        QMessageBox.information(self, "Luu xong", f"Da luu {saved} mapping!")
        self.load_mappings()

    def confirm_all(self):
        self.db.execute("UPDATE form_column_mapping SET can_xet=0 WHERE ma_do IS NOT NULL")
        self.load_mappings()

    def auto_remap(self):
        QMessageBox.information(self, "Thong bao", "Tinh nang tu dong match se duoc them sau!")

    def setup_print_tab(self):
        from PySide6.QtWidgets import QSpinBox, QGroupBox, QGridLayout, QComboBox
        from PySide6.QtGui import QPainter, QImage, QFont, QPixmap, QColor
        from PySide6.QtPrintSupport import QPrinterInfo
        import qrcode
        import io
        from datetime import datetime
        
        layout = QHBoxLayout(self.tab_print)
        
        # Left side: Form controls
        left_layout = QVBoxLayout()
        group = QGroupBox("Thông số Tem (mm)")
        grid = QGridLayout(group)
        
        self.print_cfg = {
            'printer_name': '',
            'width': 50, 'height': 30, 'qr_size': 18, 'qr_x': 2, 'qr_y': 5,
            'text_x': 22, 'ma_y': 5, 'ma_size': 10,
            'ten_y': 10, 'ten_size': 8,
            'pptk_y': 15, 'pptk_size': 8,
            'ntk_y': 20, 'ntk_size': 8,
            'hsd_y': 25, 'hsd_size': 8,
            'nv_y': 28, 'nv_size': 8
        }
        self.cfg_file = 'print_config.json'
        if __import__('os').path.exists(self.cfg_file):
            try:
                import json
                self.print_cfg.update(json.load(open(self.cfg_file)))
            except: pass
            
        row = 0
        grid.addWidget(QLabel("Máy in:"), row, 0)
        self.cb_printers = QComboBox()
        self.cb_printers.addItem("--- Chọn mỗi lần in ---", "")
        for pname in QPrinterInfo.availablePrinterNames():
            self.cb_printers.addItem(pname, pname)
        # set current
        idx = self.cb_printers.findData(self.print_cfg.get('printer_name', ''))
        if idx >= 0: self.cb_printers.setCurrentIndex(idx)
        grid.addWidget(self.cb_printers, row, 1)
        row += 1
            
        self.spinboxes = {}
        # Only spinboxes for numeric keys
        for key, val in self.print_cfg.items():
            if key == 'printer_name': continue
            lbl = QLabel(key)
            spin = QSpinBox()
            spin.setRange(1, 200)
            spin.setValue(val)
            spin.valueChanged.connect(self.update_print_preview)
            self.spinboxes[key] = spin
            grid.addWidget(lbl, row, 0)
            grid.addWidget(spin, row, 1)
            row += 1
            
        btn_save = QPushButton("Lưu Cài Đặt In")
        btn_save.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        btn_save.clicked.connect(self.save_print_settings)
        grid.addWidget(btn_save, row, 0, 1, 2)
        
        left_layout.addWidget(group)
        left_layout.addStretch()
        
        # Right side: Preview
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("<b>Xem trước (Trực quan):</b>"))
        self.lbl_preview = QLabel()
        self.lbl_preview.setStyleSheet("background-color: white; border: 1px solid black;")
        self.lbl_preview.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.lbl_preview)
        right_layout.addStretch()
        
        layout.addLayout(left_layout, 1)
        layout.addLayout(right_layout, 2)
        
        self.update_print_preview()

    def update_print_preview(self):
        from PySide6.QtGui import QPainter, QImage, QFont, QPixmap, QColor
        from PySide6.QtCore import Qt
        import qrcode
        import io
        from datetime import datetime, timedelta
        
        cfg = {k: v.value() for k, v in self.spinboxes.items()}
        
        scale = 8
        w_px = cfg['width'] * scale
        h_px = cfg['height'] * scale
        
        img = QImage(w_px, h_px, QImage.Format_RGB32)
        img.fill(QColor("white"))
        
        painter = QPainter(img)
        
        qr = qrcode.QRCode(version=1, box_size=10, border=1)
        qr.add_data("BO-TEST")
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        byte_array = io.BytesIO()
        qr_img.save(byte_array, format='PNG')
        qimg_qr = QImage.fromData(byte_array.getvalue())
        
        qr_size_px = cfg['qr_size'] * scale
        painter.drawImage(cfg['qr_x'] * scale, cfg['qr_y'] * scale, qimg_qr.scaled(qr_size_px, qr_size_px, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        
        x_px = cfg['text_x'] * scale
        
        def draw_txt(y_mm, size_mm, text, bold=False):
            font = QFont("Arial")
            font.setBold(bold)
            font.setPixelSize(int(size_mm * scale * 0.35))
            painter.setFont(font)
            painter.setPen(QColor("black"))
            painter.drawText(x_px, y_mm * scale, text)
            
        draw_txt(cfg['ma_y'], cfg['ma_size'], "MÃ: BO-TEST", True)
        draw_txt(cfg['ten_y'], cfg['ten_size'], "TÊN: Bộ Kéo Răng")
        draw_txt(cfg['pptk_y'], cfg['pptk_size'], "PPTK: STEAM")
        
        now = datetime.now()
        draw_txt(cfg['ntk_y'], cfg['ntk_size'], f"NTK: {now.strftime('%d/%m/%y %H:%M')}")
        draw_txt(cfg['hsd_y'], cfg['hsd_size'], f"HSD: {(now+timedelta(days=30)).strftime('%d/%m/%y')}")
        draw_txt(cfg['nv_y'], cfg['nv_size'], f"NV: Nguyễn Văn A")
        
        painter.end()
        self.lbl_preview.setPixmap(QPixmap.fromImage(img))

    def save_print_settings(self):
        import json
        cfg = {k: v.value() for k, v in self.spinboxes.items()}
        cfg['printer_name'] = self.cb_printers.currentData()
        try:
            with open(self.cfg_file, 'w') as f:
                json.dump(cfg, f, indent=4)
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Lưu xong", "Đã lưu cài đặt in tem!")
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Lỗi", f"Không thể lưu file: {e}")
