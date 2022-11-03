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
This module handles the base spectra creation dialog
"""
import os
import sys
import csv
import yaml
from PySide6.QtCore import Slot, Qt, QRegularExpression, QTemporaryDir
from PySide6.QtGui import QRegularExpressionValidator, QDoubleValidator, QColor, QValidator
from PySide6.QtWidgets import QDialog, QFileDialog, QTableWidgetItem, QDialogButtonBox, QItemDelegate, QMessageBox, \
    QLineEdit, QAbstractItemView
from src.rase_settings import RaseSettings
from .pcf_tools import readpcf, PCFtoN42Writer
from .ui_generated import ui_create_base_spectra_dialog
from src.rase_functions import BaseSpectraFormatException
import traceback

from glob import glob

from .base_building_algos import base_output_filename, do_all, do_glob, validate_output

hh = {'folder': 0, 'file': 1, 'specID': 2, 'matID': 3, 'otherID': 4, 'dose': 5, 'flux': 6, 'base_name': 7, 'notes': 8}

pcf_config_txt = 'PCF File'
default_config = {
    'default n42':
        {
            'measurement_spectrum_xpath': './RadMeasurement[MeasurementClassCode="Foreground"]/Spectrum',
            'realtime_xpath': './RadMeasurement[MeasurementClassCode="Foreground"]/RealTimeDuration',
            'livetime_xpath': './RadMeasurement[MeasurementClassCode="Foreground"]/Spectrum/LiveTimeDuration',
            'calibration': './EnergyCalibration/CoefficientValues',
            'subtraction_spectrum_xpath': './RadMeasurement[@id="Foreground"]/Spectrum',
            'additionals': ['./RadMeasurement[MeasurementClassCode="Background"]',
                            './RadMeasurement[MeasurementClassCode="IntrinsicActivity"]'
                            ]
        },
    pcf_config_txt:     # We will translate PCF files into n42s
        {
            'measurement_spectrum_xpath': './RadMeasurement/Spectrum',
            'realtime_xpath': './RadMeasurement/Spectrum/RealTimeDuration',
            'livetime_xpath': './RadMeasurement/Spectrum/LiveTimeDuration',
            'calibration': './EnergyCalibration/CoefficientValues',
            'subtraction_spectrum_xpath': './RadMeasurement/Spectrum',
        }
}


class CreateBaseSpectraDialog(ui_create_base_spectra_dialog.Ui_Dialog, QDialog):
    def __init__(self, session):
        QDialog.__init__(self)
        self.setupUi(self)
        self.buttonBox.addButton("Create", QDialogButtonBox.AcceptRole)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.settings = RaseSettings()

        # TODO: Add a delegate to the flux column as well; doing so now via a simple copy and paste operation is
        #  creating a SIGSEGV
        self._dbl_empty_delegate = DoubleOrEmptyDelegate()
        self.sourceTable.setItemDelegateForColumn(hh['dose'], self._dbl_empty_delegate)
        self.sourceTable.horizontalHeaderItem(hh['dose']).setToolTip("μSv / h")
        self.sourceTable.setItemDelegateForColumn(hh['flux'], self._dbl_empty_delegate)
        self.sourceTable.horizontalHeaderItem(hh['flux']).setToolTip("counts / cm<sup>2</sup> / s")
        self.sourceTable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.sourceTable.setColumnHidden(hh['folder'], True)  # folder is hidden but shown as tooltip on filename cell

        self.txtVendorID.setValidator(QRegularExpressionValidator(QRegularExpression('[a-zA-Z0-9]{0,4}')))
        self.txtModelID.setValidator(QRegularExpressionValidator(QRegularExpression('[a-zA-Z0-9]{0,3}')))

        self.btnRemoveSrc.clicked.connect(self.delete_selected)
        self.sourceTable.itemChanged.connect(self.update_base_fname)
        self.txtVendorID.textChanged.connect(self.update_base_fname_all)
        self.txtModelID.textChanged.connect(self.update_base_fname_all)
        self.btnExport.clicked.connect(self.handleExport)
        self.btnImport.clicked.connect(self.handleImport)
        self.btnClearBkgSel.clicked.connect(self.clear_background_selection)
        self.sourceTable.itemSelectionChanged.connect(self.activate_SetAsBkg_button)

        self.txtConfigFile.setText(self.settings.getBaseSpectrumCreationConfig())
        self.configs = default_config
        self.default_config = default_config
        self.comboConfig.currentIndexChanged.connect(self.combo_config_changed)
        self.loadConfigsFromFile()

        self.backgroundFileRow = None
        self.unselectedBkgColor = None
        self.btnSetAsBkg.setEnabled(False)

    def create_table_row(self, table, filename, folder, index=1, notes=''):
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
                label = folder
            elif col == hh['specID']:
                label = str(index)
            elif col == hh['notes']:
                label = notes
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
                    self.create_table_row(self.sourceTable, f, path, index+1, spectrum.title)
        else:
            if not self.checkBox_ComboFolder.isChecked():  # normal load
                filenames = [f for f in os.listdir(path) if f.lower().endswith(".n42")]
                if not filenames:
                    QMessageBox.critical(self, 'Invalid Directory Selection',
                                         'No n42 Files in selected Directory')
                    return

                for f in sorted(filenames):
                    # TODO: check that the n42 is sane otherwise skip the file and notify the user
                    self.create_table_row(self.sourceTable, f, path)
            else:  # Load each subfolder as one source and sum its files
                found_all = True
                bad_dirs = []
                for it in os.scandir(path):
                    if it.is_dir():
                        self.create_table_row(self.sourceTable, os.path.join(it.name, '*.n42'), path)
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
        self.sourceTable.setColumnHidden(hh['specID'], state)
        self.sourceTable.setColumnWidth(hh['base_name'], 150)
        self.sourceTable.setColumnHidden(hh['notes'], state)

    @Slot(QTableWidgetItem)
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

    def activate_SetAsBkg_button(self):
        items = self.sourceTable.selectedItems()
        self.btnSetAsBkg.setEnabled(True) if items else self.btnSetAsBkg.setEnabled(False)

    @Slot(bool)
    def on_btnSetAsBkg_clicked(self, checked):
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
                    for column in range(self.sourceTable.columnCount() - 1):
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

        v = {}
        throw_err = False

        # replace PCF files with n42 files before processing
        if self.comboConfig.currentText() == pcf_config_txt:
            # get list of PCF files
            pcf_files = set(
                [os.path.join(self.sourceTable.item(row, hh['folder']).text(), self.sourceTable.item(row, hh['file']).text())
                 for row in range(self.sourceTable.rowCount())])

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
            for row in range(self.sourceTable.rowCount()):
                pcf_file = os.path.join(self.sourceTable.item(row, hh['folder']).text(),
                                        self.sourceTable.item(row, hh['file']).text())
                specid = int(self.sourceTable.item(row, hh['specID']).text()) - 1
                self.sourceTable.item(row, hh['folder']).setText(temp_dirs[pcf_file].path())
                self.sourceTable.item(row, hh['file']).setText(pcf_map[pcf_file][specid])

        rows_to_run = list(range(self.sourceTable.rowCount()))
        bkg_out_file = None
        if self.backgroundFileRow is not None:
            # reorder processing so BG is always done first & figure out BG output so it can be used for subtraction
            rows_to_run.insert(0, rows_to_run.pop(self.backgroundFileRow))
            bgv={}
            for col in hh.keys():
                bgitem = self.sourceTable.item(self.backgroundFileRow, hh[col])
                bgv[col] = bgitem.text() if bgitem is not None else ''
            bkg_out_file = os.path.join(self.txtOutFolder.text(),
                                   base_output_filename(manufacturer=self.txtVendorID.text(), model=self.txtModelID.text(),
                                                        source=bgv['matID'], description=bgv['otherID']))
            print(bkg_out_file)

        for row in rows_to_run:
            for col in hh.keys():
                item = self.sourceTable.item(row, hh[col])
                v[col] = item.text() if item is not None else ''

            in_file = os.path.join(v['folder'], v['file'])
            # If this is the background spectrum, don't do background subtraction

            if row == rows_to_run[0]:
                subtraction=None

            else:
                #BG subtraction in the GUI is handled by subtracting the output base spectrum file for the background run, rather than the input/raw file
                #This is important for handling cases where the BG "file" is actually a folder of short runs that need to be summed first.
                subtraction = bkg_out_file
                configdict['subtraction_spectrum_xpath']='./RadMeasurement[@id="Foreground"]/Spectrum'

            os.makedirs(self.txtOutFolder.text(), exist_ok=True)

            # TODO: allow to indicate a different "radid" for the background spectrum to be subtracted
            # TODO: should 'containername' be part of the user inputs? Or can we just try default container names?
            for mode in ['flux', 'dose']:
                if not v[mode]:
                    pass
                else:
                    v[mode] = float(v[mode])
            try:
                do_glob(inputfileglob=in_file, config=configdict, outputfolder=self.txtOutFolder.text(),
                    manufacturer=self.txtVendorID.text(), model=self.txtModelID.text(), source=v['matID'],
                    uSievertsph=v['dose'], fluxValue=v['flux'], subtraction=subtraction,
                    description=v['otherID'])

                # TODO:  load the created file, so we can check if it was made acceptably.
            except BaseSpectraFormatException as e:
                QMessageBox.warning(self, 'Base Spectrum Creation Error', e.args   )
                return
            except Exception as e:
                QMessageBox.warning(self, 'Error', str(e) + traceback.format_exc())
                return

            try:
                validate_output(outputfolder=self.txtOutFolder.text(),
                    manufacturer=self.txtVendorID.text(), model=self.txtModelID.text(), source=v['matID'],description=v['otherID'])
            except BaseSpectraFormatException as e:
                QMessageBox.warning(self, 'File Validation Error', f'Base spectrum file was created, but the result could not be successfully read. Reading error was: \n{e.args}')
                return

            if not (v['dose'] or v['flux']):
                throw_err = True

        if throw_err:
            QMessageBox.warning(self, 'No Exposure Rate or Flux defined',
                                'At least one spectrum has neither an exposure rate or flux defined.\n' +
                                'RASE_sensitivity and FLUX_sensitivity are both set to 1 for said spectrum/spectra.')

        return QDialog.accept(self)

    def loadConfigsFromFile(self):
        self.comboConfig.clear()
        self.configs = self.default_config
        self.comboConfig.addItems([key for key in self.configs.keys()])
        try:
            with open(self.txtConfigFile.text(),'r') as file:
                fileconfigs = yaml.safe_load(file)
                self.configs = {**self.configs, **fileconfigs}

            self.comboConfig.addItems([key for key in fileconfigs.keys()])
        except yaml.YAMLError as ex:
            QMessageBox.warning(self, 'Config File Error',
                                'Config file cannot be read. Look for YAML format errors.\n' +
                                str(ex))
            self.txtConfigFile.clear()
            self.settings.setBaseSpectrumCreationConfig('')
        except FileNotFoundError:
            if self.txtConfigFile.text() and self.txtConfigFile.text().strip(): #only warn if config file box isn't empty
                QMessageBox.warning(self, 'Config File Error',
                                    'Config file not found. Load a working config file.\n')


class DoubleOrEmptyDelegate(QItemDelegate):
    def __init__(self):
        QItemDelegate.__init__(self)

    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setValidator(DoubleAndEmptyValidator(bottom=0))
        return editor

class DoubleAndEmptyValidator(QDoubleValidator):
    """
    Validate double values or empty string.
    """

    def validate(self, inputText, pos):
        """
        Reimplemented from `QDoubleValidator.validate`.
        Allow to provide an empty value.
        :param str inputText: Text to validate
        :param int pos: Position of the cursor
        """
        if inputText.strip() == "":
            # python API is not the same as C++ one
            return QValidator.Acceptable, inputText, pos
        return super(DoubleAndEmptyValidator, self).validate(inputText, pos)

    def toValue(self, text):
        """Convert the input string into an interpreted value
        :param str text: Input string
        :rtype: Tuple[object,bool]
        :returns: A tuple containing the resulting object and True if the
            string is valid
        """
        if text.strip() == "":
            return None, True
        value, validated = self.locale().toDouble(text)
        return value, validated

    def toText(self, value):
        """Convert the input string into an interpreted value
        :param object value: Input object
        :rtype: str
        """
        if value is None:
            return ""
        return str(value)
