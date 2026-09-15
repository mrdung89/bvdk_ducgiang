import sys

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\controllers\dashboard_controller.py', 'r', encoding='utf-8') as f:
    c = f.read()

import re
new_drilldown_chay = '''    def show_drilldown_chay(self):
        date_str = self.view.date_edit.date().toString("yyyy-MM-dd")
        items = self.db.get_kpi_sterilized_drilldown(date_str)
        if not items:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self.view, "Thông báo", "Không có dữ liệu mẻ chạy.")
            return
            
        dlg = TraceabilityDialog(f"Thiết bị đã xử lý ({date_str})", items, self.view)
        dlg.exec()'''

c = re.sub(r'    def show_drilldown_chay\(self\):.*?dlg\.exec\(\)', new_drilldown_chay, c, flags=re.DOTALL)

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\controllers\dashboard_controller.py', 'w', encoding='utf-8') as f:
    f.write(c)
