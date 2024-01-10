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
from .table_def import Session, Replay, Detector, Influence, DetectorInfluence, \
    BaseSpectrum, DetectorSchema, Material, SecondarySpectrum, BackgroundSpectrum, Spectrum, generate_random_string
from sqlalchemy import inspect
from .ui_generated import ui_add_detector_dialog
from .utils import profileit
from .manage_replays_dialog import ManageReplaysDialog
from .manage_influences_dialog import ManageInfluencesDialog
from .plotting import BaseSpectraViewerDialog
from src.rase_settings import RaseSettings
import yaml


class DetectorDialog(ui_add_detector_dialog.Ui_Dialog, QDialog):
    def __init__(self, parent, detectorName=None):
        QDialog.__init__(self, parent)
        self.parent = parent
        self.setupUi(self)
        self.txtDetector.setText(detectorName)
        self.detector = None
        self.settings = RaseSettings()
        self.newBaseSpectra = []
        self.secondary_spectra = []
        self.newBackgroundSpectrum = None
        self.replay = None
        self.internal_secondary = 'None'
        self.settingProgramatically = False
        self.detectorInfluences = []

        self.session = session = Session()

        self.noSecondaryRadio.setChecked(True)
        self.checkAddIntrinsic.setEnabled(False)
        self.checkAddIntrinsic.toggled.connect(self.addIntrinsicToggle)
        self.secondaryIsBackgroundRadio.toggled.connect(self.setSecondarySpecEnable)
        self.combo_typesecondary.setCurrentIndex(1)
        self.combo_typesecondary.currentIndexChanged.connect(self.enableComboBase)
        self.includeSecondarySpectrumCheckBox.setEnabled(False)

        self.cmbReplay.addItem('')
        self.cmbReplay.addItems([replay.name for replay in session.query(Replay)])

        self.btnAddInfluences.clicked.connect(lambda: self.influenceManagement(False))
        self.btnModifyInfluences.clicked.connect(lambda: self.influenceManagement(True))
        self.btnDeleteInfluences.clicked.connect(self.deleteInfluencesFromDetector)
        self.manageReplays.clicked.connect(self.replayManagement)
        self.lstBaseSpectra.doubleClicked.connect(self.showSpectrum)
        self.label_intrinsicWarning.setVisible(False)

        # case that this is an edit of an existing detector
        if detectorName:
            self.btnExportDetector.setEnabled(True)
            self.setWindowTitle('Edit Detector')
            self.detector = session.query(Detector).filter_by(name=detectorName).first()
            self.populate_gui_from_detector(self.detector)
            self.changeIntrinsicText(self.detector.base_spectra)

    def populate_gui_from_detector(self, detector):
        # populate details
        self.txtDetector.setText(detector.name)
        # self.txtDetector.setReadOnly(True)
        self.txtDetectorDescription.setText(detector.description)
        self.txtManufacturer.setText(detector.manufacturer)
        self.txtInstrumentId.setText(detector.instr_id)
        self.txtHardwareVersion.setText(detector.hardware_version)
        self.txtClassCode.setText(detector.class_code)

        # populate influences
        self.listInfluences.clear()
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
            if detector.replay.name not in [self.cmbReplay.itemText(i) for i in range(self.cmbReplay.count())]:
                self.cmbReplay.addItem(detector.replay.name)
            self.cmbReplay.setCurrentText(detector.replay.name)

        # populate materials
        self.lstBaseSpectra.clear()
        self.lstBaseSpectra.addItems(sorted([baseSpectrum.material.name for baseSpectrum in detector.base_spectra]))

        if detector.base_spectra:
            self.includeSecondarySpectrumCheckBox.setEnabled(True)
        if detector.secondary_spectra:
            self.secondary_spectra = detector.secondary_spectra.copy()
            self.checkAddIntrinsic.setEnabled(True)
            if detector.sample_intrinsic:
                self.checkAddIntrinsic.setChecked(True)  # combo_selectIntrinsic populated here
                self.combo_selectIntrinsic.setCurrentIndex(
                    self.combo_selectIntrinsic.findText(self.detector.intrinsic_classcode))
        else:
            self.combo_typesecondary.removeItem(secondary_type['file'])
        if detector.includeSecondarySpectrum:
            if detector.secondary_type is None:  # this can only happen if there is an intrinsic
                self.noSecondaryRadio.setChecked(True)
            else:
                self.secondaryIsBackgroundRadio.setChecked(True)
                self.combo_typesecondary.setEnabled(True)
                for key, val in secondary_type.items():
                    if val == detector.secondary_type:
                        self.combo_typesecondary.setCurrentIndex(secondary_type[key])
                        break


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

    def addIntrinsicToggle(self, checked=False):
        if checked:
            self.noSecondaryRadio.setText('no secondary spectrum (other than intrinsic)')
            if self.secondary_spectra:
                items = [secSpec.classcode for secSpec in self.secondary_spectra]
            else:
                items = ['UnspecifiedSecondary']
            self.combo_selectIntrinsic.addItems(items)
        else:
            self.noSecondaryRadio.setText('no secondary spectrum')
            self.combo_selectIntrinsic.clear()
        self.label_intrinsicClassCode.setEnabled(checked)
        self.combo_selectIntrinsic.setEnabled(checked)

    def changeIntrinsicText(self, base_spectra=None):
        if base_spectra is None:
            self.label_intrinsicWarning.setVisible(False)
            return
        for spec in base_spectra:
            if spec.material.include_intrinsic:
                self.label_intrinsicWarning.setVisible(True)
                return
        self.label_intrinsicWarning.setVisible(False)


    @Slot(bool)
    def on_btnRemoveBaseSpectra_clicked(self, checked):
        """
        Removes loaded Base Spectra
        """
        if self.lstBaseSpectra is not None:
            self.lstBaseSpectra.clear()
            self.combo_typesecondary.setCurrentIndex(1)
            self.setBackgroundIsoCombo(False)
            self.combo_basesecondary.clear()
        if self.detector is not None:
            for spec in Session().query(Spectrum).filter(Spectrum.detector_name ==self.detector.name).all():
                self.session.delete(spec)
            if self.detector.base_spectra is not None:
                self.detector.base_spectra.clear()
            if self.detector.bckg_spectra is not None:
                self.detector.bckg_spectra.clear()
            if self.detector.secondary_spectra is not None:
                self.detector.secondary_spectra.clear()
        self.secondary_spectra = []
        self.newBackgroundSpectrum = None
        self.includeSecondarySpectrumCheckBox.setEnabled(False)
        self.noSecondaryRadio.setChecked(True)
        if self.combo_typesecondary.count() < 3:
            self.combo_typesecondary.addItem("Use secondary defined in base spectra files")
        self.changeIntrinsicText()
        self.checkAddIntrinsic.setChecked(False)
        self.checkAddIntrinsic.setEnabled(False)


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
            self.secondary_spectra = dialog.secondary_spectra
            self.lstBaseSpectra.addItems(sorted([baseSpec.material.name for baseSpec in dialog.baseSpectra]))

            #initialize newBackgroundSpectrum
            self.newBackgroundSpectrum = dialog.backgroundSpectrum  #auto-grabs the first secondary
            self.includeSecondarySpectrumCheckBox.setEnabled(True)  #enable regardless of if
                                                                    # there is a secondary or not
            if self.secondary_spectra or self.newBackgroundSpectrum:
                self.checkAddIntrinsic.setEnabled(True)
            else:
                self.combo_typesecondary.removeItem(secondary_type['file'])
            # if there are no officially designated secondaries, set the default secondary to the
            # secondary_spectra object for long-term preservation
            if self.newBackgroundSpectrum and not self.secondary_spectra:
                self.secondary_spectra.append(SecondarySpectrum(
                                            filename=self.newBackgroundSpectrum.filename,
                                            baseCounts=self.newBackgroundSpectrum.baseCounts,
                                            counts=self.newBackgroundSpectrum.counts,
                                            realtime=self.newBackgroundSpectrum.realtime,
                                            livetime=self.newBackgroundSpectrum.livetime,
                                            ecal=self.newBackgroundSpectrum.ecal,
                                            material=self.newBackgroundSpectrum.material,
                                            classcode='UnspecifiedSecondary',
                                            spectrum_type=self.newBackgroundSpectrum.spectrum_type))
            if self.newBackgroundSpectrum is None:
                self.noSecondaryRadio.setChecked(True)
            else:
                self.internal_secondary = dialog.backgroundSpectrum.material.name  # cosmetic

            self.noSecondaryRadio.setChecked(True)
            if self.newBackgroundSpectrum is not None:
                self.internal_secondary = dialog.backgroundSpectrum.material.name
                self.secondaryIsBackgroundRadio.setChecked(True)
                self.combo_typesecondary.setEnabled(True)
                self.setDefaultSecondary(sorted([baseSpec.material.name for baseSpec in dialog.baseSpectra]))
            self._make_detector()
            self.changeIntrinsicText(self.newBaseSpectra)

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
    def on_btnNewReplay_clicked(self, checked, dialog=None):
        """
        Adds new replay
        """
        if dialog is None:
            dialog = ReplayDialog(self)
            dialog.exec_()
        if dialog.replay:
            # create new replay and change combo box index to it
            self.replay = dialog.replay
            self.cmbReplay.addItem(self.replay.name)
            self.settingProgramatically = True
            self.cmbReplay.setCurrentIndex(self.cmbReplay.count() - 1)
            self.settingProgramatically = False


    @Slot(int)
    def on_cmbReplay_currentIndexChanged(self, replayIndex):
        """
        Listens for change in replay tool selection
        """
        if self.settingProgramatically:return
        replayName = self.cmbReplay.itemText(replayIndex)
        self.replay = self.session.query(Replay).filter_by(name = replayName).first()


    def setBackgroundIsoCombo(self, switch=False):
        self.label_basesecondary.setEnabled(switch)
        self.combo_basesecondary.setEnabled(switch)

    def setSecondarySpecEnable(self, checked=False):
        self.combo_typesecondary.setEnabled(checked)
        self.label_secondarydwell.setEnabled(checked)
        self.spinBox_secondarydwell.setEnabled(checked)
        self.label_resample.setEnabled(checked)
        self.cb_resample.setEnabled(checked)
        if checked:
            self.setBackgroundIsoCombo(self.combo_typesecondary.currentIndex() == secondary_type['base_spec'])
            self.enableComboBase(self.combo_typesecondary.currentIndex())
            if (self.detector is not None):
                self.cb_resample.setChecked(self.detector.bckg_spectra_resample)
                dwell_time = 0 if self.detector.bckg_spectra_dwell is None else self.detector.bckg_spectra_dwell
                self.spinBox_secondarydwell.setValue(dwell_time)
        else:
            self.setBackgroundIsoCombo(False)

    def enableComboBase(self, comboindex):
        self.combo_basesecondary.clear()
        if comboindex == secondary_type['base_spec']:
            self.setBackgroundIsoCombo(True)
            self.populateComboBase([self.lstBaseSpectra.item(i).text() for i in range(self.lstBaseSpectra.count())])
            if self.detector and len(self.detector.bckg_spectra):
                self.combo_basesecondary.setCurrentText(self.detector.bckg_spectra[0].material_name)
            else:
                self.setDefaultSecondary([self.lstBaseSpectra.item(i).text() for i in range(self.lstBaseSpectra.count())])
        elif comboindex == secondary_type['file']:
            self.setBackgroundIsoCombo(True)
            # self.setBackgroundIsoCombo(len(self.secondary_spectra) > 1)
            self.populateComboBase([s.classcode for s in self.secondary_spectra])
            if self.detector and self.detector.secondary_classcode:
                self.combo_basesecondary.setCurrentIndex(self.combo_basesecondary.findText(self.detector.secondary_classcode))
                if self.combo_basesecondary.currentIndex() == -1:
                    self.combo_basesecondary.setCurrentIndex(0)
        else:
            self.setBackgroundIsoCombo(False)

    def populateComboBase(self, isotopes):
        self.combo_basesecondary.addItems(isotopes)

    def setDefaultSecondary(self, isotopes):
        for bgndisotope in ['Bgnd', 'Bgnd-Lab', 'NORM', 'NORM-Lab']:
            if bgndisotope in isotopes:
                self.combo_basesecondary.setCurrentIndex(self.combo_basesecondary.findText(bgndisotope))
                break

    def _make_detector(self):
        """ Create detector object with basic entries """
        name = self.txtDetector.text()
        while not name or self.session.query(Detector).filter_by(name=name).first() is not None:
            if self.detector and self.detector.name == name: break
            name, ok = QInputDialog.getText(self, "Detector Name",
                                            "Detector name already exists. \nPlease enter a different name:")

        if not self.detector:
            # create new detector
            self.txtDetector.setText(name)
            # self.txtDetector.setReadOnly(True)
            self._set_detector_name(self.session, name)

        self.detector.name = name
        self._set_ch_counts_ecal(self.txtChannelCount.text(), self.txtEcal0.text(), self.txtEcal1.text(),
                                 self.txtEcal2.text(), self.txtEcal3.text())
        self._set_detector_params(self.txtManufacturer.text(), self.txtInstrumentId.text(), self.txtClassCode.text(),
                                  self.txtHardwareVersion.text(), self.replay,
                                  self.txtDetectorDescription.toPlainText(), self.spinBox_secondarydwell.value(),
                                  self.cb_resample.isChecked())


    def _set_detector_name(self, session, name):
        """Set detector name and add to session"""
        self.detector = Detector(name=name)
        session.add(self.detector)


    def _set_ch_counts_ecal(self, chanCnt, txtEcal0, txtEcal1, txtEcal2, txtEcal3):
        """set channel and calibration data"""
        self.detector.chan_count   = float(chanCnt) if chanCnt else None
        self.detector.ecal0        = float(txtEcal0) if txtEcal0 else '0'
        self.detector.ecal1        = float(txtEcal1) if txtEcal1 else '0'
        self.detector.ecal2        = float(txtEcal2) if txtEcal2 else '0'
        self.detector.ecal3        = float(txtEcal3) if txtEcal3 else '0'


    def _set_detector_params(self, txtManufacturer, txtInstrumentId, txtClassCode, txtHardwareVersion, replay,
                             txtDetectorDescription, bkg_dwell=0, bkg_resample=True):
        """set detector description items"""
        self.detector.manufacturer = txtManufacturer
        self.detector.instr_id = txtInstrumentId
        self.detector.class_code = txtClassCode
        self.detector.hardware_version = txtHardwareVersion
        self.detector.replay = replay
        self.detector.description = txtDetectorDescription
        self.detector.bckg_spectra_dwell = bkg_dwell
        self.detector.bckg_spectra_resample = bkg_resample


    def _map_secondary_to_bgnd(self, spec=None, classcode=''):
        """
        Utility function for table class conversion
        (Note for future development: is BackgroundSpectrum strictly necessary,
        or can we get away with just using SecondarySpectrum?)
        """
        if spec is None:
            return
        return BackgroundSpectrum(filename=spec.filename, baseCounts=spec.baseCounts,
                                  counts=spec.counts, realtime=spec.realtime,
                                  livetime=spec.livetime, ecal=spec.ecal,
                                  material_name=spec.material_name, material=spec.material,
                                  classcode=classcode)


    def stash_detector(self):
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
        for secondarySpectrum in self.secondary_spectra:
            if secondarySpectrum not in self.detector.secondary_spectra:
                self.detector.secondary_spectra.append(secondarySpectrum)

        self.detector.includeSecondarySpectrum = not self.noSecondaryRadio.isChecked() or \
                                                 self.checkAddIntrinsic.isChecked()

        include_intrinsic_only = self.noSecondaryRadio.isChecked() and self.checkAddIntrinsic.isChecked()

        if self.detector.includeSecondarySpectrum:
            # if there has been a modification to the secondary spectrum of choice
            if self.newBackgroundSpectrum is None and len(self.detector.bckg_spectra):
                self.newBackgroundSpectrum = self.detector.bckg_spectra[0]
            if include_intrinsic_only:
                bgnd = [k for k in self.secondary_spectra if k.classcode ==
                        self.combo_selectIntrinsic.currentText()][0]
                self.newBackgroundSpectrum = self._map_secondary_to_bgnd(bgnd, classcode=bgnd.classcode)
            elif self.combo_typesecondary.currentIndex() == secondary_type['file']:
                bgnd = [k for k in self.secondary_spectra if k.classcode ==
                                              self.combo_basesecondary.currentText()][0]
                self.newBackgroundSpectrum = self._map_secondary_to_bgnd(bgnd, classcode=bgnd.classcode)
            elif self.combo_typesecondary.currentIndex() == secondary_type['base_spec']:
                for spec in self.detector.base_spectra:
                    if spec.material.name == self.combo_basesecondary.currentText():
                        if self.newBackgroundSpectrum is None:
                            self.newBackgroundSpectrum = BackgroundSpectrum()
                        self.newBackgroundSpectrum.filename = spec.filename
                        self.newBackgroundSpectrum.counts = spec.counts
                        self.newBackgroundSpectrum.realtime = spec.realtime
                        self.newBackgroundSpectrum.livetime = spec.livetime
                        self.newBackgroundSpectrum.ecal = spec.ecal
                        self.newBackgroundSpectrum.material = spec.material
                        self.newBackgroundSpectrum.metadata = spec.metadata
                        self.newBackgroundSpectrum.classcode = 'Background'
                        break
            elif self.combo_typesecondary.currentIndex() == secondary_type['scenario']:
                self.newBackgroundSpectrum = None

            self.detector.bckg_spectra.clear()
            if self.newBackgroundSpectrum:
                self.detector.bckg_spectra.append(self.newBackgroundSpectrum)
            self.detector.secondary_classcode = ''
            if include_intrinsic_only:
                self.detector.secondary_type = None
                self.detector.secondary_classcode = self.combo_selectIntrinsic.currentText()
            else:
                for key, val in secondary_type.items():
                    if val == self.combo_typesecondary.currentIndex():
                        self.detector.secondary_type = secondary_type[key]
                        if key == 'base_spec':
                            self.detector.secondary_classcode = self.detector.bckg_spectra[0].classcode
                        elif key == 'file':
                            self.detector.secondary_classcode = self.combo_basesecondary.currentText()
                        break

        for bg in self.session.query(BackgroundSpectrum).filter_by(detectors=None).all():
            self.session.delete(bg)  # delete any non-attached bckg spectra.
            ## May not be necessary long-term, but should be safe (for static RASE at least) to prevent detached spectra from sticking around forever and blocking unique ids in the DB.

        # set the boolean for including secondary spectrum in generated spectra
        self.detector.sample_intrinsic = self.checkAddIntrinsic.isChecked()
        if self.detector.sample_intrinsic:
            self.detector.intrinsic_classcode = self.combo_selectIntrinsic.currentText()


    @Slot()
    def accept(self):
        # set basic detector parameter
        self.stash_detector()
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


    @Slot()
    def on_btnExportDetector_clicked(self, savefilepath=None):
        self.stash_detector()
        dschema = DetectorSchema()
        exportstring = dschema.dump(self.detector)
        if savefilepath is None:
            savefilepath = QFileDialog.getSaveFileName(self,"Export Detector",self.settings.getDataDirectory(),filter='*.yaml')[0]
        if savefilepath:
            with open(savefilepath,'w') as file:
                yaml.dump(exportstring, file)
        session = Session()
        detectorimport = dschema.load(exportstring, session=session)


    @Slot()
    def on_btnImportDetector_clicked(self, importfilepath=None):
        if importfilepath is None:
            importfilepath = QFileDialog.getOpenFileName(self, "Import Detector", self.settings.getDataDirectory(), filter='*.yaml')[0]
        if importfilepath:
            with open(importfilepath, 'r') as file:
                importdict = yaml.safe_load(file)
            dschema = DetectorSchema()
            session = Session()
            while session.query(Detector).filter_by(name=importdict['name']).first():
                importdict['name'] += '_Imported'
            if importdict['replay']:
                while session.query(Replay).filter_by(name=importdict['replay']['name']).first():
                    importdict['replay']['name'] += '_Imported'
            self.detector = dschema.load(importdict, session=session)
            session.add(self.detector)
            self.populate_gui_from_detector(self.detector)


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

