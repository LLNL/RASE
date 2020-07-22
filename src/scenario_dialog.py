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
This module allows user to create replay scenario
"""

import re
from itertools import product

from PyQt5.QtCore import QModelIndex, pyqtSlot, QRegExp, Qt
from PyQt5.QtWidgets import QDialog, QTableWidgetItem, QLineEdit, QListWidgetItem, QMessageBox, QItemDelegate, QComboBox, QHeaderView
from sqlalchemy.exc import IntegrityError
from PyQt5.QtGui import QRegExpValidator, QIntValidator, QStandardItemModel, QStandardItem

from .table_def import Session, Influence, ScenarioGroup, Material, ScenarioMaterial, ScenarioBackgroundMaterial, \
    Scenario, Detector
from .ui_generated import ui_create_scenario_dialog
from src.rase_settings import RaseSettings, DEFAULT_SCENARIO_GRPNAME

UNITS, MATERIAL, INTENSITY = 0, 1, 2
units_labels = {'DOSE': 'DOSE (\u00B5Sv/h)', 'FLUX': 'FLUX (\u03B3/(cm\u00B2s))'}


def RegExpSetValidator(parent = None) -> QRegExpValidator:
    """Returns a Validator for the set range format"""
    reg_ex = QRegExp(
        r'((\d*\.\d+|\d+)-(\d*\.\d+|\d+):(\d*\.\d+|\d+)(((,\d*\.\d+)|(,\d+))*))|(((\d*\.\d+)|(\d+))((,\d*\.\d+)|(,\d+))*)')
    validator = QRegExpValidator(reg_ex, parent)
    return validator

class ScenarioDialog(ui_create_scenario_dialog.Ui_ScenarioDialog, QDialog):
    def __init__(self, rase_gui, id=None):
        QDialog.__init__(self)
        self.setupUi(self)
        self.rase_gui = rase_gui
        #save the id if passed
        self.id = id
        self.settings = RaseSettings()
        self.scenarioHasChanged = False
        self.groupHasChanged = False
        self.session = Session()

        self.txtAcqTime.setText('30')
        self.txtAcqTime.setToolTip(
            "Enter comma-separated values OR range as min-max:step OR range followed by comma-separated values")
        self.txtReplication_2.setText('100')
        int_validator = QIntValidator()
        self.txtAcqTime.setValidator(RegExpSetValidator())
        self.txtReplication_2.setValidator(int_validator)

        self.tblMaterial.setHorizontalHeaderItem(INTENSITY, QTableWidgetItem('Intensity'))
        self.tblBackground.setHorizontalHeaderItem(INTENSITY, QTableWidgetItem('Intensity'))

        # set material table
        self.tblMaterial.setColumnWidth(UNITS, 80)
        self.tblMaterial.setColumnWidth(MATERIAL, 120)
        self.tblMaterial.setColumnWidth(INTENSITY, 100)
        self.tblMaterial.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tblMaterial.setItemDelegate(MaterialDoseDelegate(self.tblMaterial, unitsCol=UNITS,
                                                              materialCol=MATERIAL, intensityCol=INTENSITY))
        self.tblMaterial.setRowCount(10)
        for row in range(self.tblMaterial.rowCount()):
            self.tblMaterial.setItem(row, UNITS, QTableWidgetItem())
            self.tblMaterial.setItem(row, INTENSITY, QTableWidgetItem())
            self.tblMaterial.setItem(row, MATERIAL, QTableWidgetItem())
            self.tblMaterial.item(row, INTENSITY).setToolTip("Enter comma-separated values OR range as min-max:step OR range followed by comma-separated values")
            self.tblMaterial.setRowHeight(row, 22)

        # set background table
        #self.tblBackground.setEnabled(False)
        self.tblBackground.setColumnWidth(UNITS, 80)
        self.tblBackground.setColumnWidth(MATERIAL, 120)
        self.tblBackground.setColumnWidth(INTENSITY, 100)
        self.tblBackground.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tblBackground.setItemDelegate(MaterialDoseDelegate(self.tblBackground, unitsCol=UNITS,
                                                                materialCol=MATERIAL, intensityCol=INTENSITY))
        self.tblBackground.setRowCount(10)
        for row in range(self.tblBackground.rowCount()):
            self.tblBackground.setItem(row, UNITS, QTableWidgetItem())
            self.tblBackground.setItem(row, INTENSITY, QTableWidgetItem())
            self.tblBackground.setItem(row, MATERIAL, QTableWidgetItem())
            self.tblBackground.item(row, INTENSITY).setToolTip("Enter comma-separated values OR range as min-max:step OR range followed by comma-separated values")
            self.tblBackground.setRowHeight(row, 22)

        # link group name and description
        self.comboScenarioGroupName.currentIndexChanged.connect(self.updateScenarioDesc)
        self.comboScenarioGroupName.currentTextChanged.connect(self.txtScenarioGroupDescription.clear)

        # fill influence list
        for influence in self.session.query(Influence):
            self.lstInfluences.addItem(QListWidgetItem(influence.name))

        # fill the group name combo box
        self.comboScenarioGroupName.addItems([s.name for s in self.session.query(ScenarioGroup).all()])
        i = self.comboScenarioGroupName.findText(self.settings.getLastScenarioGroupName())
        if i>=0:
            self.comboScenarioGroupName.setCurrentIndex(i)
        else:
            self.comboScenarioGroupName.setCurrentText(DEFAULT_SCENARIO_GRPNAME)

        self.comboDetectorSelect.addItems(["all detectors"]+[s.name for s in self.session.query(Detector).all()])
        self.comboDetectorSelect.currentIndexChanged.connect(self.updateTableDelegate)

        # display a previous scenario if defined
        if self.id:
            self.setWindowTitle("Scenario Edit")
            scenario = self.session.query(Scenario).get(id)
            materials = scenario.scen_materials
            bckg_materials = scenario.scen_bckg_materials
            influences = scenario.influences
            for table, mat_list in zip((self.tblMaterial, self.tblBackground),(materials, bckg_materials)):
                for rowCount, mat in enumerate(mat_list):
                    item = QTableWidgetItem(units_labels[mat.fd_mode])
                    item.setData(Qt.UserRole, mat.fd_mode)
                    table.setItem(rowCount, 0, item)
                    table.setItem(rowCount, 1, QTableWidgetItem(mat.material_name))
                    table.setItem(rowCount, 2, QTableWidgetItem(str(mat.dose)))
            self.txtAcqTime.setText(str(scenario.acq_time))
            self.txtReplication_2.setText(str(scenario.replication))
            scenGrp = self.session.query(ScenarioGroup).get(scenario.scen_group_id)
            i = self.comboScenarioGroupName.findText(scenGrp.name)
            self.comboScenarioGroupName.setCurrentIndex(i)
            self.txtScenarioGroupDescription.setPlainText(scenGrp.description)
            for influence in influences:
                lst = self.lstInfluences.findItems(influence.name, Qt.MatchExactly)[0]
                lst.setSelected(True)

        # signal/slot connections (this has to be done after_ the previous scenario is loaded)
        self.tblMaterial.cellChanged.connect(self.scenarioChanged)
        # self.tblMaterial.cellChanged.connect(self.material_hasChanged)
        self.tblBackground.cellChanged.connect(self.scenarioChanged)
        # self.tblBackground.cellChanged.connect(self.material_hasChanged)
        self.tblMaterial.cellChanged.connect(self.updateScenariosList)
        self.tblBackground.cellChanged.connect(self.updateScenariosList)
        self.lstInfluences.itemSelectionChanged.connect(self.scenarioChanged)
        self.txtAcqTime.textChanged.connect(self.scenarioChanged)
        self.txtReplication_2.textChanged.connect(self.scenarioChanged)
        self.comboScenarioGroupName.currentIndexChanged.connect(self.groupChanged)
        self.comboScenarioGroupName.currentTextChanged.connect(self.groupChanged)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        

    @pyqtSlot()
    def scenarioChanged(self):
        """
        Listens for Scenario changed
        """
        self.scenarioHasChanged = True

    @pyqtSlot()
    def groupChanged(self):
        """
        Listens for group changed
        """
        self.groupHasChanged = True

    @pyqtSlot(int)
    def updateTableDelegate(self, index):
        if index == 0:
            selected_detname = None
        else:
            selected_detname = self.comboDetectorSelect.currentText()
        self.tblMaterial.setItemDelegate(MaterialDoseDelegate(self.tblMaterial, unitsCol=UNITS,
                                                              materialCol=MATERIAL, intensityCol=INTENSITY,
                                                              selected_detname=selected_detname))
        self.tblBackground.setItemDelegate(MaterialDoseDelegate(self.tblBackground, unitsCol=UNITS,
                                                                materialCol=MATERIAL, intensityCol=INTENSITY,
                                                                selected_detname=selected_detname))

    @pyqtSlot(int)
    def updateScenarioDesc(self, index):
        """
        Updates Scenario description
        """
        if index >= 0:    # index = -1 should not happen, but just in case
            scenGrp = self.session.query(ScenarioGroup).filter_by(name=self.comboScenarioGroupName.currentText()).first()
            self.txtScenarioGroupDescription.setPlainText(scenGrp.description)

    @pyqtSlot()
    def updateScenariosList(self):
        materialStr=""
        for row in range(self.tblMaterial.rowCount()):
            untStr = self.tblMaterial.item(row, UNITS).text()
            matStr = self.tblMaterial.item(row, MATERIAL).text()
            intStr = self.tblMaterial.item(row, INTENSITY).text()
            if matStr and untStr and intStr:
                if (len(materialStr) > 0):
                    materialStr = materialStr + "\n "
                materialStr = materialStr + '{}({})'.format(matStr, ', '.join("{:.5f}".format(float(dose)) for
                                  dose in self.getSet(self.tblMaterial.item(row, INTENSITY)))) + \
                                  ', Units: ' + self.tblMaterial.item(row, UNITS).data(Qt.UserRole).title()

        backgroundStr = ""
        for row in range(self.tblBackground.rowCount()):
            untStr = self.tblBackground.item(row, UNITS).text()
            matStr = self.tblBackground.item(row, MATERIAL).text()
            intStr = self.tblBackground.item(row, INTENSITY).text()
            if matStr and untStr and intStr:
                if (len(backgroundStr)>0):
                    backgroundStr = backgroundStr + "\n "
                backgroundStr = backgroundStr + '{}({})'.format(matStr, ', '.join("{:.5f}".format(float(dose)) for
                                  dose in self.getSet(self.tblBackground.item(row, INTENSITY)))) + \
                                  ', Units: ' + self.tblBackground.item(row, UNITS).data(Qt.UserRole).title()
        self.txtScenariosList_2.setText(f"Source materials:\n {materialStr} \n\nBackground materials:\n {backgroundStr}")

    @pyqtSlot()
    def accept(self):
        self.tblMaterial.setCurrentIndex(QModelIndex()) # so that if table item is being edited it will commit the data

        scenGrpName = self.comboScenarioGroupName.currentText()
        scenGrpDesc = self.txtScenarioGroupDescription.toPlainText()

        # Use existing scenario group if available
        # Otherwise create a new one
        scenGroup = self.session.query(ScenarioGroup).filter_by(name=scenGrpName).first()
        if not scenGroup:
            scenGroup = ScenarioGroup(name=scenGrpName, description=scenGrpDesc)
            self.session.add(scenGroup)
        else:
            scenGroup.description = scenGrpDesc

        # if this is edit rather than create, need to treat differently:
        if self.id:
            # check if the scenario has been changed by the user
            # Note that this approach considers a change even if
            # the user rewrites the previous entry identically
            if not self.scenarioHasChanged:
                # if group has not changed, just exit
                # otherwise update just the group for the same scenario
                # so as not to change the scenario ID
                if not self.groupHasChanged:
                    return QDialog.accept(self)
                else:
                    scen = self.session.query(Scenario).get(self.id)
                    scen.scen_group_id = scenGroup.id
                    self.session.commit()
                    return QDialog.accept(self)
            else:
                # clear the existing scenario first
                scenDelete = self.session.query(Scenario).filter(Scenario.id == self.id)
                matDelete = self.session.query(ScenarioMaterial).filter(ScenarioMaterial.scenario_id == self.id)
                bckgMatDelete = self.session.query(ScenarioBackgroundMaterial).filter(ScenarioBackgroundMaterial.scenario_id == self.id)
                matDelete.delete()
                bckgMatDelete.delete()
                scenDelete.delete()
                self.session.commit()

        # replication and influences
        replication = int(self.txtReplication_2.text())
        influences = [] # element type: Influence
        for index in self.lstInfluences.selectedIndexes():
            influences.append(self.session.query(Influence).filter_by(
                name = self.lstInfluences.itemFromIndex(index).text()).first())

        materials_doses = [[],[]]
        for i, matsT in enumerate([self.tblMaterial, self.tblBackground]):
            for row in range(matsT.rowCount()):
                matName = matsT.item(row, MATERIAL).text()
                if matName:
                    matArr =[]
                    for dose in self.getSet(matsT.item(row, 2)):
                        mat = self.session.query(Material).filter_by(name=matName).first()
                        fd_mat = matsT.item(row, UNITS).data(Qt.UserRole)
                        matArr.append((fd_mat, mat, dose))
                    materials_doses[i].append(matArr)

        # cartesian product to break out scenarios from scenario group
        for acqTime in self.getSet(self.txtAcqTime):
            mm = product(*materials_doses[0])
            bb = product(*materials_doses[1])
            for mat_dose_arr, bckg_mat_dose_arr in product(mm, bb):
                scenMaterials = [ScenarioMaterial(material=m, dose=float(d), fd_mode=u) for u, m, d in mat_dose_arr]
                bcgkScenMaterials = [ScenarioBackgroundMaterial(material=m, dose=float(d), fd_mode=u)
                                                                for u, m, d in bckg_mat_dose_arr]
                scenario = Scenario(float(acqTime), replication, scenMaterials, bcgkScenMaterials, influences)
                scenGroup.scenarios.append(scenario)

        # update the record of the last scenario entered
        self.settings.setLastScenarioGroupName(scenGrpName)

        try:
            self.session.commit()
            return QDialog.accept(self)
        except IntegrityError:
            QMessageBox.critical(self, 'Record Exists',
                                 'At least one record from this Scenario Group is in the database! Please change scenario.')
            self.session.rollback()

    # TODO: combine these two methods using a cellChanged.connect()
    @pyqtSlot(int, int)
    def on_tblMaterial_cellChanged(self, row, col):
        """
        Listens for Material table cell changed
        """
        if col == UNITS:
            if self.tblMaterial.item(row, MATERIAL) and self.tblMaterial.item(row, INTENSITY):
                if not self.tblMaterial.item(row, UNITS).data(Qt.UserRole):
                    self.tblMaterial.item(row, MATERIAL).setText('')
                    self.tblMaterial.item(row, INTENSITY).setText('')
                elif self.tblMaterial.item(row, MATERIAL):
                    units = self.tblMaterial.item(row, UNITS)
                    matName = self.tblMaterial.item(row, MATERIAL)
                    doseItem = self.tblMaterial.item(row, INTENSITY)
                    self.set_otherCols_fromUnit(units, matName, doseItem)

        if col == MATERIAL:
            units = self.tblMaterial.item(row, UNITS)
            matName = self.tblMaterial.item(row, MATERIAL).text()
            doseItem = self.tblMaterial.item(row, INTENSITY)
            self.set_otherCols_fromMat(units, matName, doseItem)

    @pyqtSlot(int, int)
    def on_tblBackground_cellChanged(self, row, col):
        """
        Listens for Material table cell changed
        """
        if col == UNITS:
            if self.tblBackground.item(row, MATERIAL) and self.tblBackground.item(row, INTENSITY):
                if not self.tblBackground.item(row, UNITS).data(Qt.UserRole):
                    self.tblBackground.item(row, MATERIAL).setText('')
                    self.tblBackground.item(row, INTENSITY).setText('')
                elif self.tblBackground.item(row, MATERIAL):
                    units = self.tblBackground.item(row, UNITS)
                    matName = self.tblBackground.item(row, MATERIAL)
                    doseItem = self.tblBackground.item(row, INTENSITY)
                    self.set_otherCols_fromUnit(units, matName, doseItem)
        if col == MATERIAL:
            units = self.tblBackground.item(row, UNITS)
            matName = self.tblBackground.item(row, MATERIAL).text()
            doseItem = self.tblBackground.item(row, INTENSITY)
            self.set_otherCols_fromMat(units, matName, doseItem)

    def set_otherCols_fromUnit(self, units, matName, doseItem):
        textKeep = False
        if self.comboDetectorSelect.currentIndex() == 0:
            detector_list = [detector for detector in Session().query(Detector)]
        else:
            detector_list = [Session().query(Detector).filter_by(
                name=self.comboDetectorSelect.currentText()).first()]
        for detector in detector_list:
            for baseSpectrum in detector.base_spectra:
                if baseSpectrum.material.name == matName.text() and not textKeep:
                    if (units.data(Qt.UserRole) == 'DOSE' and isinstance(baseSpectrum.rase_sensitivity, float)) or \
                       (units.data(Qt.UserRole) == 'FLUX' and isinstance(baseSpectrum.flux_sensitivity, float)):
                        textKeep = True
        if not textKeep:
            matName.setText('')

    def set_otherCols_fromMat(self, units, matName, doseItem):
        if matName:
            if not doseItem.text():
                doseItem.setText('0.1')
            if not units.text():
                textSet = False
                if self.comboDetectorSelect.currentIndex() == 0:
                    detector_list = [detector for detector in Session().query(Detector)]
                else:
                    detector_list = [Session().query(Detector).filter_by(
                        name=self.comboDetectorSelect.currentText()).first()]
                for detector in detector_list:
                    for baseSpectrum in detector.base_spectra:
                        if baseSpectrum.material.name == matName and not textSet:
                            units.tableWidget().blockSignals(True)
                            if isinstance(baseSpectrum.rase_sensitivity, float):
                                units.setText(units_labels['DOSE'])
                                units.setData(Qt.UserRole, 'DOSE')
                                textSet = True
                            else:
                                units.setText(units_labels['FLUX'])
                                units.setData(Qt.UserRole, 'FLUX')
                            units.tableWidget().blockSignals(False)

    def getSet(self, dialogField):
        values = []
        groups =  dialogField.text().split(',')
        for group in groups:
            group = group.strip()
            if '-' in group and ':' in group:
                start, stop, step = [float(x) for x in re.match(r'([^-]+)-([^:]+):(.*)', group).groups()]
                if step == 0:
                    values.append(start)
                    values.append(stop)
                else:
                    while start <= stop:
                        values.append(start)
                        start += step
            else:
                values.append(group)
        return values


class MaterialDoseDelegate(QItemDelegate):
    def __init__(self, tblMat, materialCol, intensityCol=-1, unitsCol=2, selected_detname=None, editable=False):
        QItemDelegate.__init__(self)
        self.tblMat = tblMat
        self.matCol = materialCol
        self.intensityCol = intensityCol
        self.unitsCol = unitsCol
        self.editable = editable
        self.selected_detname = selected_detname
        self.settings = RaseSettings()

    def createEditor(self, parent, option, index):
        if index.column() == self.matCol:
            # generate material list
            fd_units = self.tblMat.item(index.row(), self.unitsCol).data(Qt.UserRole)
            material_list = []
            if not self.selected_detname:
                for detector in Session().query(Detector):
                    for baseSpectrum in detector.base_spectra:
                        if baseSpectrum.material.name not in material_list:
                            if ((isinstance(baseSpectrum.rase_sensitivity, float) and (fd_units == 'DOSE')) or
                                (isinstance(baseSpectrum.flux_sensitivity, float) and (fd_units == 'FLUX')) or
                                    not fd_units):
                                material_list.append(baseSpectrum.material.name)
                material_list = sorted(material_list)
            else:
                detector = Session().query(Detector).filter_by(name=self.selected_detname).first()
                material_list = sorted([baseSpectrum.material.name for baseSpectrum in detector.base_spectra if
                                        ((isinstance(baseSpectrum.rase_sensitivity, float) and (fd_units == 'DOSE')) or
                                         (isinstance(baseSpectrum.flux_sensitivity, float) and (fd_units == 'FLUX')) or
                                            not fd_units)])
            # remove any materials already used
            for row in range(self.tblMat.rowCount()):
                item = self.tblMat.item(row, self.matCol)
                if item and item.text() in material_list:
                    material_list.remove(item.text())

            #create and populate comboEdit
            comboEdit = QComboBox(parent)
            comboEdit.setEditable(self.editable)
            comboEdit.setSizeAdjustPolicy(0)
            comboEdit.setMaxVisibleItems(25)
            comboEdit.addItem('')
            comboEdit.addItems(material_list)
            return comboEdit
        elif index.column() == self.intensityCol:
            editor = QLineEdit(parent)
            editor.setValidator(RegExpSetValidator(editor))
            return editor
        elif index.column() == self.unitsCol:
            return self.unitsEditor(parent, index)
        else:
            return super(MaterialDoseDelegate, self).createEditor(parent, option, index)

    # def setEditorData(self, editor, index):
    #     if index.column() == self.unitsCol:
    #         item = self.tblMat.item(index.row(), self.unitsCol)
    #         print("setEditorData", item.data(Qt.UserRole))
    #         editor.setCurrentIndex(editor.findData(item.data(Qt.UserRole)))

    def setModelData(self, editor, model, index):
        if index.column() == self.unitsCol:
            self.tblMat.item(index.row(), self.unitsCol).setText(editor.currentText())
            self.tblMat.item(index.row(), self.unitsCol).setData(Qt.UserRole, editor.currentData(Qt.UserRole))
        if index.column() == self.matCol:
            self.tblMat.item(index.row(), self.matCol).setText(editor.currentText())
        if index.column() == self.intensityCol:
            self.tblMat.item(index.row(), self.intensityCol).setText(editor.text())

    def unitsEditor(self, parent, index):
        curr_item = self.tblMat.item(index.row(), self.unitsCol)
        curr_item.setText('')
        model = QStandardItemModel(0, 1)
        for index, (key, text) in enumerate(units_labels.items()):
            item = QStandardItem(text)
            item.setData(key, Qt.UserRole)
            model.appendRow(item)
        comboEdit = QComboBox(parent)
        comboEdit.setSizeAdjustPolicy(0)
        comboEdit.setModel(model)
        comboEdit.setCurrentIndex(comboEdit.findData(curr_item.data(Qt.UserRole)))
        return comboEdit
