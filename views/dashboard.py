from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                               QLabel, QLineEdit, QPushButton, QDateEdit, 
                               QScrollArea, QFrame)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont
import qtawesome as qta
from views.dashboard_components import KPICard, DashboardMachineCard

class FlowLayout(QHBoxLayout):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)

class DashboardPage(QWidget):
    signal_show_alerts = Signal()
    
    def __init__(self, parent=None):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # 1. Header: Date Picker & Search Traceability
        header_layout = QHBoxLayout()
        header_layout.setSpacing(15)
        
        lbl_date = QLabel("Ngày thống kê:")
        lbl_date.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setStyleSheet("font-size: 14px; padding: 5px;")
        
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Nhập Tên bộ hoặc quét mã QR để truy vết...")
        self.txt_search.setStyleSheet("font-size: 14px; padding: 5px;")
        
        self.btn_search = QPushButton("  Truy vết")
        self.btn_search.setIcon(qta.icon('fa5s.search', color='white'))
        self.btn_search.setStyleSheet("background-color: #e67e22; color: white; font-weight: bold; padding: 8px 15px; border-radius: 4px;")
        
        self.btn_alerts = QPushButton("  Cảnh Báo")
        self.btn_alerts.setIcon(qta.icon('fa5s.exclamation-triangle', color='white'))
        self.btn_alerts.setStyleSheet("background-color: #c0392b; color: white; font-weight: bold; padding: 8px 15px; border-radius: 4px;")
        
        header_layout.addWidget(lbl_date)
        header_layout.addWidget(self.date_edit)
        header_layout.addWidget(self.txt_search, stretch=1)
        header_layout.addWidget(self.btn_search)
        header_layout.addWidget(self.btn_alerts)
        
        main_layout.addLayout(header_layout)

        # Scrollable area for everything else
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(20)
        
        # 2. KPI Cards
        lbl_kpi = QLabel("TỔNG QUAN HÔM NAY")
        lbl_kpi.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        scroll_layout.addWidget(lbl_kpi)
        
        self.kpi_layout = QHBoxLayout()
        self.kpi_layout.setSpacing(15)
        
        self.card_nhan = KPICard("Tiếp nhận hôm nay", "TIẾP NHẬN (Khoa)", "#2980b9")
        self.card_cho = KPICard("Chờ xử lý (Bẩn)", "CHỜ XỬ LÝ (Món)", "#c0392b")
        self.card_chay = KPICard("Số mẻ đã chạy", "ĐÃ HẤP (Mẻ)", "#27ae60")
        self.card_kho = KPICard("Kho sạch tồn", "KHO SẠCH (Món)", "#f39c12")
        
        self.kpi_layout.addWidget(self.card_nhan)
        self.kpi_layout.addWidget(self.card_cho)
        self.kpi_layout.addWidget(self.card_chay)
        self.kpi_layout.addWidget(self.card_kho)
        scroll_layout.addLayout(self.kpi_layout)
        
        # 3. Real-time Machines
        lbl_machines = QLabel("TRẠNG THÁI THIẾT BỊ REAL-TIME")
        lbl_machines.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        scroll_layout.addWidget(lbl_machines)
        
        self.machines_container = QWidget()
        self.machines_layout = QGridLayout(self.machines_container)
        self.machines_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        scroll_layout.addWidget(self.machines_container)
        
        # 4. Chart 7 days
        lbl_chart = QLabel("HIỆU SUẤT VẬN HÀNH 7 NGÀY (SỐ MẺ)")
        lbl_chart.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        scroll_layout.addWidget(lbl_chart)
        
        self.chart_container = QFrame()
        self.chart_container.setStyleSheet("background-color: white; border-radius: 10px;")
        self.chart_container.setMinimumHeight(400)
        self.chart_layout = QVBoxLayout(self.chart_container)
        self.lbl_chart_loading = QLabel("Đang tải biểu đồ...")
        self.lbl_chart_loading.setAlignment(Qt.AlignCenter)
        self.chart_layout.addWidget(self.lbl_chart_loading)
        
        scroll_layout.addWidget(self.chart_container)
        
        scroll_layout.addStretch()
        
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)
