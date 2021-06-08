###############################################################################
# Copyright (c) 2018-2021 Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory
#
# Written by J. Chavez, S. Czyz, G. Kosinovsky, V. Mozin, S. Sangiorgio.
# RASE-support@llnl.gov.
#
# LLNL-CODE-819515
#
# All rights reserved.
#
# This file is part of RASE.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED,INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
###############################################################################

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
