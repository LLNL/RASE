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
"""
This module supports import, export and deletion of user defined replay options
"""

import csv

from PySide6.QtWidgets import QDialog, QFileDialog, QTableWidgetItem, QAbstractItemView
from PySide6.QtWidgets import QHeaderView, QMessageBox
from PySide6.QtCore import Slot

from .table_def import Session, Replay, ResultsTranslator, ReplayTypes
from .ui_generated import ui_manage_replays_dialog
from src.rase_settings import RaseSettings
from .replay_dialog import ReplayDialog

NUM_COL = 8
NAME, REPL_PATH, REPL_IS_CMD_LINE, REPL_SETTING, TEMPLATE_PATH, TRANSL_PATH, TRANSL_IS_CMD_LINE, TRANSL_SETTING  = range(NUM_COL)

class ManageReplaysDialog(ui_manage_replays_dialog.Ui_Dialog, QDialog):
    def __init__(self, parent = None):
        QDialog.__init__(self)
        self.parent = parent
        self.session = Session()
        self.settings = RaseSettings()
        self.setupUi(self)
        self.setReplaysTable()
        self.deleteSelectedReplaysButton.clicked.connect(self.deleteSelectedReplays)
        self.btnOK.clicked.connect(self.oK)
        self.buttonExport.clicked.connect(self.handleExport)
        self.buttonImport.clicked.connect(self.handleImport)
        self.addNewReplayButton.clicked.connect(self.on_btnNewReplay_clicked)
        self.tblStandaloneReplays.cellDoubleClicked.connect(self.on_cellDoubleClicked)
        self.tblWebReplays.cellDoubleClicked.connect(self.on_cellDoubleClicked)

    def setReplaysTable(self):
        # Load Standalone Replay Tools
        replays = list(self.session.query(Replay).filter_by(type=ReplayTypes.standalone))
        if self.tblStandaloneReplays:
            self.tblStandaloneReplays.clear()
        self.tblStandaloneReplays.setColumnCount(NUM_COL)
        self.tblStandaloneReplays.setRowCount(len(replays))
        self.tblStandaloneReplays.setHorizontalHeaderLabels(['Name', 'Replay exe', 'Cmd Line', 'Settings', 'n42 Input Template', 'Results Translator Exe', 'Cmd Line' , 'Settings'])
        self.tblStandaloneReplays.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tblStandaloneReplays.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for row, replay in enumerate(replays):
            self.tblStandaloneReplays.setItem(row, NAME, QTableWidgetItem(replay.name))
            self.tblStandaloneReplays.setItem(row, REPL_PATH, QTableWidgetItem(replay.exe_path))
            self.tblStandaloneReplays.setItem(row, REPL_IS_CMD_LINE, QTableWidgetItem("Yes" if replay.is_cmd_line else "No"))
            self.tblStandaloneReplays.setItem(row, REPL_SETTING, QTableWidgetItem(replay.settings))
            self.tblStandaloneReplays.setItem(row, TEMPLATE_PATH, QTableWidgetItem(replay.n42_template_path))
            resultsTranslator = self.session.query(ResultsTranslator).filter_by(name=replay.name).first()
            if resultsTranslator:
                self.tblStandaloneReplays.setItem(row, TRANSL_PATH, QTableWidgetItem(resultsTranslator.exe_path))
                self.tblStandaloneReplays.setItem(row, TRANSL_IS_CMD_LINE, QTableWidgetItem("Yes" if resultsTranslator.is_cmd_line else "No"))
                self.tblStandaloneReplays.setItem(row, TRANSL_SETTING, QTableWidgetItem(resultsTranslator.settings))
            else:
                self.tblStandaloneReplays.setItem(row, TRANSL_IS_CMD_LINE, QTableWidgetItem(" "))
                self.tblStandaloneReplays.setItem(row, TRANSL_SETTING, QTableWidgetItem(" "))
        self.tblStandaloneReplays.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # Load Web ID Replay Tools
        replays = list(self.session.query(Replay).filter_by(type=ReplayTypes.gadras_web))
        if self.tblWebReplays:
            self.tblWebReplays.clear()
        self.tblWebReplays.setColumnCount(3)
        self.tblWebReplays.setRowCount(len(replays))
        self.tblWebReplays.setHorizontalHeaderLabels(['Name', 'URL', 'Instrument DRF'])
        self.tblWebReplays.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tblWebReplays.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for row, replay in enumerate(replays):
            self.tblWebReplays.setItem(row, 0, QTableWidgetItem(replay.name))
            self.tblWebReplays.setItem(row, 1, QTableWidgetItem(replay.web_address))
            self.tblWebReplays.setItem(row, 2, QTableWidgetItem(replay.drf_name))
        self.tblWebReplays.setEditTriggers(QAbstractItemView.NoEditTriggers)

    def on_btnNewReplay_clicked(self, checked):
        """
        Adds new replay
        """
        dialog = ReplayDialog(self)
        if dialog.exec_():
            self.session.add(dialog.replay)
            self.session.add(dialog.resultsTranslator)
            self.session.commit()
            self.setReplaysTable()

    @Slot(int, int)
    def on_cellDoubleClicked(self, row, col):
        """
        Edit existing replay on double clicking a row
        """
        replay = self.session.query(Replay).filter_by(
            name=self.tblStandaloneReplays.item(row, NAME).text()).first()
        resultsTranslator = self.session.query(ResultsTranslator).filter_by(
            name=self.tblStandaloneReplays.item(row, NAME).text()).first()
        if ReplayDialog(self, replay, resultsTranslator).exec_():
            self.setReplaysTable()

    def handleExport(self):
        """
        Exports to CSV
        """
        # FIXME: works only for the standalone replay tools
        path = QFileDialog.getSaveFileName(self, 'Save File', self.settings.getDataDirectory(), 'CSV (*.csv)')
        if path[0]:
            with open(path[0], mode='w', newline='') as stream:
                writer = csv.writer(stream)
                for row in range(self.tblStandaloneReplays.rowCount()):
                    rowdata = []
                    for column in range(self.tblStandaloneReplays.columnCount()):
                        item = self.tblStandaloneReplays.item(row, column)
                        if item is not None:
                            rowdata.append(item.text())
                        else:
                            rowdata.append('')
                    writer.writerow(rowdata)

    def handleImport(self):
        """
        Imports from CSV
        """
        # FIXME: works only for the standalone replay tools
        path = QFileDialog.getOpenFileName(self, 'Open File', self.settings.getDataDirectory(), 'CSV(*.csv)')
        if path[0]:
            # FIXME: This doesn't check in any way that the format of the file is correct
            with open(path[0], mode='r') as stream:
                self.tblStandaloneReplays.setRowCount(0)
                self.tblStandaloneReplays.setColumnCount(0)
                for rowdata in csv.reader(stream):
                    row = self.tblStandaloneReplays.rowCount()
                    self.tblStandaloneReplays.insertRow(row)
                    self.tblStandaloneReplays.setColumnCount(len(rowdata))
                    for column, data in enumerate(rowdata):
                        item = QTableWidgetItem(data)
                        self.tblStandaloneReplays.setItem(row, column, item)
            self.tblStandaloneReplays.setHorizontalHeaderLabels(
                ['Name', 'Replay exe', 'Cmd Line', 'Settings', 'n42 Input Template', 'Results Translator Exe',
                 'Cmd Line', 'Settings'])

    def deleteSelectedReplays(self):
        """
        Deletes Selected Replays
        """
        for tbl in [self.tblWebReplays, self.tblStandaloneReplays]:
            indices = [r.row() for r in tbl.selectionModel().selectedRows()]
            indices.sort(reverse=True)
            for index in indices:
                name = tbl.item(index, 0).text()
                tbl.removeRow(index)
                replayDelete = self.session.query(Replay).filter(Replay.name == name)
                replayDelete.delete()
                resTranslatorDelete = self.session.query(ResultsTranslator).filter(ResultsTranslator.name == name)
                if resTranslatorDelete:
                    resTranslatorDelete.delete()
                self.session.commit()
                if self.parent:
                    self.parent.cmbReplay.removeItem(self.parent.cmbReplay.findText(name))

    def oK(self):
        """
        Closes dialog
        """
        return QDialog.accept(self)

