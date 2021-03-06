###############################################################################
# Copyright (c) 2018 Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory
#
# Written by J. Chavez, S. Czyz, G. Kosinovsky, V. Mozin, S. Sangiorgio.
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
from PyQt5.QtWidgets import QHeaderView, QMessageBox
from PyQt5.QtCore import pyqtSlot

from .table_def import Session, Replay, ResultsTranslator
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
        self.buttonSave.clicked.connect(self.accept)
        self.buttonExport.clicked.connect(self.handleExport)
        self.buttonImport.clicked.connect(self.handleImport)
        self.addNewReplayButton.clicked.connect(self.on_btnNewReplay_clicked)

    def setReplaysTable(self):
        replays = list(self.session.query(Replay))
        if self.tblReplays:
            self.tblReplays.clear()
        self.tblReplays.setColumnCount(NUM_COL)
        self.tblReplays.setRowCount(len(replays))
        self.tblReplays.setHorizontalHeaderLabels(['Name', 'Replay exe', 'Cmd Line', 'Settings', 'n42 Input Template', 'Results Translator Exe', 'Cmd Line' , 'Settings'])
        self.tblReplays.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tblReplays.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        row = 0
        for replay in replays:
            self.tblReplays.setItem(row, NAME, QTableWidgetItem(replay.name))
            self.tblReplays.setItem(row, REPL_PATH, QTableWidgetItem(replay.exe_path))
            if replay.is_cmd_line:
                self.tblReplays.setItem(row, REPL_IS_CMD_LINE, QTableWidgetItem("Yes"))
            else:
                self.tblReplays.setItem(row, REPL_IS_CMD_LINE, QTableWidgetItem("No"))
            self.tblReplays.setItem(row, REPL_SETTING, QTableWidgetItem(replay.settings))
            self.tblReplays.setItem(row, TEMPLATE_PATH, QTableWidgetItem(replay.n42_template_path))
            resultsTranslator = self.session.query(ResultsTranslator).filter_by(name=replay.name).first()
            if resultsTranslator:
                self.tblReplays.setItem(row, TRANSL_PATH, QTableWidgetItem(resultsTranslator.exe_path))
                if resultsTranslator.is_cmd_line:
                    self.tblReplays.setItem(row, TRANSL_IS_CMD_LINE, QTableWidgetItem("Yes"))
                else:
                    self.tblReplays.setItem(row, TRANSL_IS_CMD_LINE, QTableWidgetItem("No"))
                self.tblReplays.setItem(row, TRANSL_SETTING, QTableWidgetItem(resultsTranslator.settings))
            row = row + 1
        self.tblReplays.setEditTriggers(QAbstractItemView.NoEditTriggers)

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

    @pyqtSlot(int, int)
    def on_tblReplays_cellDoubleClicked(self, row, col):
        """
        Edit existing replay on double clicking a row
        """
        replay = self.session.query(Replay).filter_by(
            name=self.tblReplays.item(row, NAME).text()).first()
        resultsTranslator = self.session.query(ResultsTranslator).filter_by(
            name=self.tblReplays.item(row, NAME).text()).first()
        if ReplayDialog(self, replay, resultsTranslator).exec_():
            self.setReplaysTable()

    def handleExport(self):
        """
        Exports to CSV
        """
        path = QFileDialog.getSaveFileName(self, 'Save File', self.settings.getDataDirectory(), 'CSV (*.csv)')
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
            resTranslatorDelete = self.session.query(ResultsTranslator).filter(ResultsTranslator.name == name)
            if resTranslatorDelete:
                resTranslatorDelete.delete()
            self.session.commit()
            if self.parent:
                self.parent.cmbReplay.removeItem(self.parent.cmbReplay.findText(name))

    def accept(self):
        """
        Saves changes
        """
        session = Session()
        for repl in session.query(Replay):
            replayDelete = self.session.query(Replay).filter(Replay.name == repl.name)
            replayDelete.delete()
        for resTrans in session.query(ResultsTranslator):
            resTranslatorDelete = self.session.query(ResultsTranslator).filter(ResultsTranslator.name == resTrans.name)
            resTranslatorDelete.delete()
        for row in range(self.tblReplays.rowCount()):
            nameItem = self.tblReplays.item(row, NAME)
            if not nameItem:
                QMessageBox.critical(self, 'Insufficient Information', 'Must specify a replay tool name')
                return
            isReplCmdItem = self.tblReplays.item(row, REPL_IS_CMD_LINE)
            if not isReplCmdItem:
                QMessageBox.critical(self, 'Insufficient Information', 'Must specify whether replay tool is command line')
                return
            else:
                if isReplCmdItem.text().lower() == "yes":
                    isReplCmd = True
                elif isReplCmdItem.text().lower() == "no":
                    isReplCmd = False
                else:
                    QMessageBox.critical(self, 'Improper Input', ' Replay Cmd Line setting must be Yes or No')
                    return
            resTranslPathItem = self.tblReplays.item(row, TRANSL_PATH)
            isResTransCmdItem = self.tblReplays.item(row, TRANSL_IS_CMD_LINE)
            if len(resTranslPathItem.text()) > 0:
                if not isResTransCmdItem:
                    QMessageBox.critical(self, 'Insufficient Information', 'If Results Translator path set, must specify whether Results Translator is command line')
                    return
                if isResTransCmdItem.text().lower() == "yes":
                    isResTransCmd = True
                elif isResTransCmdItem.text().lower() == "no":
                    isResTransCmd = False
                else:
                    QMessageBox.critical(self, 'Improper Input', ' Results Translator Cmd Line setting must be Yes or No')
                    return
            replay = Replay(name = nameItem.text())
            replay.exe_path = self.tblReplays.item(row, REPL_PATH).text()
            replay.is_cmd_line = isReplCmd
            if self.tblReplays.item(row, REPL_SETTING):
                replay.settings = self.tblReplays.item(row, REPL_SETTING).text()
            if self.tblReplays.item(row, TEMPLATE_PATH):
                replay.n42_template_path = self.tblReplays.item(row, TEMPLATE_PATH).text()
            session.add(replay)
            if len(resTranslPathItem.text()) > 0:
                resultsTranslator = ResultsTranslator(name = nameItem.text())
                resultsTranslator.exe_path = resTranslPathItem.text()
                resultsTranslator.is_cmd_line = isResTransCmd
                if self.tblReplays.item(row, TRANSL_SETTING):
                    resultsTranslator.settings = self.tblReplays.item(row, TRANSL_SETTING).text()
                session.add(resultsTranslator)
        session.commit()
        return QDialog.accept(self)

    def oK(self):
        """
        Closes dialog
        """
        return QDialog.accept(self)

