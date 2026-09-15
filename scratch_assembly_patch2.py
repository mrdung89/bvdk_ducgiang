import sys

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\views\assembly.py', 'r', encoding='utf-8') as f:
    c = f.read()

new_do_pack = '''    def do_pack(self):
        selected_items = []
        for i in range(self.tree.topLevelItemCount()):
            parent = self.tree.topLevelItem(i)
            for j in range(parent.childCount()):
                child = parent.child(j)
                if child.checkState(0) == Qt.Checked:
                    pid = child.data(0, Qt.UserRole)
                    ma_do = child.text(0)
                    ten_do = child.text(1)
                    selected_items.append({'id': pid, 'ma_do': ma_do, 'ten_do': ten_do})
                    
        if not selected_items:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng tích chọn ít nhất 1 món đồ để đóng gói & in tem!")
            return
            
        success_count = 0
        for it in selected_items:
            ma = it['ma_do']
            is_digit = str(ma).isdigit()
            
            # Fetch attributes from DB
            pptk = ""
            han_tiet_khuan = 30
            try:
                q1 = "SELECT phuong_phap_tiet_khuan, han_tiet_khuan FROM danh_muc_bo_dung_cu WHERE ma_bo=%s" + (" OR id=%s" if is_digit else "")
                p1 = (ma, ma) if is_digit else (ma,)
                res1 = self.db.fetch_one(q1, p1)
                if res1:
                    pptk = res1.get('phuong_phap_tiet_khuan') or "STEAM"
                    han_tiet_khuan = res1.get('han_tiet_khuan') or 30
                else:
                    q2 = "SELECT han_tiet_khuan FROM danh_muc_do_vai WHERE ma_do_vai=%s" + (" OR id=%s" if is_digit else "")
                    p2 = (ma, ma) if is_digit else (ma,)
                    res2 = self.db.fetch_one(q2, p2)
                    if res2:
                        pptk = "STEAM"
                        han_tiet_khuan = res2.get('han_tiet_khuan') or 30
                    else:
                        q3 = "SELECT phuong_phap_tiet_khuan, han_tiet_khuan FROM danh_muc_dung_cu WHERE ma_dc=%s" + (" OR id=%s" if is_digit else "")
                        p3 = (ma, ma) if is_digit else (ma,)
                        res3 = self.db.fetch_one(q3, p3)
                        if res3:
                            pptk = res3.get('phuong_phap_tiet_khuan') or "STEAM"
                            han_tiet_khuan = res3.get('han_tiet_khuan') or 30
            except Exception as e:
                print("DB fetch error:", e)
                pass
                
            success = print_assembly_label(self, it['ma_do'], it['ten_do'], "NV Đóng Gói", pptk, han_tiet_khuan)
            if success:
                try:
                    self.db.execute("UPDATE lich_su_giao_nhan SET trang_thai='DA_DONG_GOI' WHERE id=%s", (it['id'],))
                    success_count += 1
                except: pass
                
        QMessageBox.information(self, "Thành công", f"Đã đóng gói và in tem thành công cho {success_count} / {len(selected_items)} đồ!")
        self.load_items()
'''

start = c.find('    def do_pack(self):')
c = c[:start] + new_do_pack

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\views\assembly.py', 'w', encoding='utf-8') as f:
    f.write(c)
