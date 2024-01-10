###############################################################################
# Copyright (c) 2018-2023 Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory
#
# Written by J. Brodsky, J. Chavez, S. Czyz, G. Kosinovsky, V. Mozin,
#            S. Sangiorgio.
#
# RASE-support@llnl.gov.
#
# LLNL-CODE-858590, LLNL-CODE-829509
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


class DoubleOrEmptyDelegate(QtWidgets.QItemDelegate):
    def __init__(self):
        QtWidgets.QItemDelegate.__init__(self)

    def createEditor(self, parent, option, index):
        editor = QtWidgets.QLineEdit(parent)
        editor.setValidator(DoubleAndEmptyValidator(bottom=0))
        return editor


class DoubleAndEmptyValidator(QtGui.QDoubleValidator):
    """
    Validate double values or empty string.
    """

    def validate(self, inputText, pos):
        """
        Reimplemented from `QDoubleValidator.validate`.
        Allow to provide an empty value.
        :param str inputText: Text to validate
        :param int pos: Position of the cursor
        """
        if inputText.strip() == "":
            # python API is not the same as C++ one
            return QtGui.QValidator.Acceptable, inputText, pos
        return super(DoubleAndEmptyValidator, self).validate(inputText, pos)

    def toValue(self, text):
        """Convert the input string into an interpreted value
        :param str text: Input string
        :rtype: Tuple[object,bool]
        :returns: A tuple containing the resulting object and True if the
            string is valid
        """
        if text.strip() == "":
            return None, True
        value, validated = self.locale().toDouble(text)
        return value, validated

    def toText(self, value):
        """Convert the input string into an interpreted value
        :param object value: Input object
        :rtype: str
        """
        if value is None:
            return ""
        return str(value)