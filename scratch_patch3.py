import sys, re

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\controllers\decontamination_controller.py', 'r', encoding='utf-8') as f:
    c = f.read()

new_start_washing = '''    def start_washing_machine(self, mac_id, cycle_id):
        selected_items = getattr(self, 'temp_selected_items', [])
        if not selected_items: return
        
        nguoi_thuc_hien = self.view.cb_employee.currentText()
        phuong_phap = "Rửa Máy"
        
        try:
            # Get cycle info
            cycle = self.db.fetch_one("SELECT thoi_gian_phut FROM danh_muc_chu_trinh WHERE id=%s", (cycle_id,))
            mins = int(cycle['thoi_gian_phut']) if cycle else 30
            
            from datetime import datetime, timedelta
            end_time = datetime.now() + timedelta(minutes=mins)
            
            loaded_ids = []
            
            for p_data in selected_items:
                pid = p_data['id']
                sl_chon = p_data['sl']
                
                row = self.db.fetch_one("SELECT so_luong, ma_do, khoa_giao FROM lich_su_giao_nhan WHERE id=%s", (pid,))
                if not row: continue
                sl_goc = int(row['so_luong'])
                
                if sl_chon >= sl_goc:
                    self.db.execute("UPDATE lich_su_giao_nhan SET trang_thai='DANG_RUA_MAY' WHERE id=%s", (pid,))
                    loaded_ids.append({'id': pid, 'ma_do': row['ma_do'], 'sl': sl_chon})
                else:
                    self.db.execute("UPDATE lich_su_giao_nhan SET so_luong=so_luong-%s WHERE id=%s", (sl_chon, pid))
                    new_id = self.db.execute("""
                        INSERT INTO lich_su_giao_nhan (ma_do, so_luong, khoa_giao, phuong_phap, thoi_gian, nguoi_giao, trang_thai)
                        VALUES (%s, %s, %s, %s, NOW(), %s, 'DANG_RUA_MAY')
                    """, (row['ma_do'], sl_chon, row['khoa_giao'], phuong_phap, nguoi_thuc_hien))
                    loaded_ids.append({'id': new_id, 'ma_do': row['ma_do'], 'sl': sl_chon})
            
            import json
            items_json = json.dumps(loaded_ids)
            
            self.db.execute("""
                UPDATE machines 
                SET status='RUNNING', current_cycle_id=%s, employee_name=%s, end_time=%s, loaded_items_json=%s 
                WHERE id=%s
            """, (cycle_id, nguoi_thuc_hien, end_time, items_json, mac_id))
            
            # Ghi lịch sử biến động
            self.db.execute("""
                INSERT INTO lich_su_bien_dong_may (machine_id, status_from, status_to, note) 
                VALUES (%s, 'READY', 'RUNNING', %s)
            """, (mac_id, f"Bắt đầu chu trình {cycle_id}"))
            
            QMessageBox.information(self.view, "Thành công", f"Máy {mac_id} bắt đầu chạy!")
            self.load_sessions()
            
        except Exception as e:
            QMessageBox.critical(self.view, "Lỗi", f"Lỗi khi lưu dữ liệu: {e}")'''

start_sw = c.find('    def start_washing_machine(self, mac_id, cycle_id):')
end_sw = c.find('    def complete_washing_machine(self, mac_id):')
c = c[:start_sw] + new_start_washing + '\n\n' + c[end_sw:]

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\controllers\decontamination_controller.py', 'w', encoding='utf-8') as f:
    f.write(c)
