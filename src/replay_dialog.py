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
"""
This module allows the user to select replay and results translator executables
as well as the translator template
"""

from PySide6.QtCore import Slot
from PySide6.QtWidgets import QDialog, QFileDialog, QMessageBox

from src.rase_settings import RaseSettings
from .rase_functions import get_DRFList_from_webid
from .table_def import Replay, Session, ReplayTypes
from .ui_generated import ui_new_replay_dialog


class ReplayDialog(ui_new_replay_dialog.Ui_ReplayDialog, QDialog):
    def __init__(self, parent, replay=None):
        QDialog.__init__(self, parent)
        self.parent = parent
        self.setupUi(self)
        self.settings = RaseSettings()
        self.replay = replay

        self.stack.setCurrentIndex(0)
        self.radioStandalone.toggled.connect(lambda x: self.stack.setCurrentIndex(0) if x else None)
        self.radioWeb.toggled.connect(lambda x: self.stack.setCurrentIndex(1) if x else None)

        self.cmbDRFs.addItems(self.settings.getWebIDDRFsList())

        if replay:
            self.radioStandalone.setChecked(self.replay.type == ReplayTypes.standalone)
            self.radioWeb.setChecked(self.replay.type == ReplayTypes.gadras_web)
            self.setWindowTitle('Edit Replay Software')
            # self.txtName.setReadOnly(True)
            self.txtName.setText(replay.name)
            self.txtCmdLine.setText(replay.exe_path)
            self.txtSettings.setText(replay.settings)
            self.cbCmdLine.setChecked(bool(replay.is_cmd_line))
            self.txtTemplatePath.setText(replay.n42_template_path)
            self.txtFilenameSuffix.setText(replay.input_filename_suffix)
            self.txtWebAddress.setText(replay.web_address)
            index = self.cmbDRFs.findText(replay.drf_name)
            self.cmbDRFs.setCurrentIndex(index) if index >=0 else self.cmbDRFs.setCurrentIndex(0)
            if replay.translator_exe_path:
                self.txtResultsTranslator.setText(replay.translator_exe_path)
                self.txtSettings_3.setText(replay.translator_settings)
                self.cbCmdLine_3.setChecked(bool(replay.translator_is_cmd_line))

    @Slot(bool)
    def on_btnBrowseExecutable_clicked(self, checked):
        """
        Selects Replay executable
        """
        filepath = QFileDialog.getOpenFileName(self, 'Path to Replay Tool', self.settings.getDataDirectory())[0]
        if filepath:
            self.txtCmdLine.setText(filepath)

    @Slot(bool)
    def on_btnBrowseTranslator_clicked(self, checked):
        """
        Selects Translator Template
        """
        filepath = QFileDialog.getOpenFileName(self, 'Path to n42 Template', self.settings.getDataDirectory())[0]
        if filepath:
            self.txtTemplatePath.setText(filepath)

    @Slot(bool)
    def on_btnBrowseResultsTranslator_clicked(self, checked):
        """
        Selects Results Translator Executable
        """
        filepath = QFileDialog.getOpenFileName(self, 'Path to Results Translator Tool', self.settings.getDataDirectory())[0]
        if filepath:
            self.txtResultsTranslator.setText(filepath)

    @Slot(bool)
    def on_btnUpdateDRFList_clicked(self, checked):
        """
        Obtain the List of DRFs from WebID
        """
        url = self.txtWebAddress.text().strip('/')
        drfList = get_DRFList_from_webid(url)
        if drfList:
            currentDRF = self.cmbDRFs.currentText()
            # remove 'auto' options since RASE does not pass n42s w/ instrument specifications
            if 'auto' in drfList:
                drfList.remove('auto')
            self.settings.setWebIDDRFsList(drfList)
            self.cmbDRFs.clear()
            self.cmbDRFs.addItems(self.settings.getWebIDDRFsList())
            index = self.cmbDRFs.findText(currentDRF)
            self.cmbDRFs.setCurrentIndex(index) if index >=0 else self.cmbDRFs.setCurrentIndex(0)
        else:
            QMessageBox.warning(self, "Connection error",
                                "Error while connecting to Full Spectrum Web ID. Is the web address correct?")

    @Slot()
    def accept(self):
        name = self.txtName.text()
        if not name:
            QMessageBox.critical(self, 'Insufficient Information', 'Must specify a replay tool name')
            return
        session = Session()
        repl = session.query(Replay).filter_by(name=name).first()
        if repl and not (self.replay and self.replay.name == name):
            QMessageBox.warning(self, 'Bad Replay Name', 'Replay with this name exists. Specify Different Replay Name')
            return
        if not self.replay:
            self.replay = Replay(name=name)
            self.parent.new_replay = self.replay
            session.add(self.replay)
        self.replay.name = self.txtName.text()
        self.replay.type = ReplayTypes.gadras_web if self.radioWeb.isChecked() else ReplayTypes.standalone
        self.replay.exe_path    = self.txtCmdLine.text()
        self.replay.is_cmd_line = self.cbCmdLine.isChecked()
        self.replay.settings    = self.txtSettings.text().strip()
        self.replay.n42_template_path = self.txtTemplatePath.text()
        self.replay.input_filename_suffix = self.txtFilenameSuffix.text()
        self.replay.web_address = self.txtWebAddress.text()
        self.replay.drf_name = self.cmbDRFs.currentText()

        self.replay.translator_exe_path = self.txtResultsTranslator.text()
        self.replay.translator_is_cmd_line = self.cbCmdLine_3.isChecked()
        self.replay.translator_settings = self.txtSettings_3.text().strip()
        session.commit()
        return QDialog.accept(self)

