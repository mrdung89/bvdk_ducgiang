import sys
from PySide6.QtWidgets import QApplication

from views.login import LoginWindow
from controllers.login_controller import LoginController
from views.main_window import MainWindow
from controllers.main_window_controller import MainWindowController

class MainController:
    def __init__(self):
        self.login_view = LoginWindow()
        self.login_controller = LoginController(self.login_view)
        self.main_window = None
        self.main_window_controller = None
        
        self.login_view.login_successful.connect(self.on_login_success)
        
    def start(self):
        self.login_view.show()
        
    def on_login_success(self, user_data):
        self.login_view.hide()
        
        self.main_window = MainWindow()
        self.main_window_controller = MainWindowController(self.main_window, user_data)
        
        self.main_window.logout_requested.connect(self.on_logout)
        self.main_window.showMaximized()
        
    def on_logout(self):
        if self.main_window:
            self.main_window.close()
            self.main_window = None
            self.main_window_controller = None
        self.login_view.show()
