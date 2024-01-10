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
This module handles the base spectra creation dialog
"""
import os
import sys
import csv
from enum import IntEnum, auto

import yaml
from PySide6.QtCore import Slot, Qt, QRegularExpression, QTemporaryDir
from PySide6.QtGui import QRegularExpressionValidator, QDoubleValidator, QColor, QValidator
from PySide6.QtWidgets import QDialog, QFileDialog, QTableWidgetItem, QDialogButtonBox, QItemDelegate, QMessageBox, \
    QLineEdit, QAbstractItemView, QWidget, QTableWidget, QPushButton, QVBoxLayout, QHBoxLayout
from src.rase_settings import RaseSettings
from .pcf_tools import readpcf, PCFtoN42Writer
from .qt_utils import DoubleOrEmptyDelegate
from .ui_generated import ui_create_base_spectra_dialog
from src.spectrum_file_reading import BaseSpectraFormatException
import traceback

from glob import glob

from .base_building_algos import base_output_filename, do_glob, validate_output, default_config, pcf_config, \
    pcf_config_txt


class ColNum(IntEnum):
    folder = 0  # Enforce starting from zero, then go in order
    file = auto()
    specID = auto()
    matID = auto()
    otherID = auto()
    dose = auto()
    flux = auto()
    base_name = auto()
    notes = auto()


class CreateBaseSpectraTableWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.VendorID = ''
        self.ModelID = ''

        self.layout = QVBoxLayout(self)

        self.sourceTable = QTableWidget(self)
        self.sourceTable.setColumnCount(len(ColNum))
        self._dbl_empty_delegate = DoubleOrEmptyDelegate()
        self.sourceTable.setHorizontalHeaderItem(ColNum.folder, QTableWidgetItem("Folder"))
        self.sourceTable.setColumnHidden(ColNum.folder, True)
        self.sourceTable.setHorizontalHeaderItem(ColNum.file, QTableWidgetItem("File"))
        self.sourceTable.setHorizontalHeaderItem(ColNum.matID, QTableWidgetItem("Source ID"))
        self.sourceTable.setHorizontalHeaderItem(ColNum.otherID, QTableWidgetItem("Description"))
        self.sourceTable.setHorizontalHeaderItem(ColNum.dose, QTableWidgetItem("Exposure Rate"))
        self.sourceTable.setItemDelegateForColumn(ColNum.dose, self._dbl_empty_delegate)
        self.sourceTable.horizontalHeaderItem(ColNum.dose).setToolTip("μSv / h")
        self.sourceTable.setHorizontalHeaderItem(ColNum.flux, QTableWidgetItem("Flux"))
        self.sourceTable.setItemDelegateForColumn(ColNum.flux, self._dbl_empty_delegate)
        self.sourceTable.horizontalHeaderItem(ColNum.flux).setToolTip("counts / cm<sup>2</sup> / s")
        self.sourceTable.setHorizontalHeaderItem(ColNum.base_name, QTableWidgetItem("Base Spectrum Name"))
        self.sourceTable.setHorizontalHeaderItem(ColNum.notes, QTableWidgetItem("Notes"))
        self.sourceTable.setHorizontalHeaderItem(ColNum.specID, QTableWidgetItem("#"))
        self.sourceTable.horizontalHeader().setStretchLastSection(True)
        self.sourceTable.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.buttonLayout = QHBoxLayout()
        self.btnSetAsBkg = QPushButton("Set Selected Entry as Background")
        self.btnClearBkgSel = QPushButton("Clear Background Selection")
        self.btnRemoveSrc = QPushButton("Remove Selected Entry")
        self.buttonLayout.addWidget(self.btnSetAsBkg)
        self.buttonLayout.addWidget(self.btnClearBkgSel)
        self.buttonLayout.addWidget(self.btnRemoveSrc)

        self.btnRemoveSrc.clicked.connect(self.delete_selected)
        self.sourceTable.itemChanged.connect(self.update_base_fname)
        self.btnClearBkgSel.clicked.connect(self.clear_background_selection)
        self.btnSetAsBkg.clicked.connect(self.set_row_as_bkg)
        self.sourceTable.itemSelectionChanged.connect(self.activate_SetAsBkg_button)

        self.layout.addWidget(self.sourceTable)
        self.layout.addLayout(self.buttonLayout)

        self.backgroundFileRow = None
        self.unselectedBkgColor = None
        self.btnSetAsBkg.setEnabled(False)

    def initialize_table(self, state):
        self.sourceTable.setColumnHidden(ColNum.specID, state)
        self.sourceTable.setColumnWidth(ColNum.base_name, 150)
        self.sourceTable.setColumnHidden(ColNum.notes, state)

    def set_vendorID_modelID(self, vendorID, modelID):
        self.VendorID = vendorID
        self.ModelID = modelID

    def create_table_row(self, filename, folder, index=1, notes=''):
        """
        Creates one row in 'table' and enters 'filename' at the filename column
        """
        row = self.sourceTable.rowCount()
        self.sourceTable.setRowCount(row + 1)
        self.sourceTable.blockSignals(True)
        for col in range(self.sourceTable.columnCount()):
            label = ""
            if col == ColNum.file:
                label = filename
            if col == ColNum.folder:
                label = folder
            elif col == ColNum.specID:
                label = str(index)
            elif col == ColNum.notes:
                label = notes
            item = QTableWidgetItem(label)
            if col == ColNum.base_name:
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.sourceTable.setItem(row, col, item)
        self.sourceTable.blockSignals(False)
        self.update_base_fname(self.sourceTable.item(row, 0))
        self.set_table_folder_tooltip(self.sourceTable.item(row, 0))
        self.unselectedBkgColor = self.sourceTable.item(row, 0).background()

    def set_table_folder_tooltip(self, item):
        t = item.tableWidget()
        row = item.row()
        t.item(row, ColNum.file).setToolTip(t.item(row, ColNum.folder).text())
        t.item(row, ColNum.file).setFlags(item.flags() & ~Qt.ItemIsEditable)

    @Slot(QTableWidgetItem)
    def update_base_fname(self, item):
        """
        Update the base filename in the table at the same row as 'item'
        """
        t = item.tableWidget()
        row = item.row()
        label = base_output_filename(self.VendorID, self.ModelID,
                                     t.item(row, ColNum.matID).text(), t.item(row, ColNum.otherID).text())
        t.item(row, ColNum.base_name).setText(label)

    def update_base_fname_all(self):
        """
        Recursively update all base filenames in both source and background tables
        """
        for row in range(self.sourceTable.rowCount()):
            self.update_base_fname(self.sourceTable.item(row, 0))

    def delete_selected(self):
        """
        deletes selected rows, updating the reference to the background row
        """
        rows = [r.row() for r in self.sourceTable.selectionModel().selectedRows()]

        shift = 0
        if self.backgroundFileRow in rows:
            self.backgroundFileRow = None
        elif self.backgroundFileRow is not None:
            for r in rows:
                if r < self.backgroundFileRow:
                    shift = shift + 1
            self.backgroundFileRow = self.backgroundFileRow - shift

        rows.sort(reverse=True)
        for r in rows:
            self.sourceTable.removeRow(r)

    def clear_table(self) -> None:
        """
        delete all rows and resets the background row reference
        """
        self.sourceTable.setRowCount(0)
        self.backgroundFileRow = None

    def activate_SetAsBkg_button(self):
        items = self.sourceTable.selectedItems()
        self.btnSetAsBkg.setEnabled(True) if items else self.btnSetAsBkg.setEnabled(False)

    @Slot(bool)
    def set_row_as_bkg(self, checked):
        rows = self.sourceTable.selectionModel().selectedRows()
        if len(rows) > 1:
            QMessageBox.information(self, 'Background File Selection', 'Please select only one row')
            return
        self.clear_background_selection()
        row = rows[0].row()
        for col in range(self.sourceTable.columnCount()):
            self.sourceTable.item(row, col).setBackground(QColor('yellow'))
        self.backgroundFileRow = row

    def clear_background_selection(self):
        if self.backgroundFileRow is not None:
            for col in range(self.sourceTable.columnCount()):
                self.sourceTable.item(self.backgroundFileRow, col).setBackground(self.unselectedBkgColor)
        self.backgroundFileRow = None

    def get_table_data_as_list(self) -> list:
        ''' Returns content of the table as a 2D list of strings'''
        data = []
        for row in range(self.sourceTable.rowCount()):
            row_data = []
            for column in range(self.sourceTable.columnCount()):
                item = self.sourceTable.item(row, column)
                if item is not None:
                    row_data.append(item.text())
                else:
                    row_data.append('')
            data.append(row_data)
        return data

    def handleExport(self, directory):
        """
        exports to CSV
        """
        path = QFileDialog.getSaveFileName(self, 'Save File', directory, 'CSV (*.csv)')
        if path[0]:
            with open(path[0], mode='w', newline='') as stream:
                writer = csv.writer(stream)
                writer.writerow([col.name for col in ColNum])
                data = self.get_table_data_as_list()
                for rowdata in data:
                    writer.writerow(rowdata)

    def validate_table_entries(self) -> bool:
        data = self.get_table_data_as_list()
        if not data:
            return False
        for row in data:
            if not(row[ColNum.dose] or row[ColNum.flux]):
                return False
            if not(row[ColNum.matID]):
                return False
        return True

    def handleImport(self, directory):
        """
        imports from CSV
        """
        path = QFileDialog.getOpenFileName(self, 'Open File', directory, 'CSV(*.csv)')
        if path[0]:
            # FIXME: This doesn't check in any way that the format of the file is correct
            with open(path[0], mode='r') as stream:
                self.sourceTable.setRowCount(0)
                self.sourceTable.blockSignals(True)
                for rowdata in csv.reader(stream):
                    row = self.sourceTable.rowCount()
                    if [col.name for col in ColNum][0] in str(rowdata): continue
                    self.sourceTable.insertRow(row)
                    for column, data in enumerate(rowdata):
                        if column < len(ColNum):
                            item = QTableWidgetItem(data)
                            self.sourceTable.setItem(row, column, item)
                    item = QTableWidgetItem()
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    self.sourceTable.setItem(row, ColNum.base_name, item)
                    self.update_base_fname(self.sourceTable.item(row, 0))
                    self.set_table_folder_tooltip(self.sourceTable.item(row, 0))
                self.sourceTable.blockSignals(False)


class CreateBaseSpectraDialog(ui_create_base_spectra_dialog.Ui_Dialog, QDialog):
    def __init__(self, session):
        QDialog.__init__(self)
        self.setupUi(self)
        self.buttonBox.button(QDialogButtonBox.Ok).setText("Create")
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)

        self.settings = RaseSettings()

        self.txtVendorID.setValidator(QRegularExpressionValidator(QRegularExpression('[a-zA-Z0-9]{0,4}')))
        self.txtModelID.setValidator(QRegularExpressionValidator(QRegularExpression('[a-zA-Z0-9]{0,3}')))

        self.createBSTable = CreateBaseSpectraTableWidget()
        self.verticalLayout_reserved.addWidget(self.createBSTable)

        self.txtVendorID.textChanged.connect(self.createBSTable.update_base_fname_all)
        self.txtModelID.textChanged.connect(self.createBSTable.update_base_fname_all)
        self.btnExport.clicked.connect(lambda: self.createBSTable.handleExport(self.settings.getLastDirectory()))
        self.btnImport.clicked.connect(lambda: self.createBSTable.handleImport(self.settings.getLastDirectory()))

        self.txtConfigFile.setText(self.settings.getBaseSpectrumCreationConfig())
        self.configs = {**default_config, **pcf_config}
        self.comboConfig.currentIndexChanged.connect(self.combo_config_changed)
        self.loadConfigsFromFile()

        self.createBSTable.sourceTable.cellChanged.connect(self.update_Ok_button_state)
        self.txtVendorID.textChanged.connect(self.update_Ok_button_state)
        self.txtModelID.textChanged.connect(self.update_Ok_button_state)
        self.txtOutFolder.textChanged.connect(self.update_Ok_button_state)

    @Slot(bool)
    def on_btnLoadSources_clicked(self, checked):
        """
        Loads source spectra files in the source table
        """
        options = QFileDialog.ShowDirsOnly
        if sys.platform.startswith('win'): options = QFileDialog.DontUseNativeDialog
        path = QFileDialog.getExistingDirectory(self, 'Choose Base Spectra Directory',
                                                self.settings.getLastDirectory(), options)
        if not path:
            return

        if self.comboConfig.currentText() == pcf_config_txt:
            filenames = [f for f in os.listdir(path) if f.lower().endswith(".pcf")]
            if not filenames:
                QMessageBox.critical(self, 'Invalid Directory Selection',
                                     'No PCF Files in selected Directory')
                return

            for f in sorted(filenames):
                for index, spectrum in enumerate(readpcf(os.path.join(path, f))):
                    self.createBSTable.create_table_row(f, path, index+1, spectrum.title)
        else:
            if not self.checkBox_ComboFolder.isChecked():  # normal load
                filenames = [f for f in os.listdir(path) if f.lower().endswith(".n42")]
                if not filenames:
                    QMessageBox.critical(self, 'Invalid Directory Selection',
                                         'No n42 Files in selected Directory')
                    return

                for f in sorted(filenames):
                    # TODO: check that the n42 is sane otherwise skip the file and notify the user
                    self.createBSTable.create_table_row(f, path)
            else:  # Load each subfolder as one source and sum its files
                found_all = True
                bad_dirs = []
                for it in os.scandir(path):
                    if it.is_dir():
                        self.createBSTable.create_table_row(os.path.join(it.name, '*.n42'), path)
                        inputfiles = glob(os.path.join(it.path, '*.n42'))
                        if not bool(inputfiles):
                            found_all = False
                            bad_dirs.append(it.name)

                if not found_all:
                    bad_dir_str = ', '.join(bad_dirs)
                    QMessageBox.critical(self, 'Invalid Directory Selection',
                                         f'Subdirectory(s) {bad_dir_str} does not contain n42 files.')

    @Slot(int)
    def combo_config_changed(self, index):
        state = False if self.comboConfig.currentText() == pcf_config_txt else True
        self.checkBox_ComboFolder.setVisible(state)
        self.checkBox_ComboFolder.setEnabled(state)
        self.createBSTable.initialize_table(state)

    @Slot(bool)
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

    @Slot(bool)
    def on_btnBrowseConfig_clicked(self, checked):
        """
        Selects configuration file
        """
        if sys.platform.startswith('win'): options = QFileDialog.DontUseNativeDialog
        path, __filter = QFileDialog.getOpenFileName(self, 'Choose Config YAML file',
                                                self.settings.getLastDirectory(),'YAML(*.yaml)')

        if path:
            self.txtConfigFile.setText(path)
            self.settings.setBaseSpectrumCreationConfig(path)
            self.loadConfigsFromFile()

    def update_Ok_button_state(self):
        entries_are_valid = self.validate_entries()
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(entries_are_valid)

    def validate_entries(self) -> bool:
        '''Validates that all entries are properly set and enable the "Create" button'''
        # TODO: add text box or tooltip explaining what is missing
        if not (self.txtVendorID.text() and self.txtModelID.text()
                and self.txtOutFolder.text()):
            return False
        return self.createBSTable.validate_table_entries()

    def accept(self):
        # TODO: If there is no background selected, ensure the user know what they are doing?

        configdict = self.configs[self.comboConfig.currentText()]

        if configdict['calibration'] == "Replace this text with your instrument's calibration coefficients.":
            QMessageBox.warning(self, 'Calibration Error', 'Calibration coefficients need to be manually set in '
                                                           'the config file for this instrument.\n\nTo do this, '
                                                           'determine the coefficients of a polynomial calibration '
                                                           'fit using your favorite external tool, and change the '
                                                           'calibration xpath field in the config file for this '
                                                           'instrument to a string of those coefficients '
                                                           '(e.g.: "0 2.998 0"). Then re-select the configuration '
                                                           'file to refresh the field and re-select the desired '
                                                           'instrument from the drop-down configuration menu.')
            return

        pcf = (self.comboConfig.currentText() == pcf_config_txt)
        try:
            create_base_spectra_from_input_data(configdict,
                                                pcf,
                                                self.createBSTable.get_table_data_as_list(),
                                                self.createBSTable.backgroundFileRow,
                                                self.txtOutFolder.text(),
                                                self.txtVendorID.text(),
                                                self.txtModelID.text())
        except BaseSpectraFormatException as e:
            QMessageBox.warning(self, 'Base Spectrum Creation Error', e.args)
            return
        # except BaseSpectraFormatException as e:
        #     QMessageBox.warning(self, 'File Validation Error',
        #                         f'Base spectrum file was created, but the result could not be successfully read. Reading error was: \n{e.args}')
        #     return
        except Exception as e:
            QMessageBox.warning(self, 'Error', str(e) + traceback.format_exc())
            return

        return QDialog.accept(self)

    def loadConfigsFromFile(self):
        self.comboConfig.clear()
        self.configs = {**default_config, **pcf_config}
        file_configs = {}
        if self.txtConfigFile.text() and self.txtConfigFile.text().strip():
            file_configs = load_configs_from_file(self, self.txtConfigFile.text())
            self.configs = {**self.configs, **file_configs}
        self.comboConfig.addItems([key for key in self.configs.keys()])
        if not file_configs:
            self.txtConfigFile.clear()
            self.settings.setBaseSpectrumCreationConfig('')


def create_base_spectra_from_input_data(config_dict: dict, pcf: bool, data: list,
                                        background_file_row: int,
                                        out_folder, vendorID, modelID):

    # replace PCF files with n42 files before processing
    if pcf:
        # get list of PCF files
        pcf_files = set([os.path.join(row[ColNum.folder], row[ColNum.file]) for row in data])

        # for each PDF file create the n42 files and get their location in a map
        pcf_map = {}
        temp_dirs = {pcf_file: QTemporaryDir() for pcf_file in pcf_files}
        if all([temp_dir.isValid() for temp_dir in temp_dirs.values()]):
            for pcf in pcf_files:
                pcf_map[pcf] = PCFtoN42Writer(pcf).generate_n42(temp_dirs[pcf].path())
        else:
            #  TODO: raise error
            pass

        # loop over the table and replace the folder and file details
        for n, row in enumerate(data):
            pcf_file = os.path.join(row[ColNum.folder], row[ColNum.file])
            specid = int(row[ColNum.specID]) - 1
            data[n][ColNum.folder] = temp_dirs[pcf_file].path()
            data[n][ColNum.file] = pcf_map[pcf_file][specid]

    bkg_out_file = None
    if background_file_row is not None:
        # reorder processing so BG is always done first
        bkg_row = data.pop(background_file_row)
        data.insert(0, bkg_row)

        # figure out BG output so it can be used for subtraction
        bkg_out_file = os.path.join(out_folder,
                                    base_output_filename(manufacturer=vendorID,
                                                         model=modelID,
                                                         source=bkg_row[ColNum.matID],
                                                         description=bkg_row[ColNum.otherID]))

    for n, row in enumerate(data):
        in_file = os.path.join(row[ColNum.folder], row[ColNum.file])

        if n == 0:  # first row is background as per above
            subtraction = None
        else:
            # BG subtraction in the GUI is handled by subtracting the output base spectrum file for the background run, rather than the input/raw file
            # This is important for handling cases where the BG "file" is actually a folder of short runs that need to be summed first.
            subtraction = bkg_out_file
            config_dict['subtraction_spectrum_xpath'] = './RadMeasurement[@id="Foreground"]/Spectrum'

        os.makedirs(out_folder, exist_ok=True)

        # TODO: allow to indicate a different "radid" for the background spectrum to be subtracted
        # TODO: should 'containername' be part of the user inputs? Or can we just try default container names?
        for mode in [ColNum.flux, ColNum.dose]:
            if not row[mode]:
                pass
            else:
                row[mode] = float(row[mode])
        try:
            do_glob(inputfileglob=in_file, config=config_dict, outputfolder=out_folder,
                    manufacturer=vendorID, model=modelID, source=row[ColNum.matID],
                    uSievertsph=row[ColNum.dose], fluxValue=row[ColNum.flux],
                    subtraction=subtraction, description=row[ColNum.otherID])

        except BaseSpectraFormatException as e:
            print('Base Spectrum Creation Error', e.args)
            raise
        except Exception as e:
            print('Error', str(e) + traceback.format_exc())
            raise

        try:
            validate_output(outputfolder=out_folder,
                            manufacturer=vendorID, model=modelID,
                            source=row[ColNum.matID],
                            description=row[ColNum.otherID])
        except BaseSpectraFormatException as e:
            print('File Validation Error',
                  f'Base spectrum file was created, but the result could not be successfully read. '
                  f'Reading error was: \n{e.args}')
            raise


def load_configs_from_file(parent, file_path) -> dict:
    file_configs = {}
    try:
        with open(file_path, 'r') as file:
            file_configs = yaml.safe_load(file)
    except yaml.YAMLError as ex:
        QMessageBox.warning(parent, 'Config File Error',
                            f'Config file {file_path} cannot be read. '
                            'Look for YAML format errors.\n' +
                            str(ex))
    except FileNotFoundError:
        QMessageBox.warning(parent, 'Config File Error',
                            'Config file not found. Load a working config file.\n')
    return file_configs
