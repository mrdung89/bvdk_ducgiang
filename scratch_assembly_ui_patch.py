import sys

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\views\assembly.py', 'r', encoding='utf-8') as f:
    c = f.read()

import re

# 1. Update refresh_session_cb display format
new_format = '''                tg_str = tg.strftime('%H:%M - %d/%m') if hasattr(tg, 'strftime') else str(tg)
                disp = f"{khoa} : {tg_str}"
                if disp in self.map_ma_phien:
                    disp = f"{khoa} : {tg_str} ({str(ma)[-4:]})"'''
c = re.sub(r"                tg_str = tg\.strftime\('%H:%M %d/%m'\).*?disp = f\"\{ma\} - \{khoa\} - \{tg_str\}\"", new_format, c, flags=re.DOTALL)

# 2. Update render_table to fetch 't' (ten_bo/ten_dc) and update color
new_render_sql = '''                is_digit = str(ma_do).isdigit()
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
                except: pass'''

c = re.sub(r'                is_digit = str\(ma_do\)\.isdigit\(\).*?except: pass', new_render_sql, c, flags=re.DOTALL)

# 3. Update lambda and list_items in render_table
new_append = '''                btn.clicked.connect(lambda ch, i=id_item, l=is_le, ten=t, kt=k_ten, hn=h, pt=pp, sp=spin, f=fr, b=btn: self.on_print_single(i, l, ten, kt, hn, pt, sp, f, b))
                l.addWidget(btn)
                
                self.scroll_layout.addWidget(fr)
                
                self.list_items.append({
                    'id': id_item, 'is_le': is_le, 'ten': t,
                    'khoa_ten': k_ten, 'han': h, 'pp': pp, 'spin': spin, 'frame': fr, 'btn': btn, 'printed': False
                })'''
c = re.sub(r'                btn\.clicked\.connect\(lambda ch, i=id_item.*?\n                \}\)', new_append, c, flags=re.DOTALL)

# 4. Add on_print_single
new_on_print_single = '''    def on_print_single(self, i, l, ten, kt, hn, pt, sp, f, b):
        success = self.do_print(i, l, ten, kt, hn, pt, sp.value())
        if success:
            f.setStyleSheet("background-color: #d4edda; border: 1px solid #c3e6cb;")
            b.setStyleSheet("background-color: #27ae60; color: white; border: none; padding: 5px;")
            b.setText("ĐÃ IN")
            for item in self.list_items:
                if item['id'] == i:
                    item['printed'] = True

    def on_scan'''
c = c.replace('    def on_scan', new_on_print_single)

# 5. Modify do_print to return True/False
c = c.replace('if n <= 0: return', 'if n <= 0: return False')
c = c.replace('self.lbl_status.setText(f"Đã in tem {t}")', 'self.lbl_status.setText(f"Đã in tem {t}")\n            return True')
c = c.replace('QMessageBox.warning(self, "Lỗi in", str(e))', 'QMessageBox.warning(self, "Lỗi in", str(e))\n            return False')

# 6. Modify print_bulk to skip printed and mark printed
new_print_bulk = '''    def print_bulk(self, mode):
        c = 0
        for i in self.list_items:
            if i.get('printed', False): continue
            
            n = i['spin'].value()
            if n > 0:
                should_print = False
                if mode == "TOÀN BỘ": should_print = True
                elif mode == "BỘ" and not i['is_le']: should_print = True
                elif mode == "ĐỒ LẺ" and i['is_le']: should_print = True
                elif i['pp'] == mode: should_print = True
                
                if should_print:
                    success = self.do_print(i['id'], i['is_le'], i['ten'], i['khoa_ten'], i['han'], i['pp'], n)
                    if success:
                        i['printed'] = True
                        i['frame'].setStyleSheet("background-color: #d4edda; border: 1px solid #c3e6cb;")
                        i['btn'].setStyleSheet("background-color: #27ae60; color: white; border: none; padding: 5px;")
                        i['btn'].setText("ĐÃ IN")
                        c += n
        self.lbl_status.setText(f"Đã in xong {c} tem ({mode})")'''
c = re.sub(r'    def print_bulk\(self, mode\):.*?Đã in xong \{c\} tem \(\{mode\}\)"\)', new_print_bulk, c, flags=re.DOTALL)

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\views\assembly.py', 'w', encoding='utf-8') as f:
    f.write(c)
