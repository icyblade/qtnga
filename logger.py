import logging

from PyQt5.QtGui import QTextCursor


def build_logger(name, level=logging.WARNING):
    logger = logging.getLogger(name)
    logger.handlers = []
    logger.setLevel(level)

    return logger


class QTextEditFormatter(logging.Formatter):
    def format(self, record):
        if record.levelno >= 40:
            # error & critical
            color = '#ff0000'
        elif record.levelno >= 30:
            # warning
            color = '#afaf00'
        else:
            # info & debug
            color = '#000000'
        message = f'<span style="color:{color};">{record.msg}</span><br>'

        return message


class QTextEditLogger(logging.Handler):
    def __init__(self, widget):
        super(QTextEditLogger, self).__init__()
        self.widget = widget
        self.setFormatter(QTextEditFormatter())

    def emit(self, record):
        msg = self.format(record)
        self.widget.textCursor().insertHtml(msg)
        self.widget.moveCursor(QTextCursor.End)

    def write(self, m):
        pass
