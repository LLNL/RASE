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
This module defines correct association between isotope names and
replay identification results
"""

import csv

from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtWidgets import QTableWidgetItem, QDialog, QFileDialog, \
     QMessageBox, QHeaderView, QItemDelegate, QComboBox, QMenu, QAction

from src.rase_settings import RaseSettings
from .table_def import CorrespondenceTableElement, CorrespondenceTable, Session, Material
from .ui_generated import ui_correspondence_table_dialog


class CorrespondenceTableDialog(ui_correspondence_table_dialog.Ui_dlgCorrTable, QDialog):
    def __init__(self):
        QDialog.__init__(self)
        self.setupUi(self)
        self.settings = RaseSettings()
        self.NUM_COLS = 3
        self.tableEdited = False
        self.session = Session()
        # self.corTable = None

        # Query the entries in the current default table
        corTableRows = self.readCorrTableRows()
        if not corTableRows:
            self.NUM_ROWS = 0
        else:
            self.NUM_ROWS = corTableRows.count()

        self.tblCCCLists.setItemDelegate(Delegate(self.tblCCCLists, isotopeCol=0))
        self.tblCCCLists.setRowCount(self.NUM_ROWS)
        self.tblCCCLists.setColumnCount(self.NUM_COLS)
        self.columnLabels = ['Source', 'Correct ID', 'Allowed ID']
        self.tblCCCLists.setHorizontalHeaderLabels(self.columnLabels)
        self.tblCCCLists.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tblCCCLists.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tblCCCLists.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tblCCCLists.customContextMenuRequested.connect(self.openMenu)
        self.tblCCCLists.setSortingEnabled(False)

        # for row in range(self.NUM_ROWS):
        #    for col in range(self.NUM_COLS):
        #        self.tblCCCLists.setItem(row, col, QTableWidgetItem())
        if corTableRows:
          for row, line in enumerate(corTableRows):
            # if (row >= self.NUM_ROWS):
            #     self.NUM_ROWS = self.NUM_ROWS + 1
            #     self.tblCCCLists.setRowCount(self.NUM_ROWS)
            #     for col in range(self.NUM_COLS):
            #         self.tblCCCLists.setItem(row, col, QTableWidgetItem())
            self.tblCCCLists.setItem(row, 0, QTableWidgetItem(line.isotope))
            self.tblCCCLists.setItem(row, 1, QTableWidgetItem(line.corrList1))
            self.tblCCCLists.setItem(row, 2, QTableWidgetItem(line.corrList2))


        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        # self.pushButton.clicked.connect(self.addLines)
        self.btnAddRow.clicked.connect(self.addRow)
        self.populateDefaultComboBox()
        self.setSaveAsTableName()

        self.buttonImport.clicked.connect(self.handleImport)
        self.buttonExport.clicked.connect(self.handleExport)

        self.buttonApplyDefaultSetting.clicked.connect(self.applySettings)
        self.btnDeleteSelected.clicked.connect(self.deleteSelected)

        self.btnClose.clicked.connect(self.closeSelected)

    def closeSelected(self):
        """
        closes dialog
        """
        super().accept()

    def deleteSelected(self):
        """
        deletes selected rows
        """
        rows = self.tblCCCLists.selectionModel().selectedRows()
        indices =[]
        for r in rows:
            indices.append(r.row())
        indices.sort(reverse=True)
        for index in indices:
            self.tblCCCLists.removeRow(index)
        self.NUM_ROWS =self.NUM_ROWS - len(indices)

    def setDefaultCorrTable(self, tableName):
        """
        Sets selected table as default
        """
        corrTable = self.session.query(CorrespondenceTable).filter_by(name=tableName).first()
        corrTable.is_default = True
        self.session.commit()

    def applySettings(self):
        """
        Sets selected table as default and loads it for edit
        """
        self.setDefaultCorrTable(self.setDefaultComboBox.currentText())
        self.tblCCCLists.setRowCount(0)
        if not self.readCorrTableRows():
            return
        corTableRows = self.readCorrTableRows()
        row =0
        if corTableRows:
          for line in corTableRows:
            self.NUM_ROWS = row+1
            self.tblCCCLists.setRowCount(self.NUM_ROWS)
            for col in range(self.NUM_COLS):
                self.tblCCCLists.setItem(row, col, QTableWidgetItem())
            self.tblCCCLists.setItem(row, 0, QTableWidgetItem(line.isotope))
            self.tblCCCLists.setItem(row, 1, QTableWidgetItem(line.corrList1))
            self.tblCCCLists.setItem(row, 2, QTableWidgetItem(line.corrList2))
            row = row + 1
        self.setSaveAsTableName()

    def populateDefaultComboBox(self):
        """
        loads available correspondence tables into the selection box
        """
        corrTables = list(self.session.query(CorrespondenceTable))
        for i, table in enumerate(corrTables):
            self.setDefaultComboBox.addItem(table.name)
            if table.is_default:
                self.setDefaultComboBox.setCurrentIndex(i)

    def setSaveAsTableName(self):
        corrTable = self.session.query(CorrespondenceTable).filter_by(is_default=True).one_or_none()
        if corrTable is not None:
            self.txtCorrespondenceTable.setText(corrTable.name)
            self.txtCorrespondenceTable.repaint()

    def readCorrTableRows(self):
        """
        Queries elements of the Default Correspondence Table
        :return: row elements of the correspondence table from DB
        """
        corrTable = self.session.query(CorrespondenceTable).filter_by(is_default=True).one_or_none()
        if corrTable is None:
            return None
        else:
            return self.session.query(CorrespondenceTableElement).filter_by(corr_table_name=corrTable.name)

    def addRow(self):
        """
        adds row to the table in the open dialog
        """
        self.NUM_ROWS = self.NUM_ROWS + 1
        self.tblCCCLists.setRowCount(self.NUM_ROWS)
        for col in range(self.NUM_COLS):
            self.tblCCCLists.setItem(self.NUM_ROWS-1, col, QTableWidgetItem())

    def accept(self):
        table_name = self.txtCorrespondenceTable.text()
        if table_name == "":
            QMessageBox.information(self, 'Correspondence Table Name Needed',
                                    'Please Specify New Table Name')
            return

        corrTable = self.session.query(CorrespondenceTable).filter_by(name=table_name).one_or_none()
        if corrTable is not None:
            # table already exists, so delete first before overwriting
            self.session.query(CorrespondenceTableElement).filter_by(
                corr_table_name=self.txtCorrespondenceTable.text()).delete()
            self.session.delete(corrTable)
            self.session.commit()

        table = CorrespondenceTable(name=table_name, is_default=True)
        self.session.add(table)
        for row in range(self.NUM_ROWS):
            iso = self.tblCCCLists.item(row, 0).text()
            l1 = self.tblCCCLists.item(row, 1).text()
            l2 = self.tblCCCLists.item(row, 2).text()
            if iso != '':
                corrTsbleEntry = CorrespondenceTableElement(isotope=iso, corrList1=l1, corrList2=l2)
                table.corr_table_elements.append(corrTsbleEntry)
            else:
                break
        self.session.commit()
        super().accept()

    def handleExport(self):
        """
        exports to CSV
        """
        path = QFileDialog.getSaveFileName(self, 'Save File', self.settings.getDataDirectory(), 'CSV (*.csv)')
        if path[0]:
            with open(path[0], mode='w', newline='') as stream:
                writer = csv.writer(stream)
                writer.writerow(self.columnLabels)
                for row in range(self.tblCCCLists.rowCount()):
                    rowdata = []
                    for column in range(self.tblCCCLists.columnCount()):
                        item = self.tblCCCLists.item(row, column)
                        if item is not None:
                            rowdata.append(item.text())
                        else:
                            rowdata.append('')
                    writer.writerow(rowdata)

    def handleImport(self):
        """
        imports from CSV
        """
        path = QFileDialog.getOpenFileName(self, 'Open File', self.settings.getDataDirectory(), 'CSV(*.csv)')
        if path[0]:
            # FIXME: This doesn't check in any way that the format of the file is correct
            with open(path[0], mode='r') as stream:
                self.tblCCCLists.setRowCount(0)
                self.tblCCCLists.setColumnCount(0)
                for rowdata in csv.reader(stream):
                    row = self.tblCCCLists.rowCount()
                    if 'Correct ID' in str(rowdata):
                        continue
                    self.tblCCCLists.insertRow(row)
                    self.tblCCCLists.setColumnCount(len(rowdata))
                    for column, data in enumerate(rowdata):
                        item = QTableWidgetItem(data)
                        self.tblCCCLists.setItem(row, column, item)
            self.tblCCCLists.setHorizontalHeaderLabels(self.columnLabels)
            self.tblCCCLists.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
            self.tblCCCLists.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
            self.NUM_ROWS = self.tblCCCLists.rowCount()

    @pyqtSlot(QTableWidgetItem)
    def on_tblCCCLists_itemChanged(self, item):
        """
        Listener for changes to the table
        """
        self.tableEdited = True

    def openMenu(self, point):
        """
        Adds sorting to the table
        """
        sortAction = QAction('Sort', self)
        menu = QMenu(self.tblCCCLists)
        menu.addAction(sortAction)
        action = menu.exec_(self.tblCCCLists.mapToGlobal(point))
        if action == sortAction:
            sortingCol = self.tblCCCLists.currentColumn()
            sortingList = []
            rowMap = {}
            for row in range(self.NUM_ROWS):
                if self.tblCCCLists.item(row,0).text() == "":
                    continue
                rowMapItem = {}
                for col in range(self.NUM_COLS):
                    if col != sortingCol:
                        rowMapItem[col] = self.tblCCCLists.item(row,col).text()
                rowMap[self.tblCCCLists.item(row,sortingCol).text()] = rowMapItem
                sortingList.append(self.tblCCCLists.item(row,sortingCol).text())
            sortingList.sort()
            row = 0
            for token in sortingList:
                rowMapItem = rowMap[token]
                for col in rowMapItem:
                    self.tblCCCLists.setItem(row, col, QTableWidgetItem(rowMapItem[col]))
                self.tblCCCLists.setItem(row, sortingCol, QTableWidgetItem(token))
                row = row + 1


class Delegate(QItemDelegate):
    def __init__(self, tblCorr, isotopeCol, editable=False):
        QItemDelegate.__init__(self)
        self.tblCorr = tblCorr
        self.isotopeCol = isotopeCol
        self.editable = editable

    def createEditor(self, parent, option, index):
        if index.column() == self.isotopeCol:
            # generate list of unique material names
            materialList = sorted(set([name for material in Session().query(Material) for name in material.name_no_shielding()]))

            # remove any materials already used
            for row in range(self.tblCorr.rowCount()):
                item = self.tblCorr.item(row, self.isotopeCol)
                if item and item.text() in materialList:
                    materialList.remove(item.text())

            #create and populate comboEdit
            comboEdit = QComboBox(parent)
            comboEdit.setEditable(self.editable)
            comboEdit.addItem('')
            comboEdit.addItems(materialList)
            return comboEdit
        else:
            return super(Delegate, self).createEditor(parent, option, index)
