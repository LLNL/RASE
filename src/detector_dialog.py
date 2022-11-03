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
This module specifies the base spectra, influences, and other detector info
"""

from PySide6.QtCore import Qt, Slot, QRegularExpression
from PySide6.QtGui import QRegularExpressionValidator, QDoubleValidator
from PySide6.QtWidgets import QDialog, QTableWidgetItem, QFileDialog, QMessageBox, QItemDelegate, QLineEdit, QComboBox, \
    QHeaderView, QInputDialog

from decimal import Decimal
from .base_spectra_dialog import BaseSpectraDialog
from .rase_functions import importDistortionFile, secondary_type
from .replay_dialog import ReplayDialog
from .table_def import Session, Replay, ResultsTranslator, Detector, Influence, DetectorInfluence, BackgroundSpectrum, \
    BaseSpectrum
from .ui_generated import ui_add_detector_dialog
from .utils import profileit
from .manage_replays_dialog import ManageReplaysDialog
from .manage_influences_dialog import ManageInfluencesDialog
from .plotting import BaseSpectraViewerDialog
from src.rase_settings import RaseSettings

SECONDARY_TYPE_BACKGROUND, SECONDARY_TYPE_INTERNAL = 0, 1

class DetectorDialog(ui_add_detector_dialog.Ui_Dialog, QDialog):
    def __init__(self, parent, detectorName=None):
        QDialog.__init__(self, parent)
        self.parent = parent
        self.setupUi(self)
        self.txtDetector.setText(detectorName)
        self.detector = None
        self.settings = RaseSettings()
        self.newBaseSpectra = []
        self.newBackgroundSpectrum = None
        self.replay = None
        self.internal_secondary = 'None'
        self.resultsTranslator = None
        self.settingProgramatically = False
        self.detectorInfluences = []

        # background combo_box
        self.back_combo = {'base_spec': 0, 'scenario': 1, 'file': 2}

        self.session = session = Session()

        self.noSecondaryRadio.setChecked(True)
        self.secondaryIsBackgroundRadio.toggled.connect(self.setSecondarySpecEnable)
        self.combo_typesecondary.currentIndexChanged.connect(self.enableComboBase)
        self.includeSecondarySpectrumCheckBox.setEnabled(False)

        self.cmbReplay.addItem('')
        self.cmbReplay.addItems([replay.name for replay in session.query(Replay)])

        self.btnAddInfluences.clicked.connect(lambda: self.influenceManagement(False))
        self.btnModifyInfluences.clicked.connect(lambda: self.influenceManagement(True))
        self.btnDeleteInfluences.clicked.connect(self.deleteInfluencesFromDetector)
        self.manageReplays.clicked.connect(self.replayManagement)
        self.lstBaseSpectra.doubleClicked.connect(self.showSpectrum)

        # case that this is an edit of an existing detector
        if detectorName:
            self.setWindowTitle('Edit Detector')
            self.detector = detector = session.query(Detector).filter_by(name=detectorName).first()

            # populate details
            self.txtDetector           .setText(detector.name)
            self.txtDetector.setReadOnly(True)
            self.txtDetectorDescription.setText(detector.description)
            self.txtManufacturer       .setText(detector.manufacturer)
            self.txtInstrumentId       .setText(detector.instr_id)
            self.txtHardwareVersion    .setText(detector.hardware_version)
            self.txtClassCode          .setText(detector.class_code)

            # populate influences
            if self.detector.influences:
                self.listInfluences.addItems(sorted([influence.name for influence in self.detector.influences]))

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
            self.lstBaseSpectra.addItems(sorted([baseSpectrum.material_name for baseSpectrum in detector.base_spectra]))

            self.includeSecondarySpectrumCheckBox.setEnabled(True)
            if detector.includeSecondarySpectrum:
                # secondary spectrum checkboxes
                if detector.secondary_type == secondary_type['internal']:
                    self.secondaryIsCalibrationRadio.setEnabled(True)
                    self.secondaryIsCalibrationRadio.setChecked(True)
                    self.bckgndSpecFileDisplay.setText("Secondary Spectrum from: " + detector.bckg_spectra[0].material_name)
                else:
                    self.secondaryIsCalibrationRadio.setChecked(False)
                    self.secondaryIsCalibrationRadio.setEnabled(False)
                    self.bckgndSpecFileDisplay.clear()

                if detector.secondary_type != secondary_type['internal']:
                    self.secondaryIsBackgroundRadio.setChecked(True)
                    self.combo_typesecondary.setEnabled(True)
                    for key, val in secondary_type.items():
                        if val == detector.secondary_type:
                            self.combo_typesecondary.setCurrentIndex(self.back_combo[key])
                            break
                    self.setBackgroundIsoCombo(detector.secondary_type == secondary_type['base_spec'])

            else:
                self.secondaryIsCalibrationRadio.setChecked(False)
                self.secondaryIsCalibrationRadio.setEnabled(False)
                self.bckgndSpecFileDisplay.clear()

            if self.detector.secondary_type != secondary_type['file']:
                self.combo_typesecondary.removeItem(self.back_combo['file'])


    def replayManagement(self):
        """
        Opens Manage Replays Dialog
        """
        manageRepDialog = ManageReplaysDialog(self)
        manageRepDialog.exec_()

    def influenceManagement(self, modify_flag=False):
        """
        Opens the Influences Dialog
        """
        self._make_detector()
        manageInflDialog = ManageInfluencesDialog(self, modify_flag)
        manageInflDialog.exec_()

    def deleteInfluencesFromDetector(self):
        """
        Removes influences from influence list
        """
        for influence in self.listInfluences.selectedItems():
            self.listInfluences.takeItem(self.listInfluences.row(influence))

    def showSpectrum(self):
        """
        Plot loaded base spectra
        """
        spectra = self.newBaseSpectra
        if not self.newBaseSpectra:
            spectra = self.detector.base_spectra
        d = BaseSpectraViewerDialog(self, spectra, self.detector, self.lstBaseSpectra.currentItem().text())
        d.exec_()


    @Slot(bool)
    def on_btnRemoveBaseSpectra_clicked(self, checked):
        """
        Removes loaded Base Spectra
        """
        if self.lstBaseSpectra is not None:
            self.lstBaseSpectra.clear()
            self.combo_typesecondary.setCurrentIndex(0)
            self.setBackgroundIsoCombo(False)
            self.combo_basesecondary.clear()
        if self.detector is not None:
            detBaseRelationDelete = Session().query(BaseSpectrum).filter(BaseSpectrum.detector_name == self.detector.name)
            detBaseRelationDelete.delete()
            detBackRelationDelete = Session().query(BackgroundSpectrum).filter(BackgroundSpectrum.detector_name == self.detector.name)
            detBackRelationDelete.delete()
            if self.detector.base_spectra is not None:
                self.detector.base_spectra.clear()
            if self.detector.bckg_spectra is not None:
                self.detector.bckg_spectra.clear()
        self.includeSecondarySpectrumCheckBox.setEnabled(False)
        self.noSecondaryRadio.setChecked(True)
        self.secondaryIsCalibrationRadio.setEnabled(False)
        if self.combo_typesecondary.count() < 3:
            self.combo_typesecondary.addItem("Use secondary defined in base spectra files")

    @Slot(bool)
    def on_btnAddBaseSpectra_clicked(self, checked, dlg = None):
        """
        Loads base spectra
        :param dlg: optional BaseSpectraDialog input

        """
        dialog = dlg
        if dialog is None:
            dialog = BaseSpectraDialog(self.session)
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
            self.lstBaseSpectra.addItems(sorted([baseSpec.material.name for baseSpec in dialog.baseSpectra]))

            #initialize newBackgroundSpectrum
            self.newBackgroundSpectrum = dialog.backgroundSpectrum
            self.includeSecondarySpectrumCheckBox.setEnabled(True)
            self.noSecondaryRadio.setChecked(True)
            if self.newBackgroundSpectrum is not None:
                self.internal_secondary = dialog.backgroundSpectrum.material.name
                if dialog.backgroundSpectrumType == SECONDARY_TYPE_BACKGROUND:
                    self.secondaryIsBackgroundRadio.setChecked(True)
                    self.combo_typesecondary.setEnabled(True)
                    self.populateComboBase(sorted([baseSpec.material.name for baseSpec in dialog.baseSpectra]))
                    self.setDefaultSecondary(sorted([baseSpec.material.name for baseSpec in dialog.baseSpectra]))
                    self.setBackgroundIsoCombo(True)
                else:
                    self.secondaryIsCalibrationRadio.setEnabled(True)
                    self.secondaryIsCalibrationRadio.setChecked(True)

                    self.bckgndSpecFileDisplay.setText("Secondary spectrum from: " + self.internal_secondary)
            else:
                self.secondaryIsCalibrationRadio.setChecked(False)
                self.secondaryIsCalibrationRadio.setEnabled(False)
                self.bckgndSpecFileDisplay.setText("No secondary spectrum found")
            self._make_detector()

    # @Slot(bool)
    # def on_btnImportInfluences_clicked(self, checked):
    #     """
    #     Imports Influences
    #     """
    #     filepath = QFileDialog.getOpenFileName(self, 'Distortion File', self.settings.getDataDirectory())[0]
    #     if filepath:
    #         self.tblInfluences.clearContents()
    #         self.detectorInfluences = importDistortionFile(filepath)
    #         for row, detInf in enumerate(self.detectorInfluences):
    #             self.tblInfluences.setItem(row, 0, QTableWidgetItem(detInf[0]))
    #             self.tblInfluences.setItem(row, 1, QTableWidgetItem(str(detInf[1][0])))
    #             self.tblInfluences.setItem(row, 2, QTableWidgetItem(str(detInf[1][1])))
    #             self.tblInfluences.setItem(row, 3, QTableWidgetItem(str(detInf[1][2])))

    @Slot(bool)
    def on_btnNewReplay_clicked(self, checked):
        """
        Adds new replay
        """
        dialog = ReplayDialog(self)
        if dialog.exec_():
            # create new replay and change combo box index to it
            self.replay = dialog.replay
            self.cmbReplay.addItem(self.replay.name)
            self.settingProgramatically = True
            self.cmbReplay.setCurrentIndex(self.cmbReplay.count() - 1)
            self.settingProgramatically = False
            self.resultsTranslator = dialog.resultsTranslator

    @Slot(int)
    def on_cmbReplay_currentIndexChanged(self, replayIndex):
        """
        Listens for change in replay tool selection
        """
        if self.settingProgramatically:return
        replayName = self.cmbReplay.itemText(replayIndex)
        self.replay = self.session.query(Replay).filter_by(name = replayName).first()
        self.resultsTranslator = self.session.query(ResultsTranslator).filter_by(name = replayName).first()

    def setBackgroundIsoCombo(self, switch=False):
        self.label_basesecondary.setEnabled(switch)
        self.combo_basesecondary.setEnabled(switch)

    def setSecondarySpecEnable(self, checked=False):
        if checked:
            self.combo_typesecondary.setEnabled(True)
            self.setBackgroundIsoCombo(self.combo_typesecondary.currentIndex() == self.back_combo['base_spec'])
            self.enableComboBase(self.combo_typesecondary.currentIndex())
            self.bckgndSpecFileDisplay.clear()
        else:
            self.combo_typesecondary.setEnabled(False)
            self.setBackgroundIsoCombo(False)
            if self.detector and len(self.detector.bckg_spectra):
                self.bckgndSpecFileDisplay.setText("Secondary Spectrum from: " + self.detector.bckg_spectra[0].material_name)
            else:
                self.bckgndSpecFileDisplay.setText("Secondary Spectrum from: " + self.internal_secondary)

    def enableComboBase(self, comboindex):
        if comboindex == self.back_combo['base_spec']:
            self.setBackgroundIsoCombo(True)
            self.populateComboBase([self.lstBaseSpectra.item(i).text() for i in range(self.lstBaseSpectra.count())])
            if self.detector and len(self.detector.bckg_spectra) and self.detector.bckg_spectra[0].material_name != 'Mix':
                self.combo_basesecondary.setCurrentText(self.detector.bckg_spectra[0].material_name)
            else:
                self.setDefaultSecondary([self.lstBaseSpectra.item(i).text() for i in range(self.lstBaseSpectra.count())])
        else:
            self.setBackgroundIsoCombo(False)
            self.combo_basesecondary.clear()

    def populateComboBase(self, isotopes):
        self.combo_basesecondary.addItems(isotopes)

    def setDefaultSecondary(self, isotopes):
        for bgndisotope in ['Bgnd', 'Bgnd-Lab', 'NORM', 'NORM-Lab']:
            if bgndisotope in isotopes:
                self.combo_basesecondary.setCurrentIndex(self.combo_basesecondary.findText(bgndisotope))
                break

    def _make_detector(self):
        """ Create detector object with basic entries """
        if not self.detector:
            # create new detector
            name = self.txtDetector.text()
            while not name or self.session.query(Detector).filter_by(name=name).first() is not None:
                name, ok = QInputDialog.getText(self, "Detector Name", "Detector Unique Name")
                # print(name, self.session.query(Detector).filter_by(name=name).first())

            self.txtDetector.setText(name)
            self.txtDetector.setReadOnly(True)
            self._set_detector_name(self.session, name)

        self._set_ch_counts_ecal(self.txtChannelCount.text(), self.txtEcal0.text(), self.txtEcal1.text(),
                                 self.txtEcal2.text(), self.txtEcal3.text())
        self._set_detector_params(self.txtManufacturer.text(), self.txtInstrumentId.text(), self.txtClassCode.text(),
                                  self.txtHardwareVersion.text(), self.replay, self.resultsTranslator,
                                  self.txtDetectorDescription.toPlainText())

    # set detector name and add to session
    def _set_detector_name(self, session, name):
        self.detector = Detector(name=name)
        session.add(self.detector)

    # set channel and calibration data
    def _set_ch_counts_ecal(self, chanCnt, txtEcal0, txtEcal1, txtEcal2, txtEcal3):
        self.detector.chan_count   = float(chanCnt) if chanCnt else None
        self.detector.ecal0        = float(txtEcal0) if txtEcal0 else '0'
        self.detector.ecal1        = float(txtEcal1) if txtEcal1 else '0'
        self.detector.ecal2        = float(txtEcal2) if txtEcal2 else '0'
        self.detector.ecal3        = float(txtEcal3) if txtEcal3 else '0'

    # set detector description items
    def _set_detector_params(self, txtManufacturer, txtInstrumentId, txtClassCode, txtHardwareVersion, replay,
                             resultsTranslator, txtDetectorDescription):
        self.detector.manufacturer = txtManufacturer
        self.detector.instr_id = txtInstrumentId
        self.detector.class_code = txtClassCode
        self.detector.hardware_version = txtHardwareVersion
        self.detector.replay = replay
        self.detector.resultsTranslator = resultsTranslator
        self.detector.description = txtDetectorDescription

    # @profileit
    @Slot()
    def accept(self):
        # set basic detector parameter
        self._make_detector()

        # set influences
        self.detector.influences.clear()
        if self.listInfluences.count() > 0:
            for infl_name in [self.listInfluences.item(index).text() for index in range(self.listInfluences.count())]:
                influence = self.session.query(Influence).filter_by(name=infl_name).first()
                self.detector.influences.append(influence)

        # add base spectra
        for baseSpectra in self.newBaseSpectra:
            self.detector.base_spectra.append(baseSpectra)

        self.detector.includeSecondarySpectrum = not self.noSecondaryRadio.isChecked()

        if self.detector.includeSecondarySpectrum:

            # if there has been a modification to the secondary spectrum of choice
            if self.newBackgroundSpectrum is None:
                if len(self.detector.bckg_spectra):
                    self.newBackgroundSpectrum = self.detector.bckg_spectra[0]
                else:
                    self.newBackgroundSpectrum = BackgroundSpectrum()

            if self.secondaryIsBackgroundRadio.isChecked():
                if self.combo_typesecondary.currentIndex() == self.back_combo['base_spec']:
                    for spec in self.detector.base_spectra:
                        if spec.material.name == self.combo_basesecondary.currentText():
                            self.newBackgroundSpectrum.counts = spec.counts
                            self.newBackgroundSpectrum.filename = spec.filename
                            self.newBackgroundSpectrum.id = spec.id
                            self.newBackgroundSpectrum.livetime = spec.livetime
                            self.newBackgroundSpectrum.material = spec.material
                            self.newBackgroundSpectrum.material_name = spec.material_name
                            self.newBackgroundSpectrum.realtime = spec.realtime
                            self.newBackgroundSpectrum.metadata = spec.metadata
                            break
                elif self.combo_typesecondary.currentIndex() == self.back_combo['scenario']:
                    self.newBackgroundSpectrum.counts = '0'  #TODO: Jason check if this bug fix is correctly implemented
                    self.newBackgroundSpectrum.material_name = 'Mix'

            self.detector.bckg_spectra.clear()
            self.detector.bckg_spectra.append(self.newBackgroundSpectrum)


        # set the boolean for including secondary spectrum in generated spectra
        # and secondary spectrum type
        if self.secondaryIsCalibrationRadio.isChecked():
            self.detector.secondary_type = secondary_type['internal']
        elif self.secondaryIsBackgroundRadio.isChecked():
            for key, val in self.back_combo.items():
                if val == self.combo_typesecondary.currentIndex():
                    self.detector.secondary_type = secondary_type[key]
                    break

        self.session.commit()
        return QDialog.accept(self)

    @Slot()
    def reject(self):
        self.session.rollback()
        return QDialog.reject(self)

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
            comboBox.setValidator(QRegularExpressionValidator(QRegularExpression('[a-zA-Z0-9_.-]+')))
            session = Session()
            for influence in session.query(Influence):
                if influence.name not in takenInfluences:
                    comboBox.addItem(influence.name)
            return comboBox

