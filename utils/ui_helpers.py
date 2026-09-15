from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton
from PySide6.QtCore import Qt, QTimer, QSortFilterProxyModel
from PySide6.QtGui import QStandardItemModel, QStandardItem
from models.db_manager import DBManager
from utils.vietnamese_filter import VietnameseSortFilterProxyModel

class DebounceAutocompleteDialog(QDialog):
    def __init__(self, parent, title, label_text, items):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(400, 120)
        self.selected_item = ""
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(label_text))
        
        self.combo = QComboBox()
        self.combo.setEditable(True)
        self.combo.setInsertPolicy(QComboBox.NoInsert)
        
        # Setup Model
        self.model = QStandardItemModel()
        for it in items:
            self.model.appendRow(QStandardItem(it))
            
        # Setup Proxy for filtering (MatchContains + No Accents)
        self.proxy = VietnameseSortFilterProxyModel(self)
        self.proxy.setSourceModel(self.model)
        self.proxy.setFilterKeyColumn(0)
        
        # Use proxy model in combobox
        self.combo.setModel(self.proxy)
        
        # Disable default completer, we will filter the proxy model
        self.combo.setCompleter(None)
        
        # Debounce timer
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(500) # 0.5s debounce
        self.timer.timeout.connect(self.apply_filter)
        
        self.combo.lineEdit().textEdited.connect(self.on_text_edited)
        
        layout.addWidget(self.combo)
        
        hl = QHBoxLayout()
        hl.addStretch()
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.accept_selection)
        btn_cancel = QPushButton("Hủy")
        btn_cancel.clicked.connect(self.reject)
        hl.addWidget(btn_ok)
        hl.addWidget(btn_cancel)
        layout.addLayout(hl)

    def on_text_edited(self, text):
        self.pending_text = text
        self.timer.start()

    def apply_filter(self):
        text = self.combo.lineEdit().text()
        self.proxy.setFilterRegularExpression(self.pending_text)
        if self.proxy.rowCount() > 0:
            self.combo.showPopup()
        else:
            self.combo.hidePopup()
        self.combo.lineEdit().setText(text)

    def accept_selection(self):
        self.selected_item = self.combo.currentText()
        self.accept()

from PySide6.QtCore import Qt, QTimer, QSortFilterProxyModel, Signal

class DebounceComboBox(QComboBox):
    selectionConfirmed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)
        
        self._model = QStandardItemModel(self)
        self._proxy = VietnameseSortFilterProxyModel(self)
        self._proxy.setSourceModel(self._model)
        self._proxy.setFilterKeyColumn(0)
        
        self.setModel(self._proxy)
        self.setCompleter(None)
        
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(500)
        self.timer.timeout.connect(self.apply_filter)
        
        self.lineEdit().textEdited.connect(self.on_text_edited)
        self.pending_text = ""
        
        self.lineEdit().returnPressed.connect(self.on_return_pressed)
        self.activated.connect(self.on_activated)
        
    def addItems(self, texts):
        for t in texts:
            self._model.appendRow(QStandardItem(t))
            
    def addItem(self, text):
        self._model.appendRow(QStandardItem(text))

    def clear(self):
        self._model.clear()
        
    def on_text_edited(self, text):
        self.pending_text = text
        self.timer.start()

    def apply_filter(self):
        text = self.pending_text
        cursor = self.lineEdit().cursorPosition()
        
        self.blockSignals(True)
        self._proxy.setFilterRegularExpression(text)
        self.blockSignals(False)
        
        self.lineEdit().setText(text)
        self.lineEdit().setCursorPosition(cursor)
        
        if self._proxy.rowCount() > 0 and text:
            self.showPopup()
        else:
            self.hidePopup()
        
    def on_return_pressed(self):
        if self._proxy.rowCount() > 0:
            idx = self._proxy.index(0, 0)
            text = self._proxy.data(idx, Qt.DisplayRole)
            self.setCurrentText(text)
            self.hidePopup()
            self.clearFocus()
            self.selectionConfirmed.emit(self.currentText())

    def on_activated(self, index):
        self.selectionConfirmed.emit(self.currentText())

def get_autocomplete_input(parent, title, label, query_type):
    db = DBManager()
    items = []
    
    try:
        if query_type == "bo_dung_cu":
            rows = db.fetch_all("SELECT ma_bo, ten_bo FROM danh_muc_bo_dung_cu")
            items = [f"{r['ma_bo']} - {r.get('ten_bo', '')}" for r in rows]
        elif query_type == "do_vai":
            rows = db.fetch_all("SELECT ma_do_vai, ten_do_vai FROM danh_muc_do_vai")
            items = [f"{r['ma_do_vai']} - {r.get('ten_do_vai', '')}" for r in rows]
        elif query_type == "khoa":
            rows = db.fetch_all("SELECT ten_khoa FROM danh_muc_khoa")
            items = [r['ten_khoa'] for r in rows]
    except:
        pass
        
    dlg = DebounceAutocompleteDialog(parent, title, label, items)
    if dlg.exec():
        val = dlg.selected_item
        if val:
            code = val.split(" - ")[0].strip()
            return code, True
    return "", False
