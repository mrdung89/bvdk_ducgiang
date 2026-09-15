import sys
import os
from PySide6.QtWidgets import QApplication
from controllers.main_controller import MainController

def main():
    app = QApplication(sys.argv)
    
    font = app.font()
    font.setPointSize(14)
    app.setFont(font)
    
    qss_path = os.path.join(os.path.dirname(__file__), "style.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    else:
        app.setStyle("Fusion")
    
    controller = MainController()
    controller.start()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
