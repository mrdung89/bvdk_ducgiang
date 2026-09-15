import unicodedata
from PySide6.QtCore import QSortFilterProxyModel, Qt

def remove_vietnamese_accents(s):
    if not s:
        return ""
    s = str(s)
    # Convert 'đ' and 'Đ'
    s = s.replace('đ', 'd').replace('Đ', 'D')
    # Remove accents using NFKD
    s = unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('utf-8')
    return s.lower()

class VietnameseSortFilterProxyModel(QSortFilterProxyModel):
    def filterAcceptsRow(self, source_row, source_parent):
        model = self.sourceModel()
        index = model.index(source_row, self.filterKeyColumn(), source_parent)
        data = model.data(index, Qt.DisplayRole)
        
        if not data:
            return False
            
        filter_str = self.filterRegularExpression().pattern()
        if not filter_str:
            return True
            
        # Remove accents and lowercase both strings
        norm_data = remove_vietnamese_accents(data)
        norm_filter = remove_vietnamese_accents(filter_str)
        
        return norm_filter in norm_data
