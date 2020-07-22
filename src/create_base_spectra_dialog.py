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
This module handles the base spectra creation dialog
"""

import os
import sys
import csv

from PyQt5.QtCore import pyqtSlot, Qt, QRegExp
from PyQt5.QtGui import QRegExpValidator, QDoubleValidator, QColor
from PyQt5.QtWidgets import QDialog, QFileDialog, QTableWidgetItem, QDialogButtonBox, QItemDelegate, QMessageBox, \
    QLineEdit, QAbstractItemView

from .ui_generated import ui_create_base_spectra_dialog

from .base_building_algos import base_output_filename, do_all

hh = {'folder': 0, 'file': 1, 'matID': 2, 'otherID': 3, 'dose': 4, 'base_name': 5,}


class CreateBaseSpectraDialog(ui_create_base_spectra_dialog.Ui_Dialog, QDialog):
    def __init__(self, session, settings):
        QDialog.__init__(self)
        self.setupUi(self)
        self.buttonBox.addButton("Create", QDialogButtonBox.AcceptRole)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.settings = settings

        self.sourceTable.setItemDelegateForColumn(hh['dose'], PositiveDoubleDelegate())
        self.sourceTable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.sourceTable.setColumnHidden(hh['folder'], True)    # folder is hidden but shown as tooltip on filename cell

        self.txtVendorID.setValidator(QRegExpValidator(QRegExp('[a-zA-Z0-9]{0,4}')))
        self.txtModelID.setValidator(QRegExpValidator(QRegExp('[a-zA-Z0-9]{0,3}')))

        self.btnRemoveSrc.clicked.connect(self.delete_selected)
        self.sourceTable.itemChanged.connect(self.update_base_fname)
        self.txtVendorID.textChanged.connect(self.update_base_fname_all)
        self.txtModelID.textChanged.connect(self.update_base_fname_all)
        self.btnExport.clicked.connect(self.handleExport)
        self.btnImport.clicked.connect(self.handleImport)
        self.btnClearBkgSel.clicked.connect(self.clear_background_selection)
        self.sourceTable.itemSelectionChanged.connect(self.activate_SetAsBkg_button)

        self.backgroundFileName = None
        self.backgroundFileFolder = None
        self.unselectedBkgColor = None
        self.btnSetAsBkg.setEnabled(False)

    def create_table_row(self, table, filename, dir):
        """
        Creates one row in 'table' and enters 'filename' at the filename column
        """
        row = table.rowCount()
        table.setRowCount(row + 1)
        table.blockSignals(True)
        for col in range(table.columnCount()):
            label = ""
            if col == hh['file']:
                label = filename
            if col == hh['folder']:
                label = dir
            item = QTableWidgetItem(label)
            if col == hh['base_name']:
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            table.setItem(row, col, item)
        table.blockSignals(False)
        self.update_base_fname(table.item(row, 0))
        self.set_table_folder_tooltip(table.item(row, 0))
        self.unselectedBkgColor = table.item(row, 0).background()

    def set_table_folder_tooltip(self, item):
        t = item.tableWidget()
        row = item.row()
        t.item(row, hh["file"]).setToolTip(t.item(row, hh['folder']).text())
        t.item(row, hh["file"]).setFlags(item.flags() & ~Qt.ItemIsEditable)

    @pyqtSlot(bool)
    def on_btnLoadSources_clicked(self, checked):
        """
        Loads source spectra files in the source table
        """
        options = QFileDialog.ShowDirsOnly
        if sys.platform.startswith('win'): options = QFileDialog.DontUseNativeDialog
        path = QFileDialog.getExistingDirectory(self, 'Choose Base Spectra Directory',
                                                self.settings.getLastDirectory(),  options)
        if path:
            filenames = [f for f in os.listdir(path) if f.lower().endswith(".n42")]
            if not filenames:
                QMessageBox.critical(self, 'Invalid Directory Selection',
                                     'No n42 Files in selected Directory')
                return

            for f in sorted(filenames):
                # TODO: check that the n42 is sane otherwise skip the file and notify the user
                self.create_table_row(self.sourceTable, f, path)

    @pyqtSlot(QTableWidgetItem)
    def update_base_fname(self, item):
        """
        Update the base filename in the table at the same row as 'item'
        """
        t = item.tableWidget()
        row = item.row()
        label = base_output_filename(self.txtVendorID.text(), self.txtModelID.text(),
                                     t.item(row, hh['matID']).text(), t.item(row, hh['otherID']).text())
        t.item(row, hh["base_name"]).setText(label)

    def update_base_fname_all(self):
        """
        Recursively update all base filenames in both source and background tables
        """
        for row in range(self.sourceTable.rowCount()):
            self.update_base_fname(self.sourceTable.item(row, 0))

    def delete_selected(self):
        """
        deletes selected rows
        """
        rows = self.sourceTable.selectionModel().selectedRows()
        indices = []
        for r in rows:
            indices.append(r.row())
        indices.sort(reverse=True)
        for index in indices:
            if self.sourceTable.item(index, hh['file']).text() == self.backgroundFileName:
                self.backgroundFileName = None
                self.backgroundFileFolder = None
            self.sourceTable.removeRow(index)
        print(self.backgroundFileName)

    @pyqtSlot(bool)
    def on_btnOutFolder_clicked(self, checked):
        """
        Loads source spectra files in the source table
        """
        options = QFileDialog.ShowDirsOnly
        if sys.platform.startswith('win'): options = QFileDialog.DontUseNativeDialog
        path = QFileDialog.getExistingDirectory(self, 'Choose Base Spectra Directory',
                                                self.settings.getLastDirectory(), options)

        if path:
            self.txtOutFolder.setText(path)

    def activate_SetAsBkg_button(self):
        items = self.sourceTable.selectedItems()
        self.btnSetAsBkg.setEnabled(True) if items else self.btnSetAsBkg.setEnabled(False)

    @pyqtSlot(bool)
    def on_btnSetAsBkg_clicked(self, checked):
        rows = self.sourceTable.selectionModel().selectedRows()
        if len(rows) > 1:
            QMessageBox.information(self, 'Background File Selection', 'Please select only one row')
            return
        self.clear_background_selection()
        row = rows[0].row()
        for col in range(self.sourceTable.columnCount()):
            self.sourceTable.item(row, col).setBackground(QColor('yellow'))
        self.backgroundFileName = self.sourceTable.item(row, hh['file']).text()
        self.backgroundFileFolder = self.sourceTable.item(row, hh['folder']).text()

    def clear_background_selection(self):
        if self.backgroundFileName:
            items = self.sourceTable.findItems(self.backgroundFileName, Qt.MatchExactly)
            for col in range(self.sourceTable.columnCount()):
                self.sourceTable.item(items[0].row(), col).setBackground(self.unselectedBkgColor)
            self.backgroundFileName = None
            self.backgroundFileFolder = None

    def handleExport(self):
        """
        exports to CSV
        """
        path = QFileDialog.getSaveFileName(self, 'Save File', self.settings.getLastDirectory(), 'CSV (*.csv)')
        if path[0]:
            with open(path[0], mode='w', newline='') as stream:
                writer = csv.writer(stream)
                writer.writerow(list(hh.keys())[:-1])
                for row in range(self.sourceTable.rowCount()):
                    rowdata = []
                    for column in range(self.sourceTable.columnCount()-1):
                        item = self.sourceTable.item(row, column)
                        if item is not None:
                            rowdata.append(item.text())
                        else:
                            rowdata.append('')
                    writer.writerow(rowdata)

    def handleImport(self):
        """
        imports from CSV
        """
        path = QFileDialog.getOpenFileName(self, 'Open File', self.settings.getLastDirectory(), 'CSV(*.csv)')
        if path[0]:
            # FIXME: This doesn't check in any way that the format of the file is correct
            with open(path[0], mode='r') as stream:
                self.sourceTable.setRowCount(0)
                self.sourceTable.blockSignals(True)
                for rowdata in csv.reader(stream):
                    row = self.sourceTable.rowCount()
                    if list(hh.keys())[0] in str(rowdata): continue
                    self.sourceTable.insertRow(row)
                    for column, data in enumerate(rowdata):
                        if column < len(hh):
                            item = QTableWidgetItem(data)
                            self.sourceTable.setItem(row, column, item)
                    item = QTableWidgetItem()
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    self.sourceTable.setItem(row, hh['base_name'], item)
                    self.update_base_fname(self.sourceTable.item(row, 0))
                    self.set_table_folder_tooltip(self.sourceTable.item(row, 0))
                self.sourceTable.blockSignals(False)

    def accept(self):
        # TODO: If there is no background selected, ensure the user know what they are doing?

        # check presence of required inputs
        missing_msg = ""
        if not self.txtOutFolder.text():
            missing_msg += " - Output Folder\n"
        if not self.txtVendorID.text():
            missing_msg += " - Vendor ID\n"
        if not self.txtModelID.text():
            missing_msg += " - Model ID\n"
        if missing_msg:
            QMessageBox.warning(self, 'Missing required inputs',
                                'Please specify the following required inputs:\n' + missing_msg)
            return

        v = {}
        for row in range(self.sourceTable.rowCount()):
            for col in hh.keys():
                item = self.sourceTable.item(row, hh[col])
                v[col] = item.text() if item is not None else ''

            in_file = os.path.join(v['folder'], v['file'])
            # If this is the background spectrum, don't do background subtraction
            if self.backgroundFileName and v['file'] != self.backgroundFileName:
                bkg_file = os.path.join(self.backgroundFileFolder, self.backgroundFileName)
            else:
                bkg_file = None

            os.makedirs(self.txtOutFolder.text(), exist_ok=True)

            # TODO: allow to indicate a different "radid" for the background spectrum to be subtracted
            # TODO: should 'containername' be part of the user inputs? Or can we just try default container names?
            radid = self.txtSpectrumTag.text() or None
            do_all(inputfile=in_file, radid=radid, outputfolder=self.txtOutFolder.text(),
                   manufacturer=self.txtVendorID.text(), model=self.txtModelID.text(), source=v['matID'],
                   uSievertsph=float(v['dose']), subtraction=bkg_file, subtraction_radid=radid,
                   description=v['otherID'], containername='RadMeasurement')

        return QDialog.accept(self)


class PositiveDoubleDelegate(QItemDelegate):
    def __init__(self):
        QItemDelegate.__init__(self)

    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setValidator(QDoubleValidator(bottom=1.0e-6))
        return editor
