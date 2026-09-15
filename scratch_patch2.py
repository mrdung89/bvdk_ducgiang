import sys, re

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\controllers\decontamination_controller.py', 'r', encoding='utf-8') as f:
    c = f.read()

new_process_washing = '''    def process_washing(self, status):
        count = self.view.tree_cart.topLevelItemCount()
        if count == 0:
            QMessageBox.warning(self.view, "Cảnh báo", "Không có dữ liệu!")
            return
            
        # Thu thập các mục được chọn
        selected_items = []
        for i in range(count):
            parent = self.view.tree_cart.topLevelItem(i)
            for j in range(parent.childCount()):
                child = parent.child(j)
                if child.checkState(0) == Qt.Checked:
                    pid = child.data(0, Qt.UserRole)
                    spin = child.data(2, Qt.UserRole)
                    if spin:
                        sl_chon = spin.value()
                        selected_items.append({'id': pid, 'sl': sl_chon})
                        
        if not selected_items:
            QMessageBox.warning(self.view, "Cảnh báo", "Vui lòng tích chọn ít nhất 1 món đồ!")
            return

        # Nếu bấm "Rửa máy" thì mở dialog chọn máy & chu trình
        if status == "WASHING":
            # Lưu tạm vào biến để truyền qua máy
            self.temp_selected_items = selected_items
            self.open_washing_machine_dialog()
            return
            
        nguoi_thuc_hien = self.view.cb_employee.currentText()
        phuong_phap = "Rửa thủ công"
            
        try:
            for p_data in selected_items:
                pid = p_data['id']
                sl_chon = p_data['sl']
                
                # 1. Check database lấy số lượng gốc
                row = self.db.fetch_one("SELECT so_luong, ma_do, khoa_giao FROM lich_su_giao_nhan WHERE id=%s", (pid,))
                if not row: continue
                sl_goc = int(row['so_luong'])
                
                # 2. Tạo log (rửa thủ công)
                if sl_chon >= sl_goc:
                    self.db.execute("UPDATE lich_su_giao_nhan SET trang_thai='DA_KHU_NHIEM' WHERE id=%s", (pid,))
                else:
                    self.db.execute("UPDATE lich_su_giao_nhan SET so_luong=so_luong-%s WHERE id=%s", (sl_chon, pid))
                    self.db.execute("""
                        INSERT INTO lich_su_giao_nhan (ma_do, so_luong, khoa_giao, phuong_phap, thoi_gian, nguoi_giao, trang_thai)
                        VALUES (%s, %s, %s, %s, NOW(), %s, 'DA_KHU_NHIEM')
                    """, (row['ma_do'], sl_chon, row['khoa_giao'], phuong_phap, nguoi_thuc_hien))
                    
            QMessageBox.information(self.view, "Thành công", "Đã ghi nhận Khử Nhiễm (Thủ công)!")
            self.load_sessions()
            
        except Exception as e:
            QMessageBox.critical(self.view, "Lỗi", f"Lỗi khi lưu dữ liệu: {e}")'''

# Replace process_washing
start_pw = c.find('    def process_washing(self, status):')
end_pw = c.find('    def open_washing_machine_dialog(self):')
c = c[:start_pw] + new_process_washing + '\n\n' + c[end_pw:]

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\controllers\decontamination_controller.py', 'w', encoding='utf-8') as f:
    f.write(c)
