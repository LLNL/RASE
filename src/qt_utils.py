###############################################################################
# Copyright (c) 2018-2022 Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory
#
# Written by J. Chavez, S. Czyz, G. Kosinovsky, V. Mozin, S. Sangiorgio.
# RASE-support@llnl.gov.
#
# LLNL-CODE-841943, LLNL-CODE-829509
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

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, QRect
import sys
from PySide6.QtCore import QEventLoop, Slot, QObject, Signal


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

    @Slot()
    @Slot(bool)
    @Slot(str)
    @Slot(int)
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


class DoubleValidator(QtGui.QDoubleValidator):
    '''Reimplements QDoubleValidator with signal when validation changes'''
    validationChanged = Signal(QtGui.QValidator.State)

    def validate(self, input, pos):
        state, input, pos = super().validate(input, pos)
        self.validationChanged.emit(state)
        return state, input, pos


class DoubleValidatorInfinity(QtGui.QDoubleValidator):
    '''
    Reimplements QDoubleValidator with signal when validation changes
    and accepts '+inf' and '-inf' values
    '''
    validationChanged = Signal(QtGui.QValidator.State)

    def validate(self, input, pos):
        state, input, pos = super().validate(input, pos)
        if input == 'i' or input == 'in' or input == '-i' or input == '-in':
            state = QtGui.QValidator.Intermediate
        if input == 'inf' or input == '-inf':
            state = QtGui.QValidator.Acceptable
        self.validationChanged.emit(state)
        return state, input, pos


class IntValidator(QtGui.QIntValidator):
    '''Reimplements QIntValidator with signal when validation changes'''
    validationChanged = Signal(QtGui.QValidator.State)

    def validate(self, input, pos):
        state, input, pos = super().validate(input, pos)
        self.validationChanged.emit(state)
        return state, input, pos


class RegExpValidator(QtGui.QRegularExpressionValidator):
    """Reimplements QRegularExpressionValidator with signal when validation changes"""
    validationChanged = Signal(QtGui.QValidator.State)

    def validate(self, input, pos):
        state, input, pos = super().validate(input, pos)
        self.validationChanged.emit(state)
        return state, input, pos
