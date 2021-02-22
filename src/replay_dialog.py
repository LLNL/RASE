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
This module allows the user to select replay and results translator executables
as well as the translator template
"""

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDialog, QFileDialog, QMessageBox

from src.rase_settings import RaseSettings
from .table_def import Replay, ResultsTranslator, Session
from .ui_generated import ui_new_replay_dialog


class ReplayDialog(ui_new_replay_dialog.Ui_ReplayDialog, QDialog):
    def __init__(self, parent, replay=None, resultsTranslator=None):
        QDialog.__init__(self, parent)
        self.parent = parent
        self.setupUi(self)
        self.settings = RaseSettings()
        self.replay = replay
        self.resultsTranslator = resultsTranslator

        if replay:
            self.setWindowTitle('Edit Replay Software')
            self.txtName.setReadOnly(True)
            self.txtName.setText(replay.name)
            self.txtCmdLine.setText(replay.exe_path)
            self.txtSettings.setText(replay.settings)
            self.cbCmdLine.setChecked(bool(replay.is_cmd_line))
            self.txtTemplatePath.setText(replay.n42_template_path)
            self.txtFilenameSuffix.setText(replay.input_filename_suffix)
        if resultsTranslator:
            self.txtResultsTranslator.setText(resultsTranslator.exe_path)
            self.txtSettings_3.setText(resultsTranslator.settings)
            self.cbCmdLine_3.setChecked(bool(resultsTranslator.is_cmd_line))

    @pyqtSlot(bool)
    def on_btnBrowseExecutable_clicked(self, checked):
        """
        Selects Replay executable
        """
        filepath = QFileDialog.getOpenFileName(self, 'Path to Replay Tool', self.settings.getDataDirectory())[0]
        if filepath:
            self.txtCmdLine.setText(filepath)

    @pyqtSlot(bool)
    def on_btnBrowseTranslator_clicked(self, checked):
        """
        Selects Translator Template
        """
        filepath = QFileDialog.getOpenFileName(self, 'Path to n42 Template', self.settings.getDataDirectory())[0]
        if filepath:
            self.txtTemplatePath.setText(filepath)

    @pyqtSlot(bool)
    def on_btnBrowseResultsTranslator_clicked(self, checked):
        """
        Selects Results Translator Executable
        """
        filepath = QFileDialog.getOpenFileName(self, 'Path to Results Translator Tool', self.settings.getDataDirectory())[0]
        if filepath:
            self.txtResultsTranslator.setText(filepath)

    @pyqtSlot()
    def accept(self):
        name = self.txtName.text()
        if not name:
            QMessageBox.critical(self, 'Insufficient Information', 'Must specify a replay tool name')
            return
        session = Session()
        if not self.replay:
            repl = session.query(Replay).filter_by(name=name).first()
            if repl:
                QMessageBox.warning(self, 'Bad Replay Name', 'Replay with this name exists. Specify Different Replay Name')
                return
            self.replay = Replay(name=name)
            self.parent.new_replay = self.replay
            session.add(self.replay)
        self.replay.exe_path    = self.txtCmdLine.text()
        self.replay.is_cmd_line = self.cbCmdLine.isChecked()
        self.replay.settings    = self.txtSettings.text().strip()
        self.replay.n42_template_path = self.txtTemplatePath.text()
        self.replay.input_filename_suffix = self.txtFilenameSuffix.text()

        if not self.resultsTranslator:
            self.resultsTranslator = ResultsTranslator(name=name)
            session.add(self.resultsTranslator)
        self.resultsTranslator.exe_path    = self.txtResultsTranslator.text()
        self.resultsTranslator.is_cmd_line = self.cbCmdLine_3.isChecked()
        self.resultsTranslator.settings    = self.txtSettings_3.text().strip()
        session.commit()
        return QDialog.accept(self)

