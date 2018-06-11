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
This module specifies the base spectra, influences, and other detector info
"""

from PyQt5.QtCore import Qt, pyqtSlot, QRegExp
from PyQt5.QtGui import QRegExpValidator, QDoubleValidator
from PyQt5.QtWidgets import QDialog, QTableWidgetItem, QFileDialog, QMessageBox, QItemDelegate, QLineEdit, QComboBox, QHeaderView

from decimal import Decimal
from .base_spectra_dialog import BaseSpectraDialog
from .rase_functions import importDistortionFile
from .replay_dialog import ReplayDialog
from .table_def import Session, Replay, ResultsTranslator, Detector, Influence, DetectorInfluence, BackgroundSpectrum
from .ui_generated import ui_add_detector_dialog
from .utils import profileit
from .manage_replays_dialog import ManageReplaysDialog
from .plotting import SpectraViewerDialog


class DetectorDialog(ui_add_detector_dialog.Ui_Dialog, QDialog):
    def __init__(self, parent, settings, detectorName=None, testDetectorName=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.txtDetector.setText(testDetectorName)
        self.detector = None
        self.settings = settings
        self.newBaseSpectra = []
        self.newBackgroundSpectra = []
        self.replay = None
        self.resultsTranslator = None
        self.settingProgramatically = False
        self.detectorInfluences = []
        self.session = session = Session()

        # set influence table properties
        self.tblInfluences.setItemDelegate(self.FloatLineDelegate(self))
        self.tblInfluences.setItemDelegateForColumn(0, self.InfluenceDelegate(self.tblInfluences))
        self.tblInfluences.setRowCount(10)
        self.tblInfluences.verticalHeader().hide()
        self.tblInfluences.setColumnWidth(0, 150)
        self.tblInfluences.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)


        for row in range(self.tblInfluences.rowCount()):
            for col in range(self.tblInfluences.columnCount()):
                self.tblInfluences.setItem(row, col, QTableWidgetItem())
            self.tblInfluences.setRowHeight(row, 22)
        self.tblInfluences.cellChanged.connect(self.onInfluenceCellChanged)

        self.cmbReplay.addItem('')
        self.cmbReplay.addItems([replay.name for replay in session.query(Replay)])

        self.includeSecondarySpectrumCheckBox.setChecked(False)
        self.includeSecondarySpectrumCheckBox.setEnabled(False)

        self.manageReplays.clicked.connect(self.replayManagement)
        self.lstBaseSpectra.doubleClicked.connect(self.showSpectrum)

        # case that this is an edit of an existing detector
        if detectorName:
            self.setWindowTitle('Edit Detector')
            self.detector = detector = session.query(Detector).filter_by(name = detectorName).first()

            # populate details
            self.txtDetector           .setText(detector.name)
            self.txtDetector.setReadOnly(True)
            self.txtDetectorDescription.setText(detector.description)
            self.txtManufacturer       .setText(detector.manufacturer)
            self.txtInstrumentId       .setText(detector.instr_id)
            self.txtHardwareVersion    .setText(detector.hardware_version)
            self.txtClassCode          .setText(detector.class_code)

            # populate influences
            for row, detInfluence in enumerate(detector.influences):
                for (col, text) in [(0, detInfluence.influence_name),
                                    (1, str(detInfluence.infl_0)),
                                    (2, str(detInfluence.infl_1)),
                                    (3, str(detInfluence.infl_2))]:
                    item = self.tblInfluences.item(row, col)
                    item.setText(text)
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)

            # populate ecal
            self.txtEcal0.setText('%E' % Decimal(detector.ecal0) if detector.ecal0 else '0')
            self.txtEcal1.setText('%E' % Decimal(detector.ecal1) if detector.ecal1 else '0')
            self.txtEcal2.setText('%E' % Decimal(detector.ecal2) if detector.ecal2 else '0')
            self.txtEcal3.setText('%E' % Decimal(detector.ecal3) if detector.ecal3 else '0')
            self.txtChannelCount.setText(str(detector.chan_count or ''))

            # Replay
            if detector.replay:
                self.cmbReplay.setCurrentText(detector.replay.name)

            # populate materials
            self.lstBaseSpectra.addItems([baseSpectrum.material_name for baseSpectrum in detector.base_spectra])

            # secondary spectrum checkboxes
            self.bckgndSpecFileDisplay.setText("No secondary spectrum found")
            secondary_spectrum = (session.query(BackgroundSpectrum).filter_by(detector_name=detector.name)).first()
            if secondary_spectrum:
                self.includeSecondarySpectrumCheckBox.setEnabled(True)
                self.bckgndSpecFileDisplay.setText("Secondary Spectrum from: " + detector.bckg_spectra[0].material.name)
            self.includeSecondarySpectrumCheckBox.setChecked(detector.includeSecondarySpectrum)
            if detector.secondary_type == 1:
                self.secondaryIsBackgroundRadio.setChecked(True)
            elif detector.secondary_type == 2:
                self.secondaryIsCalibrationRadio.setChecked(True)

    def replayManagement(self):
        """
        Opens Manage Replays Dialog
        """
        manageRepDialog = ManageReplaysDialog(self)
        manageRepDialog.exec_()

    def showSpectrum(self):
        """
        Lists loaded base spectra
        """
        spectra = self.newBaseSpectra
        if not self.newBaseSpectra:
            spectra = self.detector.base_spectra
        d = SpectraViewerDialog(self, self.session, spectra, self.lstBaseSpectra.currentItem().text())
        d.exec_()


    @pyqtSlot(bool)
    def on_btnRemoveBaseSpectra_clicked(self, checked):
        """
        Removes loaded Base Spectra
        """
        if self.lstBaseSpectra is not None:
            self.lstBaseSpectra.clear()
        if self.detector is not None:
            if self.detector.base_spectra is not None:
                self.detector.base_spectra.clear()
            if self.detector.bckg_spectra is not None:
                self.detector.bckg_spectra.clear()

    @pyqtSlot(bool)
    def on_btnAddBaseSpectra_clicked(self, checked, dlg = None):
        """
        Loads base spectra
        :param dlg: optional BaseSpectraDialog input

        """
        dialog = dlg
        if dialog == None:
            dialog = BaseSpectraDialog(self.session, self.settings)
            dialog.exec_()
        if dialog.baseSpectra:
                # set ecal and counts
            for i in range(min(len(dialog.ecal), 4)):
                txtEcal = getattr(self, 'txtEcal' + str(i))
                txtEcal.setText(str(dialog.ecal[i]))

            # set chan count
            self.txtChannelCount.setText(str(dialog.counts.count(',')+1))

            # set base spectra list
            self.newBaseSpectra = dialog.baseSpectra
            for baseSpectrum in dialog.baseSpectra:
                self.lstBaseSpectra.addItem(baseSpectrum.material.name)

            #initialize newBackgroundSpectra
            self.newBackgroundSpectra = dialog.backgroundSpectra
            if self.newBackgroundSpectra[0] is not None and dialog.backgroundSpectraType:
                self.includeSecondarySpectrumCheckBox.setEnabled(True)
                self.includeSecondarySpectrumCheckBox.setChecked(True)
                self.secondaryIsBackgroundRadio.setChecked(dialog.backgroundSpectraType == 1)
                self.secondaryIsCalibrationRadio.setChecked(dialog.backgroundSpectraType == 2)
                self.bckgndSpecFileDisplay.setText("Secondary spectrum from: "+dialog.backgroundSpectra[0].material.name)
            else:
                self.includeSecondarySpectrumCheckBox.setChecked(False)
                self.bckgndSpecFileDisplay.setText("No secondary spectrum found")

    @pyqtSlot(bool)
    def on_btnImportInfluences_clicked(self, checked):
        """
        Impoerts Influences
        """
        filepath = QFileDialog.getOpenFileName(self, 'Distortion File', self.settings.getDataDirectory())[0]
        if filepath:
            self.tblInfluences.clearContents()
            self.detectorInfluences = importDistortionFile(filepath)
            for row, detInf in enumerate(self.detectorInfluences):
                self.tblInfluences.setItem(row, 0, QTableWidgetItem(detInf[0]))
                self.tblInfluences.setItem(row, 1, QTableWidgetItem(str(detInf[1][0])))
                self.tblInfluences.setItem(row, 2, QTableWidgetItem(str(detInf[1][1])))
                self.tblInfluences.setItem(row, 3, QTableWidgetItem(str(detInf[1][2])))

    @pyqtSlot(bool)
    def on_btnNewReplay_clicked(self, checked):
        """
        Adds new replay
        """
        dialog = ReplayDialog(self, self.settings)
        if dialog.exec_():
            # create new replay and change combo box index to it
            self.replay = dialog.replay
            self.cmbReplay.addItem(self.replay.name)
            self.settingProgramatically = True
            self.cmbReplay.setCurrentIndex(self.cmbReplay.count() - 1)
            self.settingProgramatically = False
            self.resultsTranslator = dialog.resultsTranslator

    @pyqtSlot(str)
    def on_cmbReplay_currentIndexChanged(self, replayName):
        """
        Listens for change in replay tool selection
        """
        if self.settingProgramatically:return
        self.replay = self.session.query(Replay).filter_by(name = replayName).first()
        self.resultsTranslator = self.session.query(ResultsTranslator).filter_by(name = replayName).first()

    # @pyqtSlot(int, int)
    def onInfluenceCellChanged(self, row, col):
        """
        listens for change in influence values
        """
        influenceName = self.tblInfluences.item(row, col).text().lower()
        for influence in self.session.query(Influence):
            if influence.name.lower() == influenceName:
                self.tblInfluences.item(row, col).setText(influence.name)
                break

    # @profileit
    @pyqtSlot()
    def accept(self):
        if not self.detector:
            # create new detector
            name =  self.txtDetector.text()
            if not name:
                QMessageBox.warning(self, 'No Detector Name Specified', 'Must Specify Detector Name')
                return
            if self.session.query(Detector).filter_by(name = name).first():
                QMessageBox.warning(self, 'Detector Already Exists', 'Detector Name Already Exists.  Please Change Name.')
                return
            self.detector = Detector(name=name)
            self.session.add(self.detector)

        # set ecal and chan count
        chanCnt  = self.txtChannelCount.text()
        txtEcal0 = self.txtEcal0.text()
        txtEcal1 = self.txtEcal1.text()
        txtEcal2 = self.txtEcal2.text()
        txtEcal3 = self.txtEcal3.text()

        self.detector.chan_count   = float(chanCnt) if chanCnt else None
        self.detector.ecal0        = float(txtEcal0) if txtEcal0 else '0'
        self.detector.ecal1        = float(txtEcal1) if txtEcal1 else '0'
        self.detector.ecal2        = float(txtEcal2) if txtEcal2 else '0'
        self.detector.ecal3        = float(txtEcal3) if txtEcal3 else '0'

        # set detector description items
        self.detector.manufacturer = self.txtManufacturer.text()
        self.detector.instr_id     = self.txtInstrumentId.text()
        self.detector.class_code   = self.txtClassCode.text()
        self.detector.hardware_version = self.txtHardwareVersion.text()
        self.detector.replay       = self.replay
        self.detector.resultsTranslator       = self.resultsTranslator
        self.detector.description  = self.txtDetectorDescription.toPlainText()

        # set influences
        for row in range(self.tblInfluences.rowCount()):
            # check of valid row of values
            try:
                inflName = self.tblInfluences.item(row, 0).text()
                infl_0   = float(self.tblInfluences.item(row, 1).text())
                infl_1   = float(self.tblInfluences.item(row, 2).text())
                infl_2   = float(self.tblInfluences.item(row, 3).text())
            except (ValueError, AttributeError): continue

            # check if database already has this detector influence
            for detInfluence in self.detector.influences:
                if self.tblInfluences.item(row, 0).text() == detInfluence.influence_name:
                    break
            else: # create a new one
                # see if Influence in database or create new one
                influence = self.session.query(Influence).filter_by(name=inflName).first()
                if not influence:
                    influence = Influence(name=inflName)
                detInfluence = DetectorInfluence(influence=influence)
                self.detector.influences.append(detInfluence)

            detInfluence.infl_0 = infl_0
            detInfluence.infl_1 = infl_1
            detInfluence.infl_2 = infl_2

        # add base spectra
        for baseSpectra in self.newBaseSpectra:
            self.detector.base_spectra.append(baseSpectra)

        # add background spectra
        for backgroundSpectra in self.newBackgroundSpectra:
            if backgroundSpectra is not None:
                self.detector.bckg_spectra.append(backgroundSpectra)

        # set the boolean for including secondary spectrum in generated spectra
        # and secondary spectrum type
        self.detector.includeSecondarySpectrum = self.includeSecondarySpectrumCheckBox.isChecked()
        if self.secondaryIsBackgroundRadio.isChecked():
            self.detector.secondary_type = 1
        elif self.secondaryIsCalibrationRadio.isChecked():
            self.detector.secondary_type = 2

        self.session.commit()
        return QDialog.accept(self)

    class FloatLineDelegate(QItemDelegate):
        def __init__(self, parent):
            QItemDelegate.__init__(self, parent)

        def createEditor(self, parent, option, index):
            lineEdit = QLineEdit(parent)
            lineEdit.setValidator(QDoubleValidator())
            return lineEdit


    class InfluenceDelegate(QItemDelegate):
        def __init__(self, tblInfluence, parent=None):
            QItemDelegate.__init__(self, parent)
            self.tblInfluences = tblInfluence

        def createEditor(self, parent, option, index):
            takenInfluences = []
            for row in range(self.tblInfluences.rowCount()):
                item = self.tblInfluences.item(row, 0)
                if item:
                    takenInfluences.append(item.text())

            comboBox = QComboBox(parent)
            comboBox.setEditable(True)
            comboBox.setValidator(QRegExpValidator(QRegExp('[A-Za-z]+')))
            session = Session()
            for influence in session.query(Influence):
                if influence.name not in takenInfluences:
                    comboBox.addItem(influence.name)
            return comboBox

