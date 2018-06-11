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
This module supports import, export and deletion of user defined replay options
"""

import csv

from PyQt5.QtWidgets import QDialog, QFileDialog, QTableWidgetItem, QAbstractItemView
from PyQt5.QtWidgets import QHeaderView

from .table_def import Session, Replay, ResultsTranslator
from .ui_generated import ui_manage_replays_dialog
from src.rase_settings import RaseSettings


class ManageReplaysDialog(ui_manage_replays_dialog.Ui_Dialog, QDialog):
    def __init__(self, parent = None):
        QDialog.__init__(self)
        self.parent = parent
        self.session = Session()
        self.settings = RaseSettings()
        replays = list(self.session.query(Replay))
        self.setupUi(self)
        self.tblReplays.setColumnCount(8)
        self.tblReplays.setRowCount(len(replays))
        self.tblReplays.setHorizontalHeaderLabels(['Name', 'Replay exe', 'Cmd Line', 'Settings', 'n42 Input Template', 'Results Translator Exe', 'Cmd Line' , 'Settings'])
        self.tblReplays.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tblReplays.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        row = 0
        for replay in replays:
            self.tblReplays.setItem(row, 0, QTableWidgetItem(replay.name))
            self.tblReplays.setItem(row, 1, QTableWidgetItem(replay.exe_path))
            if replay.is_cmd_line:
                self.tblReplays.setItem(row, 2, QTableWidgetItem("Yes"))
            else:
                self.tblReplays.setItem(row, 2, QTableWidgetItem("No"))
            self.tblReplays.setItem(row, 3, QTableWidgetItem(replay.settings))
            self.tblReplays.setItem(row, 4, QTableWidgetItem(replay.n42_template_path))
            resultsTranslator = self.session.query(ResultsTranslator).filter_by(name=replay.name).first()
            if resultsTranslator:
                self.tblReplays.setItem(row, 5, QTableWidgetItem(resultsTranslator.exe_path))
                if resultsTranslator.is_cmd_line:
                    self.tblReplays.setItem(row, 6, QTableWidgetItem("Yes"))
                else:
                    self.tblReplays.setItem(row, 6, QTableWidgetItem("No"))
                self.tblReplays.setItem(row, 7, QTableWidgetItem(resultsTranslator.settings))
            row = row + 1
        self.deleteSelectedReplaysButton.clicked.connect(self.deleteSelectedReplays)
        self.btnOK.clicked.connect(self.oK)
        self.buttonExport.clicked.connect(self.handleExport)

    def handleExport(self):
        """
        Exports to CSV
        """
        path = QFileDialog.getSaveFileName(self, 'Save File', '', 'CSV (*.csv)')
        if path[0]:
            with open(path[0], mode='w', newline='') as stream:
                writer = csv.writer(stream)
                for row in range(self.tblReplays.rowCount()):
                    rowdata = []
                    for column in range(self.tblReplays.columnCount()):
                        item = self.tblReplays.item(row, column)
                        if item is not None:
                            rowdata.append(item.text())
                        else:
                            rowdata.append('')
                    writer.writerow(rowdata)

    def handleImport(self):
        """
        Imports from CSV
        """
        path = QFileDialog.getOpenFileName(self, 'Open File', self.settings.getDataDirectory(), 'CSV(*.csv)')
        if path[0]:
            # FIXME: This doesn't check in any way that the format of the file is correct
            with open(path[0], mode='r') as stream:
                self.tblReplays.setRowCount(0)
                self.tblReplays.setColumnCount(0)
                for rowdata in csv.reader(stream):
                    row = self.tblReplays.rowCount()
                    self.tblReplays.insertRow(row)
                    self.tblReplays.setColumnCount(len(rowdata))
                    for column, data in enumerate(rowdata):
                        item = QTableWidgetItem(data)
                        self.tblReplays.setItem(row, column, item)
            self.tblReplays.setHorizontalHeaderLabels(
                ['Name', 'Replay exe', 'Cmd Line', 'Settings', 'n42 Input Template', 'Results Translator Exe',
                 'Cmd Line', 'Settings'])

    def deleteSelectedReplays(self):
        """
        Deletes Selected Replays
        """
        rows = self.tblReplays.selectionModel().selectedRows()
        indices =[]
        for r in rows:
            indices.append(r.row())
        indices.sort(reverse=True)
        for index in indices:
            name = self.tblReplays.item(index,0).text()
            self.tblReplays.removeRow(index)
            replayDelete = self.session.query(Replay).filter(Replay.name == name)
            replayDelete.delete()
            self.session.commit()
            if self.parent:
                self.parent.cmbReplay.removeItem(self.parent.cmbReplay.findText(name))

    def oK(self):
        """
        Closes dialog
        """
        return QDialog.accept(self)

