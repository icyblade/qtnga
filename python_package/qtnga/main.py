import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

from qtnga import QtNGA


def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app = QApplication(sys.argv)
    window = QtNGA()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
