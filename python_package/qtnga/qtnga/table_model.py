from PyQt5.QtCore import QAbstractTableModel
from PyQt5.QtCore import Qt


class QueueModel(QAbstractTableModel):
    def __init__(self, queue, columns, dtype, parent=None):
        """Queue Model.

        Parameters
        --------
        queue: queue.Queue
        columns: list
        dtype: dict
        """
        super(QueueModel, self).__init__(parent)
        self._data = []
        for record in queue.queue:
            row = []
            for element, column_name in zip(record, columns):
                if element is not None:
                    row.append(dtype[column_name](element))
                else:
                    row.append(element)
            self._data.append(row)
        self._columns = columns

    def rowCount(self, parent=None, **kwargs):
        return len(self._data)

    def columnCount(self, parent=None, **kwargs):
        return len(self._columns)

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole:
                return str(self._data[index.row()][index.column()])
        return None

    def headerData(self, col, orientation, role=None):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._columns[col]
        return None

    def sort(self, p_int, order=None):
        self.layoutAboutToBeChanged.emit()
        self._data = self._data.sort_values(
            self._data.columns[p_int],
            ascending=(order == Qt.AscendingOrder)
        )
        self.layoutChanged.emit()