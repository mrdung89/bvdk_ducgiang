import sys

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\views\intem_bvdk_ducgiang.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Modify MainApp __init__ to accept is_subscreen
c = c.replace('def __init__(self, root):', 'def __init__(self, root, is_subscreen=False):')
c = c.replace('self.mk_btn(self.fr_side, "🚪  ĐĂNG XUẤT", self.logout, bg="#c0392b")',
              'if is_subscreen: self.mk_btn(self.fr_side, "⬅  QUAY LẠI", self.root.destroy, bg="#c0392b")\n        else: self.mk_btn(self.fr_side, "🚪  ĐĂNG XUẤT", self.logout, bg="#c0392b")')

# Change start_app
new_start = '''def start_app():
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--subscreen':
        global CURRENT_USER, CURRENT_USER_FULLNAME
        CURRENT_USER = 'NV'
        CURRENT_USER_FULLNAME = 'Nhân viên (Từ App Chính)'
        main_root = tk.Tk()
        MainApp(main_root, is_subscreen=True)
        main_root.mainloop()
    else:
        def on_login_success(login_root): login_root.destroy(); main_root = tk.Tk(); MainApp(main_root); main_root.mainloop()
        root = tk.Tk(); LoginWindow(root, lambda: on_login_success(root)); root.mainloop()

if __name__ == "__main__":
    start_app()'''

c = c[:c.find('def start_app():')] + new_start

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\views\intem_bvdk_ducgiang.py', 'w', encoding='utf-8') as f:
    f.write(c)
