###############################################################################
# Copyright (c) 2018 Lawrence Livermore National Security, LLC.
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
"""
This module allows user to input seed for Random Number Generation to ensure reproducible
validation results
"""

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDialog, QMessageBox

from src.rase_settings import RaseSettings
from .ui_generated import ui_input_random_seed
from math import pow


class RandomSeedDialog(ui_input_random_seed.Ui_InputRandomSeedDialog, QDialog):
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.settings = RaseSettings()
        self.setupUi(self)
        self.txtRandomVal.setText(str(self.settings.getRandomSeed()))
        if self.settings.getRandomSeedFixed():
            self.txtRandomVal.setEnabled(True)
            self.checkBox.setChecked(True)
        else:
            self.txtRandomVal.setDisabled(True)
            self.checkBox.setChecked(False)
        self.checkBox.stateChanged.connect(self.checkChanged)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    @pyqtSlot()
    def accept(self):
        randomText = self.txtRandomVal.text()
        if randomText and self.is_number(randomText) and float(randomText) >= 1 and float(randomText) <= pow(2,30):
            self.settings.setRandomSeed(int(float(randomText)))
            self.settings.setRandomSeedFixed(self.checkBox.isChecked())
            super().accept()

        else:
            QMessageBox.information(self, 'Invalid Random Seed Value',
                                        'seed value must be numeric between 1 and 1,073,741,824')
            super().accept()
            dialog = RandomSeedDialog(self)
            dialog.exec_()
    @pyqtSlot()
    def reject(self):
        super().accept()

    def checkChanged(self):
        """
        enables txtRandomVal IFF the box is checked
        """
        if self.checkBox.isChecked():
            self.txtRandomVal.setEnabled(True)
        else:
            self.txtRandomVal.setDisabled(True)

    def is_number(self,s):
        """
        returns True if string is a number.
        """
        try:
            float(s)
            return True
        except ValueError:
            return False