from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLineEdit
from PySide6.QtCore import Qt

class QuantityWidget(QWidget):
    def __init__(self, parent=None, initial_value=1):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(5)
        
        self.btn_minus = QPushButton("-")
        self.btn_minus.setFixedSize(35, 35)
        self.btn_minus.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold; border-radius: 4px;")
        self.btn_minus.clicked.connect(self.decrease)
        
        self.lbl_val = QLineEdit(str(initial_value))
        self.lbl_val.setAlignment(Qt.AlignCenter)
        self.lbl_val.setFixedWidth(50)
        self.lbl_val.setStyleSheet("border: 1px solid #bdc3c7; border-radius: 4px; padding: 2px;")
        
        self.btn_plus = QPushButton("+")
        self.btn_plus.setFixedSize(35, 35)
        self.btn_plus.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold; border-radius: 4px;")
        self.btn_plus.clicked.connect(self.increase)
        
        layout.addWidget(self.btn_minus)
        layout.addWidget(self.lbl_val)
        layout.addWidget(self.btn_plus)

    def value(self):
        try:
            return int(self.lbl_val.text())
        except ValueError:
            return 1
            
    def set_value(self, val):
        self.lbl_val.setText(str(val))
            
    def decrease(self):
        v = self.value()
        if v > 1:
            self.lbl_val.setText(str(v - 1))
            
    def increase(self):
        v = self.value()
        self.lbl_val.setText(str(v + 1))
