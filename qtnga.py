import logging
import sys
import traceback

from PyQt5 import uic
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QMainWindow, qApp, QRadioButton, QDesktopWidget, QApplication
from pynga import NGA

from logger import build_logger, QTextEditLogger

__version__ = '1.0.0'


class ExceptHandler(object):
    def __init__(self, logger):
        self.logger = logger

    def __call__(self, func):
        def generate_errcode(*args, **kwargs):
            # noinspection PyBroadException
            try:
                return func(*args[:-1], **kwargs)
            except Exception:
                self.logger.error('Error found, please send logs to @icyblade.')
                self.logger.error(traceback.format_exc())

        return generate_errcode


class QtNGA(QMainWindow):
    logger = build_logger('QtNGA', logging.DEBUG)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.uid = None
        self.cid = None
        self.tid = None
        self.nga = None
        self._is_login = False
        self.bonus_data = None

        self.ui = uic.loadUi('qtnga.ui', self)
        self.init_ui()
        self.init_logger()

    def init_logger(self):
        self.logger.addHandler(QTextEditLogger(self.ui.logTextEdit))

    def init_ui(self):
        self.setWindowTitle(f'QtNGA {__version__}')
        self.setFixedSize(800, 600)
        self._set_screen_center()

        # menu bar
        self.ui.actionExit.triggered.connect(qApp.quit)

        # settings
        int_validator = QIntValidator()
        self.ui.uidEdit.setValidator(int_validator)
        self.ui.tidEdit.setValidator(int_validator)
        self.ui.maxFloorEdit.setValidator(int_validator)

        self.uid = self.ui.uidEdit.text()
        self.ui.uidEdit.textChanged[str].connect(self._set_uid)
        self.cid = self.ui.cidEdit.text()
        self.ui.cidEdit.textChanged[str].connect(self._set_cid)
        self.tid = self.ui.tidEdit.text()
        self.ui.tidEdit.textChanged[str].connect(self._set_tid)

        # buttons
        self.ui.loginButton.clicked.connect(self._login)
        self.ui.startButton.clicked.connect(self._start)
        self.ui.bonusButton.clicked.connect(self._bonus)

    @ExceptHandler(logger)
    def _login(self):
        self.logger.debug(f'Login as UID: {self.uid}')
        self.nga = NGA(authentication={'uid': self.uid, 'cid': self.cid})
        if self.nga.current_user.username:
            self.is_login = True
            self.logger.info(f'Hello world: {self.nga.current_user.username}')
        else:
            self.is_login = False
            self.logger.info(f'Login failed!')

    @property
    def is_login(self):
        return self._is_login

    @is_login.setter
    def is_login(self, value):
        assert isinstance(value, bool)
        self.ui.startButton.setEnabled(value)
        self.ui.stopButton.setEnabled(value)
        self._is_login = value

    @ExceptHandler(logger)
    def _start(self):
        # TODO: QThread
        self.ui.bonusButton.setEnabled(False)

        thread = self.nga.Thread(self.tid)
        total_posts = len(thread.posts.items()) - 1  # except main floor
        self.logger.info(f'Thread found: {thread.subject}')

        self.ui.progressBar.setMaximum(total_posts)

        self.logger.info(f'Starting crawler...')

        seen_uids = set([])
        data = []
        for lou, post in thread.posts.items():
            mask = True

            if lou == 0:
                continue  # except main floor
            elif not post.content:
                continue  # except comment

            if post.user.uid is None:  # except anonymous user
                mask &= False
            elif post.user.uid in seen_uids and not self.ui.duplicateCheckBox.isChecked():
                mask &= False
            else:
                seen_uids.add(post.user.uid)

            if self.ui.imgCheckBox.isChecked() and post.content.find('[img]') == -1:
                mask &= False

            keyword = self.ui.keywordEdit.text()
            if keyword and post.content.find(keyword) == -1:
                mask &= False

            if self.ui.maxFloorEdit.text() and lou > int(self.ui.maxFloorEdit.text()):
                mask &= False

            if mask:
                data.append((lou, post))
            self.logger.debug(f'[{"!" if mask else "X"}] {lou} {post.user.username}: {post.content[:30]}...')
            self.ui.progressBar.setValue(lou)

        total_todo = len(data)

        self.logger.info(f'DONE, {total_todo} posts to be bonus-ed')

        self.bonus_data = data
        self.ui.bonusButton.setEnabled(True)

    @ExceptHandler(logger)
    def _stop(self):
        pass

    @ExceptHandler(logger)
    def _bonus(self):
        reputation, add_rvrc, add_gold = self._configure_bonus()
        options = ['给作者发送PM']
        if add_rvrc:
            options.append('增加威望')
        if add_gold:
            options.append('增加/扣除金钱')

        self.logger.info('Starting mass bonus...')

        self.ui.progressBar.setMaximum(len(self.bonus_data))
        for index, (lou, post) in enumerate(self.bonus_data):
            post.add_point(reputation, info=f'QtNGA/{__version__}', options=options)
            self.ui.progressBar.setValue(index + 1)

        self.logger.info('DONE')

    def _configure_bonus(self):
        radios = [15, 30, 45, 60, 75, 105, 150]
        reputation = None

        for i in radios:
            if self.ui.findChild(QRadioButton, f'rep{i}RadioButton').isChecked():
                reputation = i
                break

        if self.ui.rvrcCheckBox.isChecked():
            self.logger.error(f'二哥说了不要加威望')
        add_rvrc = False
        add_gold = self.ui.goldCheckBox.isChecked()

        return reputation, add_rvrc, add_gold

    def _set_uid(self, text):
        self.uid = int(text)

    def _set_cid(self, text):
        self.cid = text

    def _set_tid(self, text):
        self.tid = int(text)

    def _set_screen_center(self):
        frame_geo = self.frameGeometry()
        center_point = QDesktopWidget().screenGeometry().center()
        frame_geo.moveCenter(center_point)
        self.move(frame_geo.topLeft())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = QtNGA()
    window.show()
    sys.exit(app.exec_())
