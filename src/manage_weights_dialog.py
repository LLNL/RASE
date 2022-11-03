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
This module supports import, export and deletion of user defined material weights
"""

import csv

from PySide6.QtWidgets import QDialog, QFileDialog, QTableWidgetItem, QAbstractItemView
from PySide6.QtWidgets import QHeaderView, QMessageBox
from PySide6.QtCore import Slot, Qt

from .table_def import Session, MaterialWeight
from .ui_generated import ui_manage_weights_dialog
from .correspondence_table_dialog import Delegate
from src.rase_settings import RaseSettings

NUM_COL = 4
NAME, TPWF, FPWF, FNWF = range(NUM_COL)
COLUMNS = [NAME, TPWF, FPWF, FNWF]

class ManageWeightsDialog(ui_manage_weights_dialog.Ui_Dialog, QDialog):
    def __init__(self, parent = None):
        QDialog.__init__(self)
        self.parent = parent
        self.session = Session()
        self.settings = RaseSettings()
        self.setupUi(self)
        self.setWeightsTable()
        self.check_usemweights.setChecked(self.settings.getUseMWeightsInCalcs())
        self.check_useconfs.setChecked(self.settings.getUseConfidencesInCalcs())
        self.btnDeleteSelectedMaterials.clicked.connect(self.deleteSelectedMaterials)
        self.buttonExport.clicked.connect(self.handleExport)
        self.buttonImport.clicked.connect(self.handleImport)
        self.btnAddNewMaterial.clicked.connect(self.on_btnNewMaterial_clicked)

        self.setWindowTitle('Modify Material Weights')

        self.materialsToDelete = []


    def setWeightsTable(self):
        materials = list(self.session.query(MaterialWeight))
        if self.tblWeights:
            self.tblWeights.clear()
        self.tblWeights.setItemDelegate(Delegate(self.tblWeights, isotopeCol=NAME))
        self.tblWeights.setColumnCount(NUM_COL)
        self.tblWeights.setRowCount(len(materials))
        self.tblWeights.setHorizontalHeaderLabels(['Material Name',
                                                      'True Positive\nWeighting Factor',
                                                      'False Positive\nWeighting Factor',
                                                      'False Negative\nWeighting Factor'])
        self.tblWeights.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tblWeights.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        row = 0

        for col in COLUMNS[TPWF:]:
            self.tblWeights.setColumnWidth(col, 120)


        for material in materials:
            item = QTableWidgetItem(QTableWidgetItem(material.name))
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled)
            self.tblWeights.setItem(row, NAME, item)
            for (col, weight) in zip(COLUMNS[TPWF:], [str(material.TPWF), str(material.FPWF), str(material.FNWF)]):
                item = QTableWidgetItem(weight)
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled)
                self.tblWeights.setItem(row, col, item)
            row += 1

    def on_btnNewMaterial_clicked(self, checked):
        """
        Adds new influence row that is fully editable
        """
        row = self.tblWeights.rowCount()
        self.tblWeights.insertRow(row)
        union = Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled
        for col in COLUMNS:
            item = QTableWidgetItem()
            item.setFlags(union)
            if col > NAME:
                item.setText('1')
            self.tblWeights.setItem(row, col, item)


    def handleExport(self):
        """
        Exports to CSV
        """
        path = QFileDialog.getSaveFileName(self, 'Save File', self.settings.getDataDirectory(), 'CSV (*.csv)')
        if path[0]:
            with open(path[0], mode='w', newline='') as stream:
                writer = csv.writer(stream)
                for row in range(self.tblWeights.rowCount()):
                    rowdata = []
                    for column in range(self.tblWeights.columnCount()):
                        item = self.tblWeights.item(row, column)
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
                self.tblWeights.setRowCount(0)
                self.tblWeights.setColumnCount(0)
                for rowdata in csv.reader(stream):
                    row = self.tblWeights.rowCount()
                    self.tblWeights.insertRow(row)
                    self.tblWeights.setColumnCount(len(rowdata))
                    for column, data in enumerate(rowdata):
                        item = QTableWidgetItem(data)
                        self.tblWeights.setItem(row, column, item)
            self.tblWeights.setHorizontalHeaderLabels(['Material Name',
                                                      'True Positive\nWeighting Factor',
                                                      'False Positive\nWeighting Factor',
                                                      'False Negative\nWeighting Factor'])

            for col in COLUMNS[TPWF:]:
                self.tblWeights.setColumnWidth(col, 120)

    def deleteSelectedMaterials(self):
        """
        Deletes Selected Influences
        """
        rows = self.tblWeights.selectionModel().selectedRows()
        indices =[]
        for r in rows:
            indices.append(r.row())
        indices.sort(reverse=True)
        for index in indices:
            self.tblWeights.removeRow(index)


    def removeDeletedWeightsFromDB(self):
        session = Session()

        materialsToDelete = []
        prior_mats = list(session.query(MaterialWeight).all())
        current_mats = list(self.tblWeights.item(row, NAME).text() for row in range(self.tblWeights.rowCount()))
        for mat in prior_mats:
            if mat.name not in current_mats:
                materialsToDelete.append(mat)
        for materialDelete in materialsToDelete:
            self.session.delete(materialDelete)

    @Slot()
    def accept(self):
        """
        Closes dialog
        """
        self.settings.setUseConfidencesInCalcs(self.check_useconfs.isChecked())
        self.settings.setUseMWeightsInCalcs(self.check_usemweights.isChecked())

        self.removeDeletedWeightsFromDB()
        names = []

        for row in range(self.tblWeights.rowCount()):
            try:
                for col in COLUMNS[TPWF:]:
                    if not self.tblWeights.item(row, col).text():
                        self.tblWeights.item(row, col).setText('1')
                    float(self.tblWeights.item(row, col).text())
            except:
                return QMessageBox.critical(self, 'Invalid weight value', 'All specified weight values must be numbers')

            if not self.tblWeights.item(row, NAME).text():
                return QMessageBox.critical(self, 'Unnamed Material', 'Material weights must have a name!')
            names.append(self.tblWeights.item(row, NAME).text())

        if len(names) != len(set(names)):
            return QMessageBox.critical(self, 'Repeat material', 'Materials must each have unique names!')

        for row in range(self.tblWeights.rowCount()):

            name = self.tblWeights.item(row, NAME).text()

            material = self.session.query(MaterialWeight).filter_by(name=name).first()
            if not material:
                material = MaterialWeight()
                material.name = name
                self.session.add(material)

            for col in COLUMNS[TPWF:]:
                if not self.tblWeights.item(row, col).text():
                    self.tblWeights.item(row, col).setText('1')
                elif float(self.tblWeights.item(row, col).text()) <= 0:
                    self.tblWeights.item(row, col).setText('0')

            material.TPWF = float(self.tblWeights.item(row, TPWF).text())
            material.FPWF = float(self.tblWeights.item(row, FPWF).text())
            material.FNWF = float(self.tblWeights.item(row, FNWF).text())

        self.session.commit()

        return QDialog.accept(self)

