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
This module displays detailed replay/analysis results for a particular
instrument/scenario combination
"""

import csv

from PyQt5.QtWidgets import QTableWidgetItem, QDialog, QFileDialog, \
    QHeaderView

from .table_def import Session
from .ui_generated import ui_detailed_results_dialog
from src.rase_settings import RaseSettings


class DetailedResultsDialog(ui_detailed_results_dialog.Ui_dlgDetailedResults, QDialog):
    def __init__(self, resultMap):
        QDialog.__init__(self)
        self.setupUi(self)
        self.settings = RaseSettings()
        self.headerLabels = ['File', 'Tp', 'Fn', 'Fp', 'Precision', 'Recall', 'Fscore', 'IDs']
        self.NUM_COLS = len(self.headerLabels)
        self.session = Session()
        self.tblDetailedResults.setColumnCount(self.NUM_COLS)
        self.tblDetailedResults.setHorizontalHeaderLabels(self.headerLabels)
        self.tblDetailedResults.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tblDetailedResults.setRowCount(0)
        row=0
        for file in resultMap:
            results = resultMap[file]
            results.insert(0, file)
            self.tblDetailedResults.insertRow(row)
            for col in range(self.NUM_COLS):
                self.tblDetailedResults.setItem(row, col, QTableWidgetItem(results[col]))
            row = row + 1
            results.pop(0)
        self.tblDetailedResults.resizeColumnsToContents()
        self.tblDetailedResults.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.buttonOK.clicked.connect(self.closeSelected)
        self.buttonExport.clicked.connect(self.handleExport)

    def handleExport(self):
        """
        exports to CSV
        """
        path = QFileDialog.getSaveFileName(self, 'Save File', '', 'CSV (*.csv)')
        if path[0]:
            with open(path[0], mode='w', newline='') as stream:
                writer = csv.writer(stream)
                for row in range(self.tblDetailedResults.rowCount()):
                    rowdata = []
                    for column in range(self.tblDetailedResults.columnCount()):
                        item = self.tblDetailedResults.item(row, column)
                        if item is not None:
                            rowdata.append(item.text())
                        else:
                            rowdata.append('')
                    writer.writerow(rowdata)


    def closeSelected(self):
        """
        Closes dialog
        """
        super().accept()

