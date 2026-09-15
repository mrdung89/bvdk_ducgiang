import sys

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\controllers\main_window_controller.py', 'r', encoding='utf-8') as f:
    c = f.read()

new_connect = '''    def connect_signals(self):
        v = self.view
        
        v.content_area.currentChanged.connect(self.on_tab_changed)'''

c = c.replace('    def connect_signals(self):\n        v = self.view', new_connect)

new_method = '''    def on_tab_changed(self, index):
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

    def set_default_page'''

c = c.replace('    def set_default_page', new_method)

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\controllers\main_window_controller.py', 'w', encoding='utf-8') as f:
    f.write(c)
