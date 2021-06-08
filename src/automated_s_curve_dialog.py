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
This module allows user to input seed for Random Number Generation to ensure reproducible
validation results
"""

from PyQt5.QtCore import pyqtSlot, QRegularExpression
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QWidgetItem
from PyQt5.QtGui import QRegularExpressionValidator

from src.rase_settings import RaseSettings
from src.ui_generated import ui_auto_scurve
from src.table_def import Session, Detector
from src.scenario_dialog import ScenarioDialog


class AutomatedSCurve(ui_auto_scurve.Ui_AutoSCurveDialog, QDialog):
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.setWindowTitle('Automated S-Curve Generation')
        self.Rase = parent
        self.settings = RaseSettings()
        self.setupUi(self)
        self.session = Session()

        # setting default states
        self.detName = None
        self.detReplay = None
        self.static_background = []
        self.setInstrumentItems()
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)

        # Validators
        self.line_rep.setValidator(QRegularExpressionValidator(QRegularExpression("[0-9]{0,9}")))
        self.line_initrep.setValidator(QRegularExpressionValidator(QRegularExpression("[0-9]{0,9}")))
        self.line_edge.setValidator(QRegularExpressionValidator(QRegularExpression("[0-9]{0,9}")))
        self.line_dwell.setValidator(QRegularExpressionValidator(QRegularExpression("((\d*\.\d*)|(\d*))")))
        self.line_minx.setValidator(QRegularExpressionValidator(QRegularExpression("((\d*\.\d*)|(\d*))")))
        self.line_maxx.setValidator(QRegularExpressionValidator(QRegularExpression("((\d*\.\d*)|(\d*))")))
        self.line_addpoints.setValidator(QRegularExpressionValidator(QRegularExpression(
                                r"((((\d+\.\d*)|(\d*\.\d+))|(\d+))((((,\d*\.\d+)|(,\d+\.\d*))|(,\d+))*)(,|,\.)?)")))
        self.line_lowerbound.setValidator(QRegularExpressionValidator(QRegularExpression("((\d*\.\d*)|(\d*))")))
        self.line_upperbound.setValidator(QRegularExpressionValidator(QRegularExpression("((\d*\.\d*)|(\d*))")))

        # connections
        self.combo_inst.currentTextChanged.connect(self.updateMaterials)
        self.combo_mat.currentTextChanged[str].connect(lambda mat: self.updateUnits(mat, self.combo_matdose))
        self.btn_bgnd.clicked.connect(self.defineBackground)

        # Confirm enables
        self.combo_matdose.currentTextChanged.connect(self.enableOk)

        # Set values of various things based on user inputs
        self.line_rep.editingFinished.connect(lambda: self.setminval(self.line_rep, '2'))
        self.line_initrep.editingFinished.connect(lambda: self.setminval(self.line_initrep, '1'))
        self.line_edge.editingFinished.connect(lambda: self.setminval(self.line_edge, '1'))
        self.line_dwell.editingFinished.connect(lambda: self.setminval(self.line_dwell, '1', '0.00000000001'))
        self.line_minx.editingFinished.connect(lambda: self.setminval(self.line_minx, '0.00000001', '0.00000000001'))
        self.line_maxx.editingFinished.connect(lambda: self.setminval(self.line_maxx, '0.001', '0.00000000001'))
        self.line_lowerbound.editingFinished.connect(lambda: self.setminval(self.line_lowerbound, '0'))
        self.line_lowerbound.editingFinished.connect(lambda: self.setmaxval(self.line_lowerbound, '.99'))
        self.line_upperbound.editingFinished.connect(lambda: self.setmaxval(self.line_upperbound, '1'))
        self.line_minx.editingFinished.connect(self.checkMaxX)
        self.line_maxx.editingFinished.connect(self.checkMaxX)
        self.line_lowerbound.editingFinished.connect(self.checkMaxY)
        self.line_upperbound.editingFinished.connect(self.checkMaxY)
        self.line_addpoints.editingFinished.connect(self.removeZeroPoint)
        self.check_minx.stateChanged.connect(self.setDefaultMin)
        self.check_maxx.stateChanged.connect(self.setDefaultMax)
        self.check_addpoints.stateChanged.connect(self.setAddPoints)
        self.check_name.stateChanged.connect(self.setDefaultName)

    def setInstrumentItems(self):
        for det in self.session.query(Detector):
            if det.replay and det.replay.is_cmd_line:
                self.combo_inst.addItem(det.name)

    @pyqtSlot(str)
    def updateMaterials(self, detName):
        """
        Updates the possible material selection based on the selected instrument.
        Also identify the name of the replay associated with the chosen detector
        and set it for S-curve processing
        """
        self.combo_mat.clear()
        self.combo_mat.addItem('')

        if not detName.strip():
            self.combo_mat.setCurrentIndex(0)
            self.combo_mat.setEnabled(False)
            self.btn_bgnd.setEnabled(False)
            self.detName = None
            self.detReplay = None
        else:
            self.detName = detName
            self.combo_mat.setEnabled(True)
            self.btn_bgnd.setEnabled(True)
            det = self.session.query(Detector).filter_by(name=detName).first()
            self.detReplay = det.replay.name
            for baseSpectrum in det.base_spectra:
                self.combo_mat.addItem(baseSpectrum.material.name)

    def updateUnits(self, matName, combobox):
        """
        General function call for updating the flux/dose setting in the
        combobox after material has been selected
        """
        combobox.clear()
        combobox.addItem('')
        if not matName.strip():
            combobox.setCurrentIndex(0)
            combobox.setEnabled(False)
        else:
            combobox.setEnabled(True)
            det = self.session.query(Detector).filter_by(name=self.detName).first()
            for baseSpectrum in det.base_spectra:
                if baseSpectrum.material_name == matName:
                    if baseSpectrum.rase_sensitivity:
                        combobox.addItem('DOSE (\u00B5Sv/h)')
                        combobox.setCurrentIndex(1)
                    if baseSpectrum.flux_sensitivity:
                        combobox.addItem('FLUX (\u03B3/(cm\u00B2s))')


    @pyqtSlot(str)
    def enableOk(self, intensity):
        """Only enable the okay button if all the relevant points are selected"""
        if self.combo_matdose.currentText() and self.line_dwell.text() and \
                self.line_maxx.text() and self.line_minx.text():
            self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(True)
        else:
            self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)

    def changeMinMax(self):
        """Change the min and max guess based on the background intensity"""

        if not self.check_minx.isChecked():
            minv = str(1E-7)
            minv = self.checkSciNote(minv)
            self.line_minx.setText(minv)
            self.checkMaxX()
            self.setAddPoints()
        if not self.check_maxx.isChecked():
            maxv = str(1E-2)
            maxv = self.checkSciNote(maxv)
            self.line_maxx.setText(maxv)
            self.checkMaxX()

    def checkSciNote(self, val):
        """If there is scientific notation, remove it so as to not break regex"""
        if 'E' in val.upper():
            sci = val.upper().split('E')
            if int(sci[1]) < 0:
                val = '0.' + ''.zfill(abs(int(sci[1])) - 1) + sci[0].replace('.', '')
            else:
                val = str(float(sci[0]) * 10 ** int(sci[1]))
        return val

    def setminval(self, line, setval='0.00000001', minval=None):
        if not minval:
            minval = setval
        try:
            if float(line.text()) <= float(minval):
                line.setText(setval)
        except:  # if the user enters a decimal point or something nonsensical
            line.setText(setval)

    def setmaxval(self, line, setval='1', maxval=None):
        if not maxval:
            maxval = setval
        try:
            if float(line.text()) >= float(maxval):
                line.setText(setval)
        except:  # if the user enters a decimal point or something nonsensical
            line.setText(setval)

    def checkMaxX(self):
        """Make sure the maximum x value is larger than the minimum x value"""
        if self.line_maxx.text() and self.line_minx.text():
            if float(self.line_maxx.text()) <= float(self.line_minx.text()):
                self.line_maxx.setText(str(float(self.line_minx.text()) * 1E5))

    def checkMaxY(self):
        """Make sure that the bounds don't overlap each other"""
        if self.line_upperbound.text() and self.line_lowerbound.text():
            if float(self.line_upperbound.text()) <= float(self.line_lowerbound.text()):
                self.line_upperbound.setText(str(max([0.9, float(self.line_lowerbound.text())*1.01])))

    def setDefaultMin(self):
        """Set the default minimum x value if it has been unchecked"""
        if not self.check_minx.isChecked():
            self.line_minx.setText('0.00000001')
            self.setAddPoints()
            self.checkMaxX()

    def setDefaultMax(self):
        """Set the default max x value if it has been unchecked"""
        if not self.check_maxx.isChecked():
            self.line_maxx.setText('0.001')
            self.checkMaxX()

    def setAddPoints(self):
        """Set default user-added points and clears them if the box is unchecked"""
        if self.check_addpoints.isChecked():
            if not self.line_addpoints.text():
                self.line_addpoints.setText(self.line_minx.text())
        else:
            self.line_addpoints.setText('')

    def setDefaultName(self):
        """Set name back to [Default] if the checkbox is unchecked"""
        if not self.check_name.isChecked():
            self.line_name.setText('[Default]')

    def removeZeroPoint(self):
        """Disallow the user to add a point with 0 dose/flux"""
        if self.line_addpoints.text():
            self.line_addpoints.setText(self.endRecurse(self.line_addpoints.text()))
            addpoints = [float(i) for i in self.line_addpoints.text().split(',')]
            if 0 in addpoints:
                addpoints = [i for i in addpoints if i != 0]
            addpoints = list(dict.fromkeys(addpoints))
            addpoints.sort()
            addpoints = [self.checkSciNote(str(i)) for i in addpoints]
            addpoints = str(addpoints)[1:-1].replace('\'', '').replace(' ', '')
            self.line_addpoints.setText(addpoints)

    def endRecurse(self, line):
        """Remove commas/periods at the end of the uesr-adde points list, recursively"""
        if (line[-1] == ',') or (line[-1] == '.'):
            return self.endRecurse(line[:-1])
        else:
            return line

    def defineBackground(self):
        dialog = ScenarioDialog(self, auto_s=True)
        dialog.comboDetectorSelect.setCurrentText(self.combo_inst.currentText())
        remove_layouts = [dialog.horizontalLayout, dialog.horizontalLayout_4]
        for layout in remove_layouts:
            for i in reversed(range(layout.count())):
                item = layout.itemAt(i)
                if isinstance(item, QWidgetItem):
                    item.widget().hide()
        dialog.pushButton.hide()
        dialog.tblMaterial.hide()
        dialog.label_scenlist.hide()
        dialog.txtScenariosList_2.hide()
        dialog.label_influences.hide()
        dialog.lstInfluences.hide()
        dialog.resize(440, 340)
        dialog.setWindowTitle('Set static background for the ' + self.combo_inst.currentText() + '.')
        dialog.exec_()

    @pyqtSlot()
    def accept(self):
        if self.line_addpoints.text():
            addpoints = [float(i) for i in self.line_addpoints.text().split(',')]
        else:
            addpoints = []
        self.input_d = {"instrument": self.detName,
                        "replay": self.detReplay,
                        "source": self.combo_mat.currentText(),
                        "source_fd": self.combo_matdose.currentText().split()[0],
                        "background": self.static_background,
                        "dwell_time": float(self.line_dwell.text()),
                        "results_type": self.combo_resulttype.currentText(),
                        "input_reps": int(self.line_rep.text()),
                        "invert_curve": self.check_invert.isChecked()
                        }

        self.input_advanced = {"rise_points": int(self.line_edge.text()),
                               "min_guess": float(self.line_minx.text()),
                               "max_guess": float(self.line_maxx.text()),
                               "repetitions": int(self.line_initrep.text()),
                               "add_points": addpoints,
                               "cleanup": self.check_cleanup.isChecked(),
                               "custom_name": self.line_name.text(),
                               "num_points": 6,  # hardcode for now
                               "lower_bound": float(self.line_lowerbound.text()),
                               "upper_bound": float(self.line_upperbound.text())
                               }

        return QDialog.accept(self)
