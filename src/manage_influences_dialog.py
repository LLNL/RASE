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
This module supports import, export and deletion of user defined replay options
"""

import csv

from PySide6.QtWidgets import QDialog, QFileDialog, QTableWidgetItem, QAbstractItemView
from PySide6.QtWidgets import QHeaderView, QMessageBox
from PySide6.QtCore import Slot, Qt

from .table_def import Session, DetectorInfluence, Influence, Scenario, ScenarioMaterial, ScenarioBackgroundMaterial
from .ui_generated import ui_manage_influences_dialog
from src.rase_settings import RaseSettings

NUM_COL = 11
NAME, INFL_0, DEGRAGE_INFL_0, INFL_1, DEGRAGE_INFL_1, INFL_2, DEGRAGE_INFL_2, FIX_SMEAR, DEGRADE_FIX_SMEAR, \
LIN_SMEAR, DEGRADE_LIN_SMEAR = range(NUM_COL)
COLUMNS = [NAME, INFL_0, DEGRAGE_INFL_0, INFL_1, DEGRAGE_INFL_1, INFL_2, DEGRAGE_INFL_2, FIX_SMEAR,
           DEGRADE_FIX_SMEAR, LIN_SMEAR, DEGRADE_LIN_SMEAR]

class ManageInfluencesDialog(ui_manage_influences_dialog.Ui_Dialog, QDialog):
    def __init__(self, parent = None, modify_flag=False):
        QDialog.__init__(self)
        self.parent = parent
        self.modify_flag = modify_flag
        self.session = Session()
        self.settings = RaseSettings()
        self.setupUi(self)
        self.setInfluencesTable()
        self.btnDeleteSelectedInfluences.clicked.connect(self.deleteSelectedInfluences)
        self.buttonExport.clicked.connect(self.handleExport)
        self.buttonImport.clicked.connect(self.handleImport)
        self.btnAddNewInfluence.clicked.connect(self.on_btnNewInfluence_clicked)

        if self.modify_flag:
            self.setWindowTitle('Modify Influences')
        else:
            self.setWindowTitle('Add Influences')

        self.influencesToDelete = []


    def setInfluencesTable(self):
        influences = list(self.session.query(DetectorInfluence))
        if self.tblInfluences:
            self.tblInfluences.clear()
        self.tblInfluences.setColumnCount(NUM_COL)
        self.tblInfluences.setRowCount(len(influences))
        self.tblInfluences.setHorizontalHeaderLabels(['Name', 'Infl_0\n(offset)', 'Drift\n(Infl_0)',
                                                              'Infl_1\n(linear)', 'Drift\n(Infl_1)',
                                                              'Infl_2\n(quadratic)', 'Drift\n(Infl_2)',
                                                              'Fixed Smear\n(Eres, keV)', 'Drift\n(Fixed Smear)',
                                                              'Linear Smear\n(Eres, %)', 'Drift\n(Linear Smear)'])
        self.tblInfluences.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tblInfluences.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        row = 0
        if self.modify_flag:
            union = Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled
        else:
            union = Qt.ItemIsSelectable | Qt.ItemIsEnabled

        for influence in influences:
            item = QTableWidgetItem(QTableWidgetItem(influence.influence_name))
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.tblInfluences.setItem(row, NAME, item)
            for (col, infl) in zip(COLUMNS[1:], [str(influence.infl_0), str(influence.degrade_infl0),
                                             str(influence.infl_1), str(influence.degrade_infl1),
                                             str(influence.infl_2), str(influence.degrade_infl2),
                                             str(influence.fixed_smear), str(influence.degrade_f_smear),
                                             str(influence.linear_smear), str(influence.degrade_l_smear)]):
                item = QTableWidgetItem(infl)
                item.setFlags(union)
                self.tblInfluences.setItem(row, col, item)
            row += 1

        self.tblInfluences.setColumnWidth(INFL_2, 80)
        self.tblInfluences.setColumnWidth(FIX_SMEAR, 90)
        self.tblInfluences.setColumnWidth(DEGRADE_FIX_SMEAR, 90)
        self.tblInfluences.setColumnWidth(LIN_SMEAR, 90)
        self.tblInfluences.setColumnWidth(DEGRADE_LIN_SMEAR, 90)

    def on_btnNewInfluence_clicked(self, checked):
        """
        Adds new influence row that is fully editable
        """
        row = self.tblInfluences.rowCount()
        self.tblInfluences.insertRow(row)
        union = Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled
        for col in COLUMNS:
            item = QTableWidgetItem()
            item.setFlags(union)
            if col != NAME and col != INFL_1:
                item.setText('0.0')
            elif col == INFL_1:
                item.setText('1.0')
            self.tblInfluences.setItem(row, col, item)


    def handleExport(self):
        """
        Exports to CSV
        """
        path = QFileDialog.getSaveFileName(self, 'Save File', self.settings.getDataDirectory(), 'CSV (*.csv)')
        if path[0]:
            with open(path[0], mode='w', newline='') as stream:
                writer = csv.writer(stream)
                for row in range(self.tblInfluences.rowCount()):
                    rowdata = []
                    for column in range(self.tblInfluences.columnCount()):
                        item = self.tblInfluences.item(row, column)
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
                self.tblInfluences.setRowCount(0)
                self.tblInfluences.setColumnCount(0)
                for rowdata in csv.reader(stream):
                    row = self.tblInfluences.rowCount()
                    self.tblInfluences.insertRow(row)
                    self.tblInfluences.setColumnCount(len(rowdata))
                    for column, data in enumerate(rowdata):
                        item = QTableWidgetItem(data)
                        self.tblInfluences.setItem(row, column, item)
            self.tblInfluences.setHorizontalHeaderLabels(['Name', 'Infl_0\n(offset)', 'Drift\n(Infl_0)',
                                                              'Infl_1\n(linear)', 'Drift\n(Infl_1)',
                                                              'Infl_2\n(quadratic)', 'Drift\n(Infl_2)',
                                                              'Fixed Smear\n(Eres, keV)', 'Drift\n(Fixed Smear)',
                                                              'Linear Smear\n(Eres, %)', 'Drift\n(Linear Smear)'])

    def deleteSelectedInfluences(self):
        """
        Deletes Selected Influences
        """
        rows = self.tblInfluences.selectionModel().selectedRows()
        indices =[]
        for r in rows:
            indices.append(r.row())
        indices.sort(reverse=True)
        for index in indices:
            name = self.tblInfluences.item(index, NAME).text()
            self.tblInfluences.removeRow(index)
            influenceDelete = self.session.query(Influence).filter(Influence.name == name).first()
            if influenceDelete:
                self.influencesToDelete.append(influenceDelete)


    @Slot()
    def accept(self):
        """
        Closes dialog
        """
        names = []
        for row in range(self.tblInfluences.rowCount()):
            try:
                for col in COLUMNS[1:]:
                    float(self.tblInfluences.item(row, col).text())
            except:
                return QMessageBox.critical(self, 'Invalid influence value', 'All specified influence values must be numbers')

            if not self.tblInfluences.item(row, NAME).text():
                return QMessageBox.critical(self, 'Unnamed influence', 'Influence must have a name!')
            names.append(self.tblInfluences.item(row, NAME).text())
            if not self.tblInfluences.item(row, INFL_1).text():
                self.tblInfluences.item(row, INFL_1).setText('1')
            elif float(self.tblInfluences.item(row, INFL_1).text()) <= 0:
                return QMessageBox.critical(self, 'Linear influence factor error', 'Linear scaling factor must be greater than zero! For no linear scaling, set this value to 1.')

        if len(names) != len(set(names)):
            return QMessageBox.critical(self, 'Repeat influence', 'Influences must each have unique names!')

        for row in range(self.tblInfluences.rowCount()):

            influence_name = self.tblInfluences.item(row, NAME).text()

            influence = self.session.query(Influence).filter_by(name=influence_name).first()
            if not influence:
                influence = Influence()
                influence.name = influence_name
                self.session.add(influence)

            det_influence = self.session.query(DetectorInfluence).filter_by(influence_name=influence_name).first()
            if not det_influence:
                det_influence = DetectorInfluence()
                self.session.add(det_influence)

            det_influence.influence_name = influence_name
            for col in COLUMNS[INFL_0:]:
                if not self.tblInfluences.item(row, col).text():
                    if col == INFL_1:
                        self.tblInfluences.item(row, col).setText('1')
                    else:
                        self.tblInfluences.item(row, col).setText('0')
            det_influence.infl_0 = float(self.tblInfluences.item(row, INFL_0).text())
            det_influence.degrade_infl0 = float(self.tblInfluences.item(row, DEGRAGE_INFL_0).text())
            det_influence.infl_1 = float(self.tblInfluences.item(row, INFL_1).text())
            det_influence.degrade_infl1 = float(self.tblInfluences.item(row, DEGRAGE_INFL_1).text())
            det_influence.infl_2 = float(self.tblInfluences.item(row, INFL_2).text())
            det_influence.degrade_infl2 = float(self.tblInfluences.item(row, DEGRAGE_INFL_2).text())
            det_influence.fixed_smear = float(self.tblInfluences.item(row, FIX_SMEAR).text())
            det_influence.degrade_f_smear = float(self.tblInfluences.item(row, DEGRADE_FIX_SMEAR).text())
            det_influence.linear_smear = float(self.tblInfluences.item(row, LIN_SMEAR).text())
            det_influence.degrade_l_smear = float(self.tblInfluences.item(row, DEGRADE_LIN_SMEAR).text())
            det_influence.influence = influence

        for influenceDelete in self.influencesToDelete:
            #TODO: detector influences are not actually deleted, which is where the table is
            # populated from. This means influences can't really be deleted!
            #TODO #2: We shouldn't delete the scenarios that have the influence associated with
            # it. We should leave the scenario existing.
            for scen in self.session.query(Scenario).filter(Scenario.influences.contains(influenceDelete)).all():
                if influenceDelete.name in [i.name for i in scen.influences]:
                    scen_hash=Scenario.scenario_hash(scen.acq_time, scen.scen_materials, scen.scen_bckg_materials,
                                                     [i for i in scen.influences if i.name != influenceDelete.name])
                    if not self.session.query(Scenario).filter_by(id=scen_hash).first():
                        smats = [ScenarioMaterial(dose=mat.dose, fd_mode=mat.fd_mode,
                                                  material=mat.material) for mat in scen.scen_materials]
                        sback = [ScenarioBackgroundMaterial(dose=mat.dose, fd_mode=mat.fd_mode,
                                                            material=mat.material) for mat in scen.scen_bckg_materials]

                        Scenario(acq_time=scen.acq_time, replication=scen.replication,
                                 scen_materials=smats, scen_bckg_materials=sback,
                                 influences=[i for i in scen.influences if i.name != influenceDelete.name],
                                 scenario_groups=scen.scenario_groups)

                    self.session.delete(scen)
            self.session.delete(influenceDelete)

        self.session.commit()

        if not self.modify_flag:
            for index in sorted(self.tblInfluences.selectionModel().selectedRows()):
                row = index.row()
                col = NAME
                if index.sibling(row, col).data() not in \
                        [self.parent.listInfluences.item(itemnum).text() for
                         itemnum in range(self.parent.listInfluences.count())]:
                    self.parent.listInfluences.addItem(index.sibling(row, col).data())

        return QDialog.accept(self)

