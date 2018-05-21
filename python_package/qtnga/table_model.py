from PyQt5.QtCore import QAbstractTableModel
from PyQt5.QtCore import Qt


class PandasModel(QAbstractTableModel):
    def __init__(self, data, parent=None):
        super(PandasModel, self).__init__(parent)
        self._data = data

    def rowCount(self, parent=None, **kwargs):
        return self._data.shape[0]

    def columnCount(self, parent=None, **kwargs):
        return self._data.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole:
                return str(self._data.iloc[index.row(), index.column()])
        return None

    def headerData(self, col, orientation, role=None):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._data.columns[col]
        return None
