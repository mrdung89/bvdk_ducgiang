from PySide6.QtCore import QObject
from PySide6.QtWidgets import QMessageBox

from views.dashboard import DashboardPage
from controllers.dashboard_controller import DashboardController
from views.decontamination import DecontaminationPage
from controllers.decontamination_controller import DecontaminationController
from views.assembly import AssemblyPage
from views.sterilization import SterilizationPage
from views.distribution import ReceivePage, IssuePage
from views.reports import ReportsPage
from views.inventory_extra import InventoryExtraPage
from views.master_data import MasterDataPage
from views.management import ManagementPage
from views.settings import SettingsPage

class MainWindowController(QObject):
    def __init__(self, view, user_data):
        super().__init__()
        self.view = view
        self.user_data = user_data
        self.role = self.user_data.get('role', 'ADMIN')
        
        # Setup UI first
        self.view.setup_ui(self.user_data)
        
        # Initialize sub-controllers and views
        self.init_pages()
        
        # Setup connections
        self.connect_signals()
        
        # Set default page
        self.set_default_page()

    def init_pages(self):
        # Giao Nhan (Using old ReceivePage)
        self.page_receive = ReceivePage(self.user_data)
        self.view.add_page(self.page_receive)
        self.idx_receive = self.view.content_area.indexOf(self.page_receive)
        
        # Dashboard
        if self.role != "KHOA_LAM_SANG":
            self.page_dashboard = DashboardPage()
            self.controller_dashboard = DashboardController(self.page_dashboard)
            self.view.add_page(self.page_dashboard)
            self.idx_dashboard = self.view.content_area.indexOf(self.page_dashboard)
        else:
            self.page_dashboard = None
            self.idx_dashboard = self.idx_receive # Fallback to ReceivePage!
        
        # Processing Pages (if authorized)
        if self.role in ["ADMIN", "STAFF", "NV_KSNK", "LANH_DAO"]:
            self.page_decon = DecontaminationPage()
            self.controller_decon = DecontaminationController(self.page_decon, self.user_data)
            self.page_assembly = AssemblyPage(self.user_data)
            self.page_sterilize = SterilizationPage()
            from controllers.sterilization_controller import SterilizationController
            self.controller_sterilize = SterilizationController(self.page_sterilize, self.user_data)
            self.view.add_page(self.page_decon)
            self.view.add_page(self.page_assembly)
            self.view.add_page(self.page_sterilize)
            
            self.idx_decon = self.view.content_area.indexOf(self.page_decon)
            self.idx_assembly = self.view.content_area.indexOf(self.page_assembly)
            self.idx_sterilize = self.view.content_area.indexOf(self.page_sterilize)
            
        # Cap Phat
        self.page_issue = IssuePage(self.user_data)
        self.view.add_page(self.page_issue)
        self.idx_issue = self.view.content_area.indexOf(self.page_issue)
        
        # Reports / Inventory / Master Data
        if self.role != "KHOA_LAM_SANG":
            self.page_reports = ReportsPage()
            self.page_inventory = InventoryExtraPage()
            self.view.add_page(self.page_reports)
            self.view.add_page(self.page_inventory)
            
            self.idx_reports = self.view.content_area.indexOf(self.page_reports)
            self.idx_inventory = self.view.content_area.indexOf(self.page_inventory)
            
            if self.role == "ADMIN":
                self.page_masterdata = MasterDataPage()
                self.view.add_page(self.page_masterdata)
                self.idx_masterdata = self.view.content_area.indexOf(self.page_masterdata)

    
        self.page_management = ManagementPage()
        self.view.add_page(self.page_management)
        self.idx_management = self.view.content_area.indexOf(self.page_management)
        if hasattr(self.page_management, "set_user_data"):
            self.page_management.set_user_data(self.user_data)

        # Settings
        self.page_settings = SettingsPage(self.user_data)
        self.view.add_page(self.page_settings)
        self.idx_settings = self.view.content_area.indexOf(self.page_settings)

    def connect_signals(self):
        v = self.view
        
        v.content_area.currentChanged.connect(self.on_tab_changed)
        
        if hasattr(v, 'btn_dashboard') and v.btn_dashboard:
            v.btn_dashboard.clicked.connect(lambda: v.switch_page(self.idx_dashboard, v.btn_dashboard))
            
        if hasattr(v, 'btn_decon') and v.btn_decon:
            v.btn_decon.clicked.connect(lambda: v.switch_page(self.idx_decon, v.btn_decon))
        if hasattr(v, 'btn_assembly') and v.btn_assembly:
            v.btn_assembly.clicked.connect(lambda: v.switch_page(self.idx_assembly, v.btn_assembly))
        if hasattr(v, 'btn_sterilize') and v.btn_sterilize:
            v.btn_sterilize.clicked.connect(lambda: v.switch_page(self.idx_sterilize, v.btn_sterilize))
            
        if hasattr(v, 'btn_receive') and v.btn_receive:
            v.btn_receive.clicked.connect(lambda: v.switch_page(self.idx_receive, v.btn_receive))
            
        if hasattr(v, 'btn_issue') and v.btn_issue:
            v.btn_issue.clicked.connect(lambda: v.switch_page(self.idx_issue, v.btn_issue))
            
        if hasattr(v, 'btn_reports') and v.btn_reports:
            v.btn_reports.clicked.connect(lambda: v.switch_page(self.idx_reports, v.btn_reports))
        if hasattr(v, 'btn_inventory') and v.btn_inventory:
            v.btn_inventory.clicked.connect(lambda: v.switch_page(self.idx_inventory, v.btn_inventory))
        if hasattr(v, 'btn_masterdata') and v.btn_masterdata:
            v.btn_masterdata.clicked.connect(lambda: v.switch_page(self.idx_masterdata, v.btn_masterdata))

    
        if hasattr(v, 'btn_management') and v.btn_management:
            v.btn_management.clicked.connect(lambda: v.switch_page(self.idx_management, v.btn_management))
        if hasattr(v, 'btn_settings') and v.btn_settings:
            v.btn_settings.clicked.connect(lambda: v.switch_page(self.idx_settings, v.btn_settings))

    def on_tab_changed(self, index):
        if index == getattr(self, 'idx_decon', -1) and hasattr(self, 'controller_decon'):
            self.controller_decon.load_sessions()
        elif index == getattr(self, 'idx_receive', -1) and hasattr(self, 'page_receive'):
            if hasattr(self.page_receive, 'load_multi_client'):
                self.page_receive.load_multi_client()
        elif index == getattr(self, 'idx_assembly', -1) and hasattr(self, 'page_assembly'):
            if hasattr(self.page_assembly, 'refresh_session_cb'):
                self.page_assembly.refresh_session_cb()
        elif index == getattr(self, 'idx_issue', -1) and hasattr(self, 'page_issue'):
            if hasattr(self.page_issue, 'load_issue'):
                self.page_issue.load_issue()

    def set_default_page(self):
        v = self.view
        if hasattr(v, 'btn_dashboard') and v.btn_dashboard:
            v.switch_page(self.idx_dashboard, v.btn_dashboard)
        elif hasattr(v, 'btn_receive') and v.btn_receive:
            v.switch_page(self.idx_receive, v.btn_receive)

    def show_placeholder(self, title):
        QMessageBox.information(self.view, title, f'Tính năng {title} đang được phát triển, sẽ ra mắt trong phiên bản sau.')
        # Re-check the current page button
        idx = self.view.content_area.currentIndex()
        if idx == getattr(self, 'idx_dashboard', -1): self.view.btn_dashboard.setChecked(True)
        elif idx == getattr(self, 'idx_receive', -1): self.view.btn_receive.setChecked(True)
        elif idx == getattr(self, 'idx_decon', -1): self.view.btn_decon.setChecked(True)
        elif idx == getattr(self, 'idx_assembly', -1): self.view.btn_assembly.setChecked(True)
        elif idx == getattr(self, 'idx_sterilize', -1): self.view.btn_sterilize.setChecked(True)
        elif idx == getattr(self, 'idx_issue', -1): self.view.btn_issue.setChecked(True)
