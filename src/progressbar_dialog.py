###############################################################################
# Copyright (c) 2018 Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory
#
# Written by J. Chavez, G. Kosinovsky, V. Mozin, S. Sangiorgio.
# RASE-support@llnl.gov.
#
# LLNL-CODE-750919
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
"""
This module defines the progress bar module used when loading base spectra
"""

import time

from PyQt5.QtCore import QThread, pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QDialog, QProgressBar, QPushButton, QLabel, QGridLayout


class ProgressBar(QDialog):
    """
    Generic progress bar dialog that run a Worker function.
    The worker function needs to define a sig_step and sig_done signals
    and must have a 'work' and 'abort' methods.
    Once finished, a sig_finished signal is emitted.
    """

    sig_abort_worker = pyqtSignal()
    sig_finished = pyqtSignal(bool)

    def __init__(self, parent):
        super(ProgressBar, self).__init__(parent)
        self.setWindowTitle('Progress')

        self.progress = QProgressBar(self)
        self.progress.setGeometry(0, 0, 300, 35)
        self.progress.setFormat("%p%")
        self.progress.setTextVisible(True)

        self.button_stop = QPushButton('Cancel', self)
        self.button_stop.clicked.connect(self.abort_worker)
        self.button_stop.move(0, 30)

        self.label = QLabel()
        self.label.setText("Estimating time remaining...")

        self.title = QLabel()
        self.title.setText("Working")

        self.layout = QGridLayout()
        self.layout.addWidget(self.title, 0, 0)
        self.layout.addWidget(self.progress, 1, 0)
        self.layout.addWidget(self.label, 2, 0)
        self.layout.addWidget(self.button_stop, 3, 0)

        self.setLayout(self.layout)
        self.setModal(True)
        self.show()

        self.t = 0
        # self.button_stop.setDisabled(True)

    def run(self, worker, ):
        # get the worker function to a
        self.worker = worker
        self.thread = QThread()
        self.worker.moveToThread(self.thread)

        # get progress messages from worker:
        self.worker.sig_step.connect(self.onCountChanged)
        self.worker.sig_done.connect(self.on_worker_done)

        # control worker:
        self.sig_abort_worker.connect(self.worker.abort)

        # get ready to start worker:
        self.thread.started.connect(self.worker.work)
        self.thread.start()  # this will emit 'started' and start thread's event loop
        self.t = time.time()

    @pyqtSlot(int)
    def onCountChanged(self, value):
        self.progress.setValue(value)
        deltaT = (time.time() - self.t) / float(value)
        # self.t = curr_time
        time_str = str(int(deltaT * (self.progress.maximum() - value)) + 1)
        self.label.setText("Time Remaining: " + time_str + " seconds")

    @pyqtSlot(bool)
    def on_worker_done(self, value):
        self.thread.quit()
        self.thread.wait()
        self.close()
        self.sig_finished.emit(value)

    @pyqtSlot()
    def abort_worker(self):
        self.sig_abort_worker.emit()

    # override close event method to ensure thread is aborted
    def closeEvent(self, event):
        self.abort_worker()
        event.accept()  # let the window close
