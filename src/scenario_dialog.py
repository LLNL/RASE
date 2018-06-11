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
This module allows user to create replay scenario
"""

import re
from itertools import product

from PyQt5.QtCore import QModelIndex, pyqtSlot, QRegExp, Qt
from PyQt5.QtWidgets import QDialog, QTableWidgetItem, QLineEdit, QListWidgetItem, QMessageBox, QItemDelegate, QComboBox, QHeaderView
from sqlalchemy.exc import IntegrityError
from PyQt5.QtGui import QRegExpValidator

from .table_def import Session, Influence, ScenarioGroup, Material, ScenarioMaterial, Scenario
from .ui_generated import ui_create_scenario
from src.rase_settings import RaseSettings, DEFAULT_SCENARIO_GRPNAME

MATERIAL, DOSE = 0, 1


class ScenarioDialog(ui_create_scenario.Ui_ScenarioDialog, QDialog):
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

        # set buttons and text
        self.txtAcqTime.setText('30')
        self.txtReplication.setText('100')

        # set material table
        self.tblMaterial.setColumnWidth(MATERIAL, 120)
        self.tblMaterial.setColumnWidth(DOSE, 100)
        self.tblMaterial.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tblMaterial.setHorizontalHeaderItem(DOSE, QTableWidgetItem('Dose (\u00B5Sv/h)'))
        self.tblMaterial.setItemDelegate(MaterialDoseDelegate(self.tblMaterial, materialCol=MATERIAL, doseCol=DOSE))
        self.tblMaterial.setRowCount(10)
        for row in range(self.tblMaterial.rowCount()):
            self.tblMaterial.setItem(row, DOSE    , QTableWidgetItem())
            self.tblMaterial.setItem(row, MATERIAL, QTableWidgetItem())
            self.tblMaterial.item(row, DOSE).setToolTip("Enter value or range as min-max:step")
            self.tblMaterial.setRowHeight(row, 22)

        self.tblMaterial.cellChanged.connect(self.updateScenariosList)

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

        # display a previous scenario if defined
        if self.id:
            self.setWindowTitle("Scenario Edit")
            scenario = self.session.query(Scenario).get(id)
            materials = scenario.scen_materials
            influences = scenario.influences
            for rowCount, mat in enumerate(materials):
                self.tblMaterial.setItem(rowCount, 0, QTableWidgetItem(mat.material_name))
                self.tblMaterial.setItem(rowCount, 1, QTableWidgetItem(str(mat.dose)))
            self.txtAcqTime.setText(str(scenario.acq_time))
            self.txtReplication.setText(str(scenario.replication))
            scenGrp = self.session.query(ScenarioGroup).get(scenario.scen_group_id)
            i = self.comboScenarioGroupName.findText(scenGrp.name)
            self.comboScenarioGroupName.setCurrentIndex(i)
            self.txtScenarioGroupDescription.setPlainText(scenGrp.description)
            for influence in influences:
                lst = self.lstInfluences.findItems(influence.name, Qt.MatchExactly)[0]
                lst.setSelected(True)

        # signal/slot connections (this has to be done after_ the previous scenario is loaded)
        self.tblMaterial.cellChanged.connect(self.scenarioChanged)
        self.lstInfluences.itemSelectionChanged.connect(self.scenarioChanged)
        self.txtAcqTime.textChanged.connect(self.scenarioChanged)
        self.txtReplication.textChanged.connect(self.scenarioChanged)
        self.comboScenarioGroupName.currentIndexChanged.connect(self.groupChanged)
        self.comboScenarioGroupName.currentTextChanged.connect(self.groupChanged)


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
    def updateScenarioDesc(self, index):
        """
        Updates Scenario description
        """
        if index>=0:    # index = -1 should not happen, but just in case
            scenGrp = self.session.query(ScenarioGroup).filter_by(name = self.comboScenarioGroupName.currentText()).first()
            self.txtScenarioGroupDescription.setPlainText(scenGrp.description)

    @pyqtSlot()
    def updateScenariosList(self):
        scenDescList = []
        for row in range(self.tblMaterial.rowCount()):
            matStr = self.tblMaterial.item(row, MATERIAL).text()
            if matStr:
                scenDescList.append('{}({})'.format(matStr, ', '.join(str(dose) for dose in self.getSet(self.tblMaterial.item(row, DOSE)))))
        self.txtScenariosList.setText('\n'.join(scenDescList))

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
                matDelete.delete()
                scenDelete.delete()
                self.session.commit()

        # replication and influences
        replication = self.txtReplication.text()
        influences = [] # element type: Influence
        for index in self.lstInfluences.selectedIndexes():
            influences.append(self.session.query(Influence).filter_by(
                name = self.lstInfluences.itemFromIndex(index).text()).first())

        # load lists of components into lists to calculate cartesian product below
        scenarioComponents = []
        scenarioComponents.append(self.getSet(self.txtAcqTime))

        materials = []
        for row in range(self.tblMaterial.rowCount()):
            matName = self.tblMaterial.item(row, MATERIAL).text()
            if matName:
                materials.append(self.session.query(Material).filter_by(name = matName).first())
                scenarioComponents.append(self.getSet(self.tblMaterial.item(row, 1)))

        # cartesian product to break out scenarios from scenario group
        for acqTime, *doses in product(*scenarioComponents):
            scenMaterials = []
            for material, dose in zip(materials, doses):
                scenMaterials.append(ScenarioMaterial(material=material, dose=float(dose)))
            scenario = Scenario(acqTime, replication, scenMaterials, influences)
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

    @pyqtSlot(int, int)
    def on_tblMaterial_cellChanged(self, row, col):
        """
        Listens for Material table cell changed
        """
        if col == MATERIAL:
            matName = self.tblMaterial.item(row, MATERIAL).text()
            doseItem = self.tblMaterial.item(row, DOSE)
            if   not matName:         doseItem.setText('')
            elif not doseItem.text(): doseItem.setText('0.1')

    def getSet(self, dialogField):
        values = []
        groups =  dialogField.text().split(',')
        for group in groups:
            group = group.strip()
            if '-' in group:
                start, stop, step = [float(x) for x in re.match(r'([^-]+)-([^:]+):(.*)', group).groups()]
                if step == 0:
                    values.append(start)
                    values.append(stop)
                while start <= stop:
                    values.append(round(start, 7))
                    start += step
            else:
                values.append(group)
        return values


class MaterialDoseDelegate(QItemDelegate):
    def __init__(self, tblMat, materialCol, doseCol=-1, editable=False):
        QItemDelegate.__init__(self)
        self.tblMat = tblMat
        self.matCol = materialCol
        self.doseCol = doseCol
        self.editable = editable

    def createEditor(self, parent, option, index):
        if index.column() == self.matCol:
            # generate material list
            materialList = sorted([material.name for material in Session().query(Material)])

            # remove any materials already used
            for row in range(self.tblMat.rowCount()):
                item = self.tblMat.item(row, self.matCol)
                if item and item.text() in materialList:
                    materialList.remove(item.text())

            #create and populate comboEdit
            comboEdit = QComboBox(parent)
            comboEdit.setEditable(self.editable)
            comboEdit.setSizeAdjustPolicy(0)
            comboEdit.setMaxVisibleItems(25)
            comboEdit.addItem('')
            comboEdit.addItems(materialList)
            return comboEdit
        elif index.column() == self.doseCol:
            editor = QLineEdit(parent)
            validator = QRegExpValidator(QRegExp(r'([^-]+)-([^:]+):(.*)|^[+-]?([0-9]*[.])?[0-9]+$'), editor)
            editor.setValidator(validator)
            return editor
        else:
            return super(MaterialDoseDelegate, self).createEditor(parent, option, index)

