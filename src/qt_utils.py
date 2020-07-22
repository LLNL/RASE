from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QRect
import sys
from PyQt5.QtCore import QEventLoop, pyqtSlot, QObject


class QSignalWait(QObject):
    """
    Class that waits for a QTSignal and returns its value
    Works only with signals with no type or type int,str,bool
    """
    def __init__(self, signal, parent=None):
        super(QSignalWait, self).__init__(parent)
        self.state = None
        self.signal = signal
        self.loop = QEventLoop()

    @pyqtSlot()
    @pyqtSlot(bool)
    @pyqtSlot(str)
    @pyqtSlot(int)
    def _quit(self, state = None):
        self.state = state
        self.loop.quit()

    def wait(self):
        """Waits for a signal to be emitted.
        """
        self.signal.connect(self._quit)
        self.loop.exec()
        self.signal.disconnect(self._quit)
        return self.state
