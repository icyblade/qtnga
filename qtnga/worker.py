import traceback

from PyQt5.QtCore import pyqtSignal, QObject, QRunnable, pyqtSlot


class WorkerSignal(QObject):
    """Signal for QtNGA workers.

    Properties
    --------
    progress: pyqtSignal
        Contains an int object, indicating current works have been done.
        Usually used in progress bar.
    total: pyqtSignal
        Contains an int object, indicating total works to be done.
        Usually used in progress bar.
    error: pyqtSignal
        Contains a tuple of Exception and traceback, indicating exception raised.
    result: pyqtSignal
        Contains an object, indicating return value of jobs.
    done: pyqtSignal
        Indicating whether work has been done.
    force_stop: pyqtSignal
        Indicating whether work has been force stopped.
    """
    progress = pyqtSignal(int)
    total = pyqtSignal(int)
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    done = pyqtSignal()
    force_stop = pyqtSignal()


class Worker(QRunnable):
    """Common QtNGA worker.

    Basically it's `func(i) for i in full_batch`

    Parameters
    --------
    func: callable
        Function to be called.
    full_batch: iterable
        Jobs to be done.
    """
    def __init__(self, func, full_batch):
        super(Worker, self).__init__()

        self.func = func
        self.full_batch = full_batch
        self.signals = WorkerSignal()
        self.stopped = False

        def done_update():
            self.stopped = True

        self.signals.force_stop.connect(done_update)

    @pyqtSlot()
    def run(self):
        try:
            self.signals.total.emit(len(self.full_batch))
        except TypeError:
            self.signals.total.emit(None)

        for index, args in enumerate(self.full_batch):
            if self.stopped:
                break
            try:
                result = self.func(*args)
            except Exception as e:
                self.signals.error.emit((e, traceback.format_exc()))
            else:
                self.signals.result.emit(result)
            finally:
                self.signals.progress.emit(index)

        self.signals.done.emit()
