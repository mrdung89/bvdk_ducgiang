import sys, re

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\controllers\decontamination_controller.py', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Remove SelectionPopup
start_sp = c.find('class SelectionPopup(QDialog):')
end_sp = c.find('class DecontaminationController(QObject):')
if start_sp != -1 and end_sp != -1:
    c = c[:start_sp] + c[end_sp:]

# 2. Modify DecontaminationController __init__
c = c.replace('self.view.btn_select_items.clicked.connect(self.open_selection_popup)', '')

# 3. Rewrite load_sessions
new_load_sessions = '''    def load_sessions(self):
        self.refresh_wash_machines_table()
        # Vẫn giữ dt_date phòng hờ, nhưng tải toàn bộ chờ
        self.view.tree_cart.clear()
        
        try:
            # ORDER BY thoi_gian DESC để ưu tiên phiên mới nhất lên trên
            rows = self.db.fetch_all("""
                SELECT id, khoa_giao, ma_do, so_luong, DATE_FORMAT(thoi_gian, '%d/%m %H:%i') as tm 
                FROM lich_su_giao_nhan 
                WHERE trang_thai IN ('DA_TIEP_NHAN', 'DANG_GIAT')
                ORDER BY thoi_gian DESC, id DESC
            """)
            
            # Enrich ten_do
            for r in rows:
                ma = r['ma_do']
                ten = ma
                is_digit = str(ma).isdigit()
                try:
                    q1 = "SELECT ten_bo FROM danh_muc_bo_dung_cu WHERE ma_bo=%s" + (" OR id=%s" if is_digit else "")
                    p1 = (ma, ma) if is_digit else (ma,)
                    res1 = self.db.fetch_one(q1, p1)
                    if res1: ten = res1['ten_bo']
                    else:
                        q2 = "SELECT ten_do_vai FROM danh_muc_do_vai WHERE ma_do_vai=%s" + (" OR id=%s" if is_digit else "")
                        p2 = (ma, ma) if is_digit else (ma,)
                        res2 = self.db.fetch_one(q2, p2)
                        if res2: ten = res2['ten_do_vai']
                        else:
                            q3 = "SELECT ten_dc FROM danh_muc_dung_cu WHERE ma_dc=%s" + (" OR id=%s" if is_digit else "")
                            p3 = (ma, ma) if is_digit else (ma,)
                            res3 = self.db.fetch_one(q3, p3)
                            if res3: ten = res3['ten_dc']
                except: pass
                r['ten_do'] = ten
            
            # Group by Phiên
            from collections import OrderedDict
            groups = OrderedDict()
            for r in rows:
                key = f"{r['khoa_giao']} - {r['tm']}"
                if key not in groups:
                    groups[key] = []
                groups[key].append(r)
                
            self.view.tree_cart.blockSignals(True)
            for key, items in groups.items():
                parent = QTreeWidgetItem([key, "", ""])
                parent.setCheckState(0, Qt.Unchecked)
                # Đổi màu nền cho Parent để dễ nhìn
                from PySide6.QtGui import QColor, QFont
                parent.setBackground(0, QColor("#ecf0f1"))
                parent.setBackground(1, QColor("#ecf0f1"))
                parent.setBackground(2, QColor("#ecf0f1"))
                font = QFont()
                font.setBold(True)
                parent.setFont(0, font)
                
                self.view.tree_cart.addTopLevelItem(parent)
                
                for it in items:
                    child = QTreeWidgetItem([it['ma_do'], it['ten_do'], ""])
                    child.setCheckState(0, Qt.Unchecked)
                    child.setData(0, Qt.UserRole, it['id'])
                    
                    parent.addChild(child)
                    
                    from PySide6.QtWidgets import QSpinBox
                    spin = QSpinBox()
                    spin.setMinimum(1)
                    spin.setMaximum(int(it['so_luong']))
                    spin.setValue(int(it['so_luong']))
                    spin.setStyleSheet("font-size: 16px;")
                    
                    # Store logic data in child UserRole 2
                    child.setData(2, Qt.UserRole, spin) 
                    self.view.tree_cart.setItemWidget(child, 2, spin)
                    
                parent.setExpanded(True)
            self.view.tree_cart.blockSignals(False)
            
            # Hook itemChanged
            try: self.view.tree_cart.itemChanged.disconnect()
            except: pass
            self.view.tree_cart.itemChanged.connect(self.on_tree_item_changed)
                
        except Exception as e:
            print("Error load_sessions:", e)'''

# Replace load_sessions entirely
start_ls = c.find('    def load_sessions(self):')
end_ls = c.find('    def open_selection_popup(self):')
c = c[:start_ls] + new_load_sessions + '\n\n' + c[end_ls:]

# Remove open_selection_popup and add_to_cart
start_osp = c.find('    def open_selection_popup(self):')
end_osp = c.find('    def process_washing(self, status):')
c = c[:start_osp] + c[end_osp:]

# Insert on_tree_item_changed before process_washing
item_changed_func = '''    def on_tree_item_changed(self, item, column):
        if column != 0: return
        self.view.tree_cart.blockSignals(True)
        state = item.checkState(0)
        
        # Nếu là Parent -> đổi tất cả con
        if item.parent() is None:
            for i in range(item.childCount()):
                item.child(i).setCheckState(0, state)
        else:
            # Nếu là Child -> kiểm tra lại Parent
            parent = item.parent()
            all_checked = True
            any_checked = False
            for i in range(parent.childCount()):
                if parent.child(i).checkState(0) == Qt.Checked:
                    any_checked = True
                else:
                    all_checked = False
            if all_checked: parent.setCheckState(0, Qt.Checked)
            elif any_checked: parent.setCheckState(0, Qt.PartiallyChecked)
            else: parent.setCheckState(0, Qt.Unchecked)
        self.view.tree_cart.blockSignals(False)

'''
c = c.replace('    def process_washing(self, status):', item_changed_func + '    def process_washing(self, status):')

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\controllers\decontamination_controller.py', 'w', encoding='utf-8') as f:
    f.write(c)
