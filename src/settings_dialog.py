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
"""
This module allows user to change program settings such as the data directory
and sampling algorithm
"""

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDialog, QFileDialog, QMessageBox

from src import sampling_algos
from src.rase_settings import RaseSettings
from .ui_generated import ui_prefs_dialog
import os
import sys
import inspect


class SettingsDialog(ui_prefs_dialog.Ui_Dialog, QDialog):
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.settings = RaseSettings()
        self.setupUi(self)
        self.txtDataDir.setReadOnly(True)
        self.txtDataDir.setText(self.settings.getDataDirectory())
        self.dataDirectoryChanged = False
        self.algoDictionary = {}

        algoCount = 0

        for name, data in inspect.getmembers(sampling_algos, predicate=inspect.isfunction):
            try:
                readable_name = data.__doc__.splitlines()[0].strip()
                if readable_name == '':
                    raise Exception("")
            except:
                readable_name = name
            self.downSapmplingAlgoComboBox.addItem(readable_name)
            self.algoDictionary[algoCount] = data
            if data == self.settings.getSamplingAlgo():
                self.downSapmplingAlgoComboBox.setCurrentIndex(algoCount)
            algoCount += 1
        self.algorithmSelected = False
        self.downSapmplingAlgoComboBox.currentIndexChanged.connect(self.chooseSamplingAlgo)

    @pyqtSlot(bool)
    def on_btnBrowseDataDir_clicked(self, checked):
        """
        Selects Data Directory
        """
        options = QFileDialog.ShowDirsOnly
        if sys.platform.startswith('win'): options = QFileDialog.DontUseNativeDialog
        dir = QFileDialog.getExistingDirectory(self, 'Choose RASE Data Directory', self.settings.getDataDirectory(),
                                               options)
        if dir:
            self.txtDataDir.setText(dir)
            self.dataDirectoryChanged = True

    def chooseSamplingAlgo(self, index):
        """
        Selects Sampling Algo
        """
        self.algorithmSelected = True


    @pyqtSlot()
    def accept(self):
        if self.dataDirectoryChanged:
            self.settings.setDataDirectory(os.path.normpath(self.txtDataDir.text()))
        idx = self.downSapmplingAlgoComboBox.currentIndex()
        if self. algorithmSelected:
            self.settings.setSamplingAlgo(self.algoDictionary[idx])
        # if current state is different from initial state (somehow record the initial state so if the user toggles
        # but then toggles back the user is not prompted to reset RASE)

        super().accept()
