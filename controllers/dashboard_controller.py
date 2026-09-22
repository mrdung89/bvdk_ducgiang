import threading
from PySide6.QtCore import QObject, Signal, QDate, QTimer
from PySide6.QtWidgets import QMessageBox
import pandas as pd
import seaborn as sns
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import warnings
warnings.filterwarnings("ignore")

from models.db_manager import DBManager
from views.dashboard_components import DashboardMachineCard
from views.traceability_dialog import TraceabilityDialog
from views.drilldown_dialog import DrilldownDialog

class DashboardController(QObject):
    # Signals to update UI from background threads
    update_kpi_signal = Signal(dict)
    update_machines_signal = Signal(list)
    update_chart_signal = Signal(object) # figure

    def __init__(self, view):
        super().__init__()
        self.view = view
        self.db = DBManager()
        
        self.view.date_edit.dateChanged.connect(self.load_data)
        self.view.btn_search.clicked.connect(self.search_traceability)
        
        self.view.card_nhan.clicked.connect(self.show_drilldown_nhan)
        self.view.card_cho.clicked.connect(lambda: QMessageBox.information(self.view, "Thông báo", "Đang phát triển"))
        self.view.card_chay.clicked.connect(self.show_drilldown_chay)
        self.view.card_kho.clicked.connect(self.show_drilldown_kho)
        
        self.view.signal_show_alerts.connect(self.show_alerts)
        
        self.update_kpi_signal.connect(self.on_kpi_updated)
        self.update_machines_signal.connect(self.on_machines_updated)
        self.update_chart_signal.connect(self.on_chart_updated)
        
        # Load initial data
        self.load_data()
        
        # Set a timer to reload data every 5 minutes
        self.reload_timer = QTimer(self)
        self.reload_timer.timeout.connect(self.load_data)
        self.reload_timer.start(5000)

    def load_data(self):
        date_str = self.view.date_edit.date().toString("yyyy-MM-dd")
        tu_ngay = self.view.date_edit.date().addDays(-6).toString("yyyy-MM-dd 00:00:00")
        den_ngay = self.view.date_edit.date().toString("yyyy-MM-dd 23:59:59")
        
        # Run in thread
        threading.Thread(target=self._fetch_data_worker, args=(date_str, tu_ngay, den_ngay), daemon=True).start()

    def _fetch_data_worker(self, date_str, tu_ngay, den_ngay):
        # Local db connection for thread
        local_db = DBManager()
        
        kpi = local_db.get_kpi_summary_v2(date_str)
        if kpi:
            self.update_kpi_signal.emit(kpi)
            
        machines = local_db.get_realtime_machines()
        if machines:
            self.update_machines_signal.emit(machines)
            
        chart_data = local_db.get_chart_data_7days(tu_ngay, den_ngay)
        if chart_data is not None:
            fig = self._create_chart(chart_data)
            self.update_chart_signal.emit(fig)

    def _create_chart(self, chart_data):
        df = pd.DataFrame(chart_data)
        
        fig, ax = plt.subplots(figsize=(8, 4))
        if df.empty:
            ax.text(0.5, 0.5, "Không có dữ liệu", ha='center', va='center')
        else:
            sns.barplot(data=df, x='ngay', y='so_me', hue='ten_may', ax=ax, palette="viridis")
            ax.set_xlabel("")
            ax.set_ylabel("Số Chu trình")
            ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.15), ncol=5, frameon=False, fontsize=8)
        
        fig.tight_layout()
        return fig

    def on_kpi_updated(self, kpi):
        self.view.card_nhan.set_value(kpi.get('nhan', 0))
        self.view.card_cho.set_value(kpi.get('cho_xu_ly', 0))
        self.view.card_chay.set_value(kpi.get('da_xu_ly', 0))
        self.view.card_kho.set_value(kpi.get('kho_sach', 0))

    def on_machines_updated(self, machines):
        # Clear old machines
        while self.view.machines_layout.count():
            item = self.view.machines_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
                
        row = 0
        col = 0
        for m in machines:
            card = DashboardMachineCard(m)
            card.clicked.connect(lambda name=m.get('ten_may'): QMessageBox.information(self.view, "Thông báo", f"Lịch sử máy {name}"))
            self.view.machines_layout.addWidget(card, row, col)
            col += 1
            if col > 3:
                col = 0
                row += 1

    def on_chart_updated(self, fig):
        # Clear layout
        while self.view.chart_layout.count():
            item = self.view.chart_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
                
        canvas = FigureCanvas(fig)
        self.view.chart_layout.addWidget(canvas)

    # --- Drill downs ---
    def show_alerts(self):
        expiries = self.db.get_expiry_alerts()
        min_stocks = self.db.get_min_stock_alerts()
        
        from views.alerts_dialog import AlertsDialog
        dlg = AlertsDialog(expiries, min_stocks, self.view)
        dlg.exec()

    def show_drilldown_nhan(self):
        date_str = self.view.date_edit.date().toString("yyyy-MM-dd")
        items = self.db.get_kpi_received_drilldown(date_str)
        if items:
            dlg = DrilldownDialog(f"Tiếp nhận hôm nay ({date_str})", items, self.view)
            dlg.exec()
        else:
            QMessageBox.information(self.view, "Thông báo", "Không có dữ liệu tiếp nhận.")

    def show_drilldown_chay(self):
        date_str = self.view.date_edit.date().toString("yyyy-MM-dd")
        items = self.db.get_kpi_sterilized_drilldown(date_str)
        if not items:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self.view, "Thông báo", "Không có dữ liệu mẻ chạy.")
            return
            
        dlg = DrilldownDialog(f"Thiết bị đã xử lý ({date_str})", items, self.view)
        dlg.exec()

    def show_drilldown_kho(self):
        items = self.db.get_kpi_clean_inventory_drilldown()
        if items:
            dlg = DrilldownDialog("Kho sạch tồn", items, self.view)
            dlg.exec()
        else:
            QMessageBox.information(self.view, "Thông báo", "Kho sạch trống.")
            
    def search_traceability(self):
        from views.traceability_dialog import TraceabilityDialog
        dlg = TraceabilityDialog(db=self.db, parent=self.view)
        keyword = self.view.txt_search.text().strip()
        if keyword:
            dlg.txt_search.setText(keyword)
            dlg._do_trace()
        dlg.exec()
