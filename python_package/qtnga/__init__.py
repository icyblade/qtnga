import logging
from queue import Queue
from time import time

import pandas as pd
from PyQt5 import uic
from PyQt5.QtCore import QThreadPool
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QMainWindow, qApp, QRadioButton, QDesktopWidget, QHeaderView
from logger import build_logger, QTextEditLogger
from pynga import NGA

from .helper import ExceptHandler
from .logic import _generate_mask
from .table_model import PandasModel
from .worker import Worker

__version__ = '1.0.0'


class QtNGA(QMainWindow):
    logger = build_logger('QtNGA', logging.DEBUG)
    posts_header = ['lou', 'pid', 'username', 'uid', 'content', 'mask']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.uid = None
        self.cid = None
        self.tid = None
        self.nga = None
        self._is_login = False
        self.bonus_data = None
        self.worker = None

        self.ui = uic.loadUi('qtnga.ui', self)
        self.init_ui()
        self.init_logger()

        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(1)

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
        self.ui.stopButton.clicked.connect(self._stop)

        # posts
        self._refresh_posts_from_queue(Queue())

    def _refresh_posts_from_queue(self, queue):
        """Refresh Posts box from Queue.

        This is a thread-safe(I hope) method.
        """
        self.posts = pd.DataFrame(list(queue.queue), columns=self.posts_header)
        model = PandasModel(self.posts)
        self.ui.postsTableView.setModel(model)
        self.ui.postsTableView.model().layoutChanged.emit()

        self.ui.postsTableView.horizontalHeader().setSectionResizeMode(
            self.posts_header.index('content'), QHeaderView.Stretch
        )
        self.ui.postsTableView.scrollToBottom()

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
        self.ui.bonusButton.setEnabled(False)

        thread = self.nga.Thread(self.tid)
        self.logger.info(f'Thread found: {thread.subject}')

        result_queue, seen_uids, posts_queue = Queue(), Queue(), Queue()
        config = {
            'duplicate': self.ui.duplicateCheckBox.isChecked(),
            'img': self.ui.imgCheckBox.isChecked(),
            'keyword': self.ui.keywordEdit.text(),
            'max_floor': self.ui.maxFloorEdit.text(),
            'skip': self.ui.skipCheckBox.isChecked(),
        }

        def func(lou, post):
            mask = _generate_mask(lou, post, seen_uids, config)

            return lou, post, mask

        def total_ontrigger(total):
            self.ui.progressBar.setMaximum(total)

        def progress_ontrigger(index):
            self.ui.progressBar.setValue(index + 1)

        def error_ontrigger(exception, traceback):
            self.logger.error(traceback)
            self.logger.error(exception)

        def result_ontrigger(result):
            lou, post, mask = result

            posts_queue.put((lou, post.pid, post.user.username, post.user.uid, post.content[:30], mask))
            if mask:
                result_queue.put(result)

            self._refresh_posts_from_queue(posts_queue)

        def done_ontrigger():
            self.bonus_data = [
                (lou, post)
                for lou, post, mask in list(result_queue.queue)
            ]
            self.ui.bonusButton.setEnabled(True)

            elapsed = time() - self._start_time
            self.logger.info(f'DONE, {len(self.bonus_data)} posts to be bonus-ed, {elapsed:.2f}s elapsed.')

        self.worker = Worker(func, thread.posts.items())
        self.worker.signals.total.connect(total_ontrigger)
        self.worker.signals.progress.connect(progress_ontrigger)
        self.worker.signals.error.connect(error_ontrigger)
        self.worker.signals.result.connect(result_ontrigger)
        self.worker.signals.done.connect(done_ontrigger)

        self._start_time = time()
        self.thread_pool.start(self.worker)

    @ExceptHandler(logger)
    def _stop(self):
        if self.worker:
            self.worker.signals.force_stop.emit()

    @ExceptHandler(logger)
    def _bonus(self):
        reputation, add_rvrc, add_gold = self._configure_bonus()
        options = ['给作者发送PM']
        if add_rvrc:
            options.append('增加威望')
        if add_gold:
            options.append('增加/扣除金钱')

        self.logger.info('Starting mass bonus...')
        self.ui.startButton.setEnabled(False)

        def func(lou, post):
            post.add_point(reputation, info=f'QtNGA/{__version__}', options=options)

        def total_ontrigger(total):
            self.ui.progressBar.setMaximum(total)

        def progress_ontrigger(index):
            self.ui.progressBar.setValue(index + 1)

        def error_ontrigger(exception, traceback):
            self.logger.error(traceback)
            self.logger.error(exception)

        def result_ontrigger(result):
            pass

        def done_ontrigger():
            self.ui.startButton.setEnabled(True)
            self.logger.info(f'DONE, {time() - self._start_time:.2f}s elapsed.')

        self.worker = Worker(func, self.bonus_data)
        self.worker.signals.total.connect(total_ontrigger)
        self.worker.signals.progress.connect(progress_ontrigger)
        self.worker.signals.error.connect(error_ontrigger)
        self.worker.signals.result.connect(result_ontrigger)
        self.worker.signals.done.connect(done_ontrigger)

        self._start_time = time()
        self.thread_pool.start(self.worker)

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
