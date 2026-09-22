from PySide6.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, 
                               QTableWidgetItem, QHeaderView, QPushButton)
from PySide6.QtCore import Qt

class DrilldownDialog(QDialog):
    def __init__(self, title, items, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(800, 500)
        
        layout = QVBoxLayout(self)
        
        self.table = QTableWidget()
        layout.addWidget(self.table)
        
        btn_close = QPushButton("ĐÓNG")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignRight)
        
        self.populate(items)
        
    def populate(self, items):
        if not items:
            return
            
        # Get columns from the first item
        cols = list(items[0].keys())
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels([str(c).upper() for c in cols])
        self.table.setRowCount(len(items))
        
        for row, item in enumerate(items):
            for col, key in enumerate(cols):
                val = item.get(key, "")
                self.table.setItem(row, col, QTableWidgetItem(str(val)))
                
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
