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
This module allows user to create replay scenario
"""

import re
import hashlib
from itertools import product
import numpy as np

from PySide6.QtCore import QModelIndex, Slot, QRegularExpression, Qt, QPoint
from PySide6.QtWidgets import QDialog, QTableWidgetItem, QLineEdit, QListWidgetItem, QMessageBox, QItemDelegate,  \
    QComboBox, QMenu, QDialogButtonBox
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import FlushError
from PySide6.QtGui import QRegularExpressionValidator, QStandardItemModel, QStandardItem, QAction, \
    QValidator

from src.qt_utils import DoubleValidator, IntValidator, RegExpValidator
from src.table_def import Session, Influence, ScenarioGroup, Material, ScenarioMaterial, ScenarioBackgroundMaterial, \
    Scenario, Detector, BaseSpectrum
from src.ui_generated import ui_create_scenario_dialog, ui_scenario_range_dialog
from src.rase_settings import RaseSettings
from src.scenario_group_dialog import GroupSettings
from src.help_dialog import HelpDialog

UNITS, MATERIAL, INTENSITY = 0, 1, 2
units_labels = {'DOSE': 'DOSE (\u00B5Sv/h)', 'FLUX': 'FLUX (\u03B3/(cm\u00B2s))'}


def RegExpSetValidator(parent=None, auto_s=False) -> QRegularExpressionValidator:
    """Returns a Validator for the set range format"""
    if auto_s:
        reg_ex = QRegularExpression("((\d*\.\d*)|(\d*))")
    else:
        reg_ex = QRegularExpression(
            r'((\d*\.\d+|\d+)-(\d*\.\d+|\d+):(\d*\.\d+|\d+)(((,\d*\.\d+)|(,\d+))*))|(((\d*\.\d+)|(\d+))((,\d*\.\d+)|(,\d+))*)')
    validator = RegExpValidator(reg_ex, parent)
    return validator

class ScenarioDialog(ui_create_scenario_dialog.Ui_ScenarioDialog, QDialog):
    def __init__(self, rase_gui, id=None, duplicate=[], auto_s=False):
        QDialog.__init__(self)
        self.setupUi(self)
        self.rase_gui = rase_gui
        self.tblMaterial.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tblBackground.setContextMenuPolicy(Qt.CustomContextMenu)
        self.id = id
        self.auto_s = auto_s
        self.settings = RaseSettings()
        self.scenarioHasChanged = False
        self.groupHasChanged = False
        self.duplicate = duplicate
        self.session = Session()

        self.txtAcqTime.setText('30')
        self.txtAcqTime.setToolTip(
            "Enter comma-separated values OR range as min-max:step OR range followed by comma-separated values")
        self.txtAcqTime.setValidator(RegExpSetValidator(self.txtAcqTime))
        self.txtAcqTime.validator().validationChanged.connect(self.handle_validation_change)

        self.txtReplication_2.setText('100')
        self.txtReplication_2.setValidator(IntValidator(self.txtReplication_2))
        self.txtReplication_2.validator().setBottom(1)
        self.txtReplication_2.validator().validationChanged.connect(self.handle_validation_change)

        self.tblMaterial.setHorizontalHeaderItem(INTENSITY, QTableWidgetItem('Intensity'))
        self.tblBackground.setHorizontalHeaderItem(INTENSITY, QTableWidgetItem('Intensity'))

        self.tblMaterial.customContextMenuRequested.connect(lambda x, table=self.tblMaterial:
                                                                self.context_auto_range(x, self.tblMaterial))
        self.tblBackground.customContextMenuRequested.connect(lambda x, table=self.tblBackground:
                                                                self.context_auto_range(x, self.tblBackground))

        # set material table
        self.tblMaterial.setItemDelegate(MaterialDoseDelegate(self.tblMaterial, unitsCol=UNITS,
                                                              materialCol=MATERIAL, intensityCol=INTENSITY,
                                                              tables=[self.tblMaterial, self.tblBackground]))
        self.tblMaterial.setRowCount(10)
        for row in range(self.tblMaterial.rowCount()):
            self.tblMaterial.setItem(row, UNITS, QTableWidgetItem())
            self.tblMaterial.setItem(row, INTENSITY, QTableWidgetItem())
            self.tblMaterial.setItem(row, MATERIAL, QTableWidgetItem())
            self.tblMaterial.item(row, INTENSITY).setToolTip("Enter comma-separated values OR range as min-max:step OR range followed by comma-separated values")
            self.tblMaterial.setRowHeight(row, 22)

        # set background table
        self.tblBackground.setItemDelegate(MaterialDoseDelegate(self.tblBackground, unitsCol=UNITS,
                                                                materialCol=MATERIAL, intensityCol=INTENSITY,
                                                                auto_s=self.auto_s,
                                                                tables=[self.tblMaterial, self.tblBackground]))
        self.tblBackground.setRowCount(10)
        for row in range(self.tblBackground.rowCount()):
            self.tblBackground.setItem(row, UNITS, QTableWidgetItem())
            self.tblBackground.setItem(row, INTENSITY, QTableWidgetItem())
            self.tblBackground.setItem(row, MATERIAL, QTableWidgetItem())
            self.tblBackground.item(row, INTENSITY).setToolTip("This material will not be run for detector(s): Symetrica due to containing an internal source for that detector. Set the Intensity to 0.5 to run with that detector.")
            self.tblBackground.setRowHeight(row, 22)

        # fill influence list
        for influence in self.session.query(Influence):
            self.lstInfluences.addItem(QListWidgetItem(influence.name))

        self.comboDetectorSelect.addItems(["all detectors"]+[s.name for s in self.session.query(Detector).all()])
        self.comboDetectorSelect.currentIndexChanged.connect(self.updateTableDelegate)

        # display a previous scenario if defined
        if self.id:
            if not self.duplicate:
                self.setWindowTitle("Scenario Edit")
                scenario = self.session.query(Scenario).get(id)
                materials = scenario.scen_materials
                bckg_materials = scenario.scen_bckg_materials
                influences = scenario.influences
                for table, mat_list in zip((self.tblMaterial, self.tblBackground),(materials, bckg_materials)):
                    for rowCount, mat in enumerate(mat_list):
                        item = QTableWidgetItem(units_labels[mat.fd_mode])
                        item.setData(Qt.UserRole, mat.fd_mode)
                        table.setItem(rowCount, UNITS, item)
                        table.setItem(rowCount, MATERIAL, QTableWidgetItem(mat.material_name))
                        item = QTableWidgetItem(str(mat.dose))
                        item.setData(Qt.UserRole, item.text())
                        table.setItem(rowCount, INTENSITY, item)
                self.txtComment.setText(scenario.comment)
                self.txtAcqTime.setText(str(scenario.acq_time))
                self.txtReplication_2.setText(str(scenario.replication))
                for influence in influences:
                    lst = self.lstInfluences.findItems(influence.name, Qt.MatchExactly)[0]
                    lst.setSelected(True)
                self.groups = self.getGroups()

            else:
                self.setWindowTitle("Build Scenario from Other Scenario")
                scens = [self.session.query(Scenario).filter_by(id=scen).first() for scen in self.duplicate]
                scenario = scens[0]
                materials = scenario.scen_materials
                back_materials = scenario.scen_bckg_materials
                influences = scenario.influences
                mat_dict = {}
                back_dict = {}
                mat_fd = []
                back_fd = []
                for mat in materials:
                    mat_fd.append((mat.material_name, mat.fd_mode))
                    mat_dict[mat.material_name] = set([mat.dose])
                for back in back_materials:
                    back_fd.append((back.material_name, back.fd_mode))
                    back_dict[back.material_name] = set([back.dose])

                if len(scens) > 1:
                    for scen in scens[1:]:
                        mat_dict = self.make_matDict(scen.scen_materials, mat_dict)
                        back_dict = self.make_matDict(scen.scen_bckg_materials, back_dict)
                        if influences:
                            influences.append[scen.influences]
                        else:
                            influences = scen.influences

                for table, material_dictionary, fd_list in \
                        zip((self.tblMaterial, self.tblBackground), (mat_dict, back_dict), (mat_fd, back_fd)):
                    mat_list_tup = [(k, v) for k, v in material_dictionary.items()]
                    for rowCount, (mat, fd_mode) in enumerate(zip(mat_list_tup, fd_list)):
                        doses = [str(d) for d in sorted(mat[1])]
                        item = QTableWidgetItem(units_labels[fd_mode[1]])
                        item.setData(Qt.UserRole, fd_mode[1])
                        table.setItem(rowCount, UNITS, item)
                        table.setItem(rowCount, MATERIAL, QTableWidgetItem(str(mat[0])))
                        item = QTableWidgetItem(str(','.join(doses)))
                        item.setData(Qt.UserRole, item.text())
                        table.setItem(rowCount, INTENSITY, item)
                self.txtComment.setText(scenario.comment)
                self.txtAcqTime.setText(str(scenario.acq_time))
                for influence in influences:
                    lst = self.lstInfluences.findItems(influence.name, Qt.MatchExactly)[0]
                    lst.setSelected(True)
                self.groups = self.getGroups()

        else:
            self.groups = []

        if self.auto_s and self.rase_gui.static_background:
            for rowCount, mat in enumerate(self.rase_gui.static_background):
                mat = mat[0]
                item = QTableWidgetItem(units_labels[mat[0]])
                item.setData(Qt.UserRole, mat[0])
                self.tblBackground.setItem(rowCount, UNITS, item)
                self.tblBackground.setItem(rowCount, MATERIAL, QTableWidgetItem(mat[1].name))
                item = QTableWidgetItem(str(mat[2]))
                item.setData(Qt.UserRole, item.text())
                self.tblBackground.setItem(rowCount, INTENSITY, item)

        # signal/slot connections (this has to be done after_ the previous scenario is loaded)
        self.tblMaterial.cellChanged.connect(self.scenarioChanged)
        self.tblBackground.cellChanged.connect(self.scenarioChanged)
        self.tblMaterial.cellChanged.connect(self.updateScenariosList)
        self.tblBackground.cellChanged.connect(self.updateScenariosList)
        self.lstInfluences.itemSelectionChanged.connect(self.scenarioChanged)
        self.txtComment.textChanged.connect(self.scenarioChanged)
        self.txtAcqTime.textChanged.connect(self.scenarioChanged)
        self.txtReplication_2.textChanged.connect(self.scenarioChanged)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def make_matDict(self, mats, m_dict):
        for mat in mats:
            m_dict[mat.material_name].update([mat.dose])
        return m_dict

    def getGroups(self):
        if self.id:
            if not self.duplicate:
                scen_edit = self.session.query(Scenario).filter_by(id=self.id).first()
                return [grp.name for grp in scen_edit.scenario_groups]
            else:
                scens = [self.session.query(Scenario).filter_by(id=scen).first() for scen in self.duplicate]
                grps = set()
                for scen in scens:
                    grps.update([grp.name for grp in scen.scenario_groups])
                return grps
        else:
            return []

    @Slot(QValidator.State)
    def handle_validation_change(self, state):
        if state == QValidator.Invalid:
            color = 'red'
        elif state == QValidator.Intermediate:
            color = 'gold'
        elif state == QValidator.Acceptable:
            color = 'green'
        sender = self.sender().parent()
        sender.setStyleSheet(f'border: 2px solid {color}')

    @Slot()
    def scenarioChanged(self):
        """
        Listens for Scenario changed
        Updates an internal flag related to changed scenario
        Enables and Disables OK button if scenario values are acceptable or not
        """
        self.scenarioHasChanged = True

        if self.txtAcqTime.hasAcceptableInput() and self.txtReplication_2.hasAcceptableInput():
            self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(True)
        else:
            self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)

    @Slot()
    def groupChanged(self):
        """
        Listens for group changed
        """
        self.groupHasChanged = True

    @Slot(int)
    def updateTableDelegate(self, index):
        if index == 0:
            selected_detname = None
        else:
            selected_detname = self.comboDetectorSelect.currentText()
        self.tblMaterial.setItemDelegate(MaterialDoseDelegate(self.tblMaterial, unitsCol=UNITS,
                                                              materialCol=MATERIAL, intensityCol=INTENSITY,
                                                              selected_detname=selected_detname,
                                                              tables=[self.tblMaterial, self.tblBackground]))
        self.tblBackground.setItemDelegate(MaterialDoseDelegate(self.tblBackground, unitsCol=UNITS,
                                                                materialCol=MATERIAL, intensityCol=INTENSITY,
                                                                selected_detname=selected_detname, auto_s=self.auto_s,
                                                                tables=[self.tblMaterial, self.tblBackground]))

    @Slot(QPoint)
    def context_auto_range(self, point, table):
        current_cell = table.itemAt(point)
        # show the context menu only if on an a valid part of the table
        if current_cell:
            column = current_cell.column()
            if column == INTENSITY:
                autorangeAction = QAction('Auto-Define Range', self)
                menu = QMenu(table)
                menu.addAction(autorangeAction)
                action = menu.exec_(table.mapToGlobal(point))
                if action == autorangeAction:
                    auto_list = self.auto_range()
                    if auto_list:
                        current_cell.setText(','.join(auto_list))
                        current_cell.setData(Qt.UserRole, current_cell.text())


    @Slot(bool)
    def auto_range(self):
        dialog = ScenarioRange(self)
        dialog.setWindowModality(Qt.WindowModal)
        if dialog.exec_():
            if dialog.points:
                return dialog.points


    @Slot()
    def updateScenariosList(self):
        materialStr=""
        for row in range(self.tblMaterial.rowCount()):
            untStr = self.tblMaterial.item(row, UNITS).text()
            matStr = self.tblMaterial.item(row, MATERIAL).text()
            intStr = self.tblMaterial.item(row, INTENSITY).data(Qt.UserRole)
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
            intStr = self.tblBackground.item(row, INTENSITY).data(Qt.UserRole)
            if matStr and untStr and intStr:
                if (len(backgroundStr)>0):
                    backgroundStr = backgroundStr + "\n "
                backgroundStr = backgroundStr + '{}({})'.format(matStr, ', '.join("{:.5f}".format(float(dose)) for
                                  dose in self.getSet(self.tblBackground.item(row, INTENSITY)))) + \
                                  ', Units: ' + self.tblBackground.item(row, UNITS).data(Qt.UserRole).title()
        self.txtScenariosList_2.setText(f"Source materials:\n {materialStr} \n\nBackground materials:\n {backgroundStr}")

    @Slot(bool)
    def on_btnGroups_clicked(self, checked):
        dialog = GroupSettings(self, groups=self.groups)
        dialog.setWindowModality(Qt.WindowModal)
        if dialog.exec_():
            self.groups = dialog.n_groups

    @Slot()
    def accept(self):
        if self.auto_s:
            materials_doses = []
            for matsT in [self.tblBackground]:
                for row in range(matsT.rowCount()):
                    matName = matsT.item(row, MATERIAL).text()
                    if matName:
                        matArr = []
                        for dose in self.getSet(matsT.item(row, 2)):
                            mat = self.session.query(Material).filter_by(name=matName).first()
                            fd_mat = matsT.item(row, UNITS).data(Qt.UserRole)
                            matArr.append((fd_mat, mat, dose))
                        materials_doses.append(matArr)

            self.rase_gui.static_background = materials_doses
            return QDialog.accept(self)

        self.tblMaterial.setCurrentIndex(QModelIndex())  # so that if table item is being edited it will commit the data

        # if this is edit rather than create, need to treat differently:
        if self.id and not self.duplicate:
            # check if the scenario has been changed by the user
            # Note that this approach considers a change even if
            # the user rewrites the previous entry identically
            if not self.scenarioHasChanged:
                # update just the group for the same scenario
                # so as not to change the scenario ID
                scen = self.session.query(Scenario).get(self.id)
                self.provide_message_new_groups = False
                self.add_groups_to_scen(scen, self.groups, add_groups=True)
                self.session.commit()
                return QDialog.accept(self)
            else:
                # clear the existing scenario first
                self.scenario_delete()

        # replication and influences
        replication = int(self.txtReplication_2.text())
        influences = [] # element type: Influence
        for index in self.lstInfluences.selectedIndexes():
            influences.append(self.session.query(Influence).filter_by(
                name=self.lstInfluences.itemFromIndex(index).text()).first())

        materials_doses = [[],[]]
        for i, matsT in enumerate([self.tblMaterial, self.tblBackground]):
            for row in range(matsT.rowCount()):
                matName = matsT.item(row, MATERIAL).text()
                if matName and matsT.item(row, 2).data(Qt.UserRole):   # skip if no intensity specified
                    matArr =[]
                    for dose in self.getSet(matsT.item(row, 2)):
                        mat = self.session.query(Material).filter_by(name=matName).first()
                        fd_mat = matsT.item(row, UNITS).data(Qt.UserRole)
                        matArr.append((fd_mat, mat, dose))
                    materials_doses[i].append(matArr)

        # cartesian product to break out scenarios from scenario group
        integrity_fail = False
        duplicate = False
        self.provide_message_new_groups = True
        for acqTime in self.getSet(self.txtAcqTime):
            mm = product(*materials_doses[0])
            bb = product(*materials_doses[1])
            for mat_dose_arr, bckg_mat_dose_arr in product(mm, bb):
                scenMaterials = [ScenarioMaterial(material=m, dose=float(d), fd_mode=u) for u, m, d in mat_dose_arr]
                bcgkScenMaterials = [ScenarioBackgroundMaterial(material=m, dose=float(d), fd_mode=u)
                                                                for u, m, d in bckg_mat_dose_arr]
                scen_groups = []
                try:
                    for groupname in self.groups:
                        scen_groups.append(self.session.query(ScenarioGroup).filter_by(name=groupname).first())
                    if not scen_groups:
                        scen_groups.append(self.session.query(ScenarioGroup).filter_by(name='default_group').first())
                    # if just changing groups, add to new group without creating a new scenario
                    scen_hash = Scenario.scenario_hash(float(acqTime), scenMaterials, bcgkScenMaterials, influences)
                    scen_exists = self.session.query(Scenario).filter_by(id=scen_hash).first()
                    add_groups = False
                    if scen_exists:
                        # and (sorted([g.name for g in scen_exists.scenario_groups]) !=
                        #                 sorted([g.name for g in scen_groups])):
                        for group in scen_groups:
                            if group not in scen_exists.scenario_groups:
                                add_groups = True
                                break
                        all_groups = set(g.name for g in scen_exists.scenario_groups + scen_groups)
                        all_groups.update(self.groups)
                        # don't allow duplicate scenarios, unless there are other scenarios in the group that are
                        # simply having their group changed. In which case, pass by those groups without impact.
                        duplicate = self.add_groups_to_scen(scen_exists, all_groups, add_groups=add_groups)
                    else:
                        self.session.add(Scenario(float(acqTime), replication, scenMaterials, bcgkScenMaterials, influences, scen_groups,
                                 self.txtComment.text()))
                # if inputting multiple scenarios with at least one preexisting scenario (i.e.: this only happens when
                # the loop traverses more than once and the database is accessed again)
                except (IntegrityError, FlushError):
                    self.integrity_message(materials_doses)
                    integrity_fail = True
                    break

        # if inputting a single scenario that already exists
        if not integrity_fail:
            if duplicate:
                self.integrity_message(materials_doses)
            else:
                try:
                    self.session.commit()
                    return QDialog.accept(self)
                except (IntegrityError, FlushError):
                    self.integrity_message(materials_doses)


    def add_groups_to_scen(self, scen, all_groups, add_groups=False):
        """
        Clear groups associated with a scenario and append new ones
        """
        if add_groups:
            scen.scenario_groups.clear()
            for groupname in all_groups:
                scen.scenario_groups.append(self.session.query(ScenarioGroup).filter_by(name=groupname).first())
                if self.provide_message_new_groups:
                    QMessageBox.information(self, 'Record Exists',
                                     'At least one defined scenario is already in the database; '
                                     'adding scenario to additional groups.')
                    self.provide_message_new_groups = False
        elif self.provide_message_new_groups:
            return True
        return False


    def scenario_delete(self):
        """
        Clear existing scenario before adding the modified version
        """
        scenDelete = self.session.query(Scenario).filter(Scenario.id == self.id)
        matDelete = self.session.query(ScenarioMaterial).filter(ScenarioMaterial.scenario_id == self.id)
        bckgMatDelete = self.session.query(ScenarioBackgroundMaterial).filter(
            ScenarioBackgroundMaterial.scenario_id == self.id)
        scenTableAssocDelete = scenDelete.first()
        scenTableAssocDelete.scenario_groups.clear()
        scenTableAssocDelete.influences.clear()
        matDelete.delete()
        bckgMatDelete.delete()
        scenDelete.delete()


    def integrity_message(self, materials_doses):
        if (materials_doses[0] and len(list(product(*materials_doses[0]))) > 1) or \
                (materials_doses[1] and len(list(product(*materials_doses[1]))) > 1):
            QMessageBox.critical(self, 'Record Exists',
                                 'At least one defined scenario is already in the database! '
                                 'Please change scenarios.')
        else:
            QMessageBox.critical(self, 'Record Exists',
                                 'This scenario is already in the database! Please change scenario.')
        self.session.rollback()

    # TODO: combine these two methods using a cellChanged.connect()
    @Slot(int, int)
    def on_tblMaterial_cellChanged(self, row, col):
        """
        Listens for Material table cell changed
        """
        if col == UNITS:
            if self.tblMaterial.item(row, MATERIAL) and self.tblMaterial.item(row, INTENSITY):
                if not self.tblMaterial.item(row, UNITS).data(Qt.UserRole):
                    self.tblMaterial.item(row, MATERIAL).setText('')
                    self.tblMaterial.item(row, INTENSITY).setText('')
                    self.tblMaterial.item(row, INTENSITY).setData(Qt.UserRole, None)
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

    @Slot(int, int)
    def on_tblBackground_cellChanged(self, row, col):
        """
        Listens for Material table cell changed
        """
        if col == UNITS:
            if self.tblBackground.item(row, MATERIAL) and self.tblBackground.item(row, INTENSITY):
                if not self.tblBackground.item(row, UNITS).data(Qt.UserRole):
                    self.tblBackground.item(row, MATERIAL).setText('')
                    self.tblBackground.item(row, INTENSITY).setText('')
                    self.tblBackground.item(row, INTENSITY).setData(Qt.UserRole, None)
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
            # set default value for intensity
            if not doseItem.text():
                doseItem.setText('0.1')
            else:
                doseItem.setText(doseItem.data(Qt.UserRole))    # in case previous value is from intrinsic source
            if Session().query(Material).get(matName).include_intrinsic:
                doseItem.setText('')
            doseItem.setData(Qt.UserRole, doseItem.text())

            # force units to match what is available in the selected base spectrum
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
        data = dialogField.data(Qt.UserRole) if type(dialogField) is QTableWidgetItem else dialogField.text()
        groups = data.split(',')
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
    def __init__(self, parent, materialCol, intensityCol=-1, unitsCol=2, selected_detname=None, editable=False,
                 auto_s=False, tables=None):
        super(MaterialDoseDelegate, self).__init__(parent)
        self.tblMat = parent
        self.tables = tables
        self.matCol = materialCol
        self.intensityCol = intensityCol
        self.unitsCol = unitsCol
        self.editable = editable
        self.selected_detname = selected_detname
        self.auto_s = auto_s
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

            intrinsic_material_present = False
            for table in self.tables:
                for row in range(table.rowCount()):
                    if row == index.row() and table is self.tblMat:
                        continue
                    item = table.item(row, self.matCol)
                    # remove any materials already used
                    if item and item.text() in material_list:
                        material_list.remove(item.text())
                    # check if at least one material include intrinsic source
                    if item and item.text() and Session().query(Material).get(item.text()).include_intrinsic:
                        intrinsic_material_present = True
            if intrinsic_material_present:  # only one material with intrinsic source is allowed
                for material in material_list:
                    if Session().query(Material).get(material).include_intrinsic:
                        material_list.remove(material)

            #create and populate comboEdit
            comboEdit = QComboBox(parent)
            comboEdit.setEditable(self.editable)
            comboEdit.setSizeAdjustPolicy(QComboBox.AdjustToContents)
            comboEdit.setMaxVisibleItems(25)
            comboEdit.addItem('')
            comboEdit.addItems(material_list)
            return comboEdit
        elif index.column() == self.intensityCol:
            return self.intensityEditor(parent, index)
        elif index.column() == self.unitsCol:
            return self.comboEditor(parent, index, units_labels)
        else:
            return super(MaterialDoseDelegate, self).createEditor(parent, option, index)

    def intensityEditor(self, parent, index):
        mat_name = self.tblMat.item(index.row(), self.matCol).text()
        if mat_name and Session().query(Material).get(mat_name).include_intrinsic:
            fd_units = self.tblMat.item(index.row(), self.unitsCol).data(Qt.UserRole)
            intensity_labels = {}
            for base_spectrum in Session().query(BaseSpectrum).filter_by(material_name=mat_name):
                if self.selected_detname and base_spectrum.detector_name != self.selected_detname:
                    continue
                if isinstance(base_spectrum.rase_sensitivity, float) and (fd_units == 'DOSE'):
                    intensity_value = str(base_spectrum.get_measured_dose_and_flux()[0])
                elif isinstance(base_spectrum.flux_sensitivity, float) and (fd_units == 'FLUX'):
                    intensity_value = str(base_spectrum.get_measured_dose_and_flux()[1])
                else:
                    continue
                if intensity_value in intensity_labels:
                    intensity_desc = intensity_labels[intensity_value].replace('Instrument', 'Instruments')
                    intensity_desc += f', {base_spectrum.detector_name}'
                else:
                    intensity_desc = f'{intensity_value} - Instrument: {base_spectrum.detector_name}'
                intensity_labels[intensity_value] = intensity_desc
            return self.comboEditor(parent, index, intensity_labels)
        else:
            editor = QLineEdit(parent)
            editor.setValidator(RegExpSetValidator(editor, self.auto_s))
            return editor

    def setModelData(self, editor, model, index):
        if index.column() == self.unitsCol:
            self.tblMat.item(index.row(), self.unitsCol).setText(editor.currentText())
            self.tblMat.item(index.row(), self.unitsCol).setData(Qt.UserRole, editor.currentData(Qt.UserRole))
        if index.column() == self.matCol:
            self.tblMat.item(index.row(), self.matCol).setText(editor.currentText())
        if index.column() == self.intensityCol:
            item = self.tblMat.item(index.row(), self.intensityCol)
            if type(editor) == QLineEdit:
                item.setText(editor.text())
                item.setData(Qt.UserRole, editor.text())
            elif type(editor) == QComboBox:
                item.setText(editor.currentText())
                item.setData(Qt.UserRole, editor.currentData(Qt.UserRole))

    def comboEditor(self, parent, index, map):
        curr_item = self.tblMat.item(index.row(), index.column())
        curr_item.setText('')
        curr_item.setData(Qt.UserRole, '')
        model = QStandardItemModel(0, 1)
        for key, text in map.items():
            item = QStandardItem(text)
            item.setData(key, Qt.UserRole)
            model.appendRow(item)
        comboEdit = QComboBox(parent)
        comboEdit.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        comboEdit.setModel(model)
        comboEdit.setCurrentIndex(comboEdit.findData(curr_item.data(Qt.UserRole)))
        return comboEdit


class ScenarioRange(ui_scenario_range_dialog.Ui_RangeDefinition, QDialog):
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.points = []
        self.help_dialog = None
        self.setupUi(self)

        self.line_max.setValidator(DoubleValidator(self.line_max))
        self.line_max.validator().setBottom(0.)
        self.line_max.validator().validationChanged.connect(self.handle_validation_change)

        self.line_min.setValidator(DoubleValidator(self.line_min))
        self.line_min.validator().setBottom(0.)
        self.line_min.validator().validationChanged.connect(self.handle_validation_change)
        self.line_min.textEdited.connect(self.update_max_validator_range)

        self.line_num.setValidator(IntValidator(self.line_num))
        self.line_num.validator().setBottom(1)
        self.line_num.validator().validationChanged.connect(self.handle_validation_change)

        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)

        self.line_dose.setValidator(DoubleValidator(self.line_dose))
        self.line_dose.validator().setBottom(1e-6)
        self.line_dose.validator().validationChanged.connect(self.handle_validation_change)

        self.line_distance.setValidator(DoubleValidator(self.line_distance))
        self.line_distance.validator().setBottom(1)
        self.line_distance.validator().validationChanged.connect(self.handle_validation_change)

        for widget in [self.line_num, self.line_max, self.line_min, self.line_dose, self.line_distance]:
            widget.textEdited.connect(self.update_calc)
        for widget in [self.radio_distance, self.radio_dose, self.radio_lin, self.radio_log]:
            widget.clicked.connect(self.update_calc)

        self.on_radio_distance_toggled(False)

        self.btnInfo.clicked.connect(self.open_help)

    @Slot(bool)
    def on_radio_distance_toggled(self, checked):
        self.wdgtDistanceParams.setVisible(checked)
        tmp_str = 'distance' if checked else 'dose/flux'
        self.label_minimum.setText(f"Minimum {tmp_str}:")
        self.label_maximum.setText(f"Maximum {tmp_str}:")

    @Slot(QValidator.State)
    def handle_validation_change(self, state):
        if state == QValidator.Invalid:
            color = 'red'
        elif state == QValidator.Intermediate:
            color = 'gold'
        elif state == QValidator.Acceptable:
            color = 'green'
        sender = self.sender().parent()
        sender.setStyleSheet(f'border: 2px solid {color}')
        # QtCore.QTimer.singleShot(1000, lambda: sender.setStyleSheet(''))

    @Slot(str)
    def update_max_validator_range(self, text):
        if self.sender().hasAcceptableInput():
            self.line_max.validator().setBottom(float(text) if text else 0.)

    @Slot(str)
    @Slot(bool)
    def update_calc(self, dummy):
        """Update computed points if all the relevant input are correct"""
        state = self.line_min.hasAcceptableInput() and self.line_max.hasAcceptableInput() \
                and self.line_num.hasAcceptableInput()
        if self.radio_distance.isChecked():
            state = state and self.line_dose.hasAcceptableInput() and self.line_distance.hasAcceptableInput()
        if state:
            self.calculate_range()
            self.display_points()
            self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(True)

    def calculate_range(self):
        range_min = float(self.line_min.text())
        range_min = 1.0e-12 if range_min == 0 else range_min
        range_max = float(self.line_max.text())
        steps = int(self.line_num.text())

        if self.radio_lin.isChecked():
            points = np.linspace(range_min, range_max, steps)
        else:
            points = np.geomspace(range_min, range_max, steps)

        if self.radio_distance.isChecked():
            ref_distance = float(self.line_distance.text())
            ref_dose = float(self.line_dose.text())
            points = ref_dose * np.power(ref_distance / points, 2)

        self.points = [f'{point:g}' for point in points]

    def display_points(self):
        """Display computed points"""
        model = QStandardItemModel()
        self.listView.setModel(model)
        for i in self.points:
            item = QStandardItem(i)
            item.setEditable(False)
            model.appendRow(item)

    def open_help(self):
        if not self.help_dialog:
            self.help_dialog = HelpDialog(page='Use_distance.html')
        if self.help_dialog.isHidden():
            self.help_dialog.load_page(page='Use_distance.html')
            self.help_dialog.show()
        self.help_dialog.activateWindow()
