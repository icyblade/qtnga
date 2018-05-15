import sys

from PyQt5.QtWidgets import QApplication

from qtnga import QtNGA

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = QtNGA()
    window.show()
    sys.exit(app.exec_())
