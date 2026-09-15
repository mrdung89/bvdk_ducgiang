import sys

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\views\assembly.py', 'r', encoding='utf-8') as f:
    c = f.read()

new_refresh_session_cb = '''    def refresh_session_cb(self):
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
            print("Error refresh_session_cb:", e)'''

new_tai_ds_phien = '''    def tai_ds_phien(self):
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
            print("Error tai ds:", e)'''

new_render_table = '''    def render_table(self, ds):
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
                print("Error rendering row:", e)'''

import re
c = re.sub(r'    def refresh_session_cb\(self\):.*?def tai_ds_phien\(self\):', new_refresh_session_cb + '\n\n    def tai_ds_phien(self):', c, flags=re.DOTALL)
c = re.sub(r'    def tai_ds_phien\(self\):.*?def render_table\(self, ds\):', new_tai_ds_phien + '\n\n    def render_table(self, ds):', c, flags=re.DOTALL)
c = re.sub(r'    def render_table\(self, ds\):.*?def do_print\(self', new_render_table + '\n\n    def do_print(self', c, flags=re.DOTALL)

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\views\assembly.py', 'w', encoding='utf-8') as f:
    f.write(c)
