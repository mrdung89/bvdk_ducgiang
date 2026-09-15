from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                               QTreeWidget, QTreeWidgetItem, QHeaderView, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
from models.db_manager import DBManager
from utils.printer import print_assembly_label
from collections import OrderedDict

class AssemblyPage(QWidget):
    def __init__(self):
        super().__init__()
        self.db = DBManager()
        self.setup_ui()
        self.load_items()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        header = QLabel("ĐÓNG GÓI & IN TEM")
        header.setFont(QFont("Arial", 23, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # TreeView
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Phiên Khử Nhiễm / Mã đồ", "Tên đồ", "Số lượng"])
        self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tree.itemChanged.connect(self.on_tree_item_changed)
        layout.addWidget(self.tree)
        
        btn_layout = QHBoxLayout()
        
        self.btn_refresh = QPushButton("Làm mới")
        self.btn_refresh.clicked.connect(self.load_items)
        btn_layout.addWidget(self.btn_refresh)
        
        btn_layout.addStretch()
        
        btn_pack = QPushButton("📦 Đóng Gói & In Tem")
        btn_pack.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold; font-size: 16px; padding: 10px 20px; border-radius: 5px;")
        btn_pack.clicked.connect(self.do_pack)
        btn_layout.addWidget(btn_pack)
        
        layout.addLayout(btn_layout)

    def load_items(self):
        self.tree.blockSignals(True)
        self.tree.clear()
        
        try:
            # Lấy các đồ đã khử nhiễm, sắp xếp mới nhất lên trên
            rows = self.db.fetch_all("""
                SELECT id, khoa_giao, ma_do, so_luong, DATE_FORMAT(thoi_gian, '%d/%m %H:%i') as tm 
                FROM lich_su_giao_nhan 
                WHERE trang_thai = 'DA_KHU_NHIEM'
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
                
            groups = OrderedDict()
            for r in rows:
                key = f"{r['khoa_giao']} - {r['tm']}"
                if key not in groups:
                    groups[key] = []
                groups[key].append(r)
                
            for key, items in groups.items():
                parent = QTreeWidgetItem([key, "", ""])
                parent.setCheckState(0, Qt.Unchecked)
                parent.setBackground(0, QColor("#ecf0f1"))
                parent.setBackground(1, QColor("#ecf0f1"))
                parent.setBackground(2, QColor("#ecf0f1"))
                font = QFont()
                font.setBold(True)
                parent.setFont(0, font)
                
                self.tree.addTopLevelItem(parent)
                
                for it in items:
                    child = QTreeWidgetItem([it['ma_do'], it['ten_do'], str(it['so_luong'])])
                    child.setCheckState(0, Qt.Unchecked)
                    child.setData(0, Qt.UserRole, it['id']) # Store ID
                    parent.addChild(child)
                    
                parent.setExpanded(True)
                
        except Exception as e:
            print("Error loading assembly items:", e)
            
        self.tree.blockSignals(False)

    def on_tree_item_changed(self, item, column):
        if column != 0: return
        self.tree.blockSignals(True)
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
        self.tree.blockSignals(False)

    def do_pack(self):
        selected_items = []
        for i in range(self.tree.topLevelItemCount()):
            parent = self.tree.topLevelItem(i)
            for j in range(parent.childCount()):
                child = parent.child(j)
                if child.checkState(0) == Qt.Checked:
                    pid = child.data(0, Qt.UserRole)
                    selected_items.append({'id': pid, 'ma_do': child.text(0), 'ten_do': child.text(1)})
                    
        if not selected_items:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng tích chọn ít nhất 1 món đồ để đóng gói & in tem!")
            return
            
        # Fetch DB attributes for printing
        for it in selected_items:
            ma = it['ma_do']
            is_digit = str(ma).isdigit()
            pptk = "STEAM"
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
                        han_tiet_khuan = res2.get('han_tiet_khuan') or 30
                    else:
                        q3 = "SELECT phuong_phap_tiet_khuan, han_tiet_khuan FROM danh_muc_dung_cu WHERE ma_dc=%s" + (" OR id=%s" if is_digit else "")
                        p3 = (ma, ma) if is_digit else (ma,)
                        res3 = self.db.fetch_one(q3, p3)
                        if res3:
                            pptk = res3.get('phuong_phap_tiet_khuan') or "STEAM"
                            han_tiet_khuan = res3.get('han_tiet_khuan') or 30
            except: pass
            it['pptk'] = pptk
            it['han_tiet_khuan'] = han_tiet_khuan
            it['nguoi_dong_goi'] = "NV KSNK" # Có thể lấy từ phiên đăng nhập sau
            
        from views.print_dialog import PrintLabelDialog
        dlg = PrintLabelDialog(self, selected_items)
        if dlg.exec():
            # In thành công -> Đổi trạng thái
            success_count = 0
            for it in selected_items:
                try:
                    self.db.execute("UPDATE lich_su_giao_nhan SET trang_thai='DA_DONG_GOI' WHERE id=%s", (it['id'],))
                    success_count += 1
                except: pass
            QMessageBox.information(self, "Thành công", f"Đã in tem và chuyển trạng thái cho {success_count} đồ!")
            self.load_items()
