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
import os.path
import sys
import traceback
from enum import IntEnum, auto
from glob import glob

import yaml
from PySide6.QtCore import QRegularExpression, Slot
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtWidgets import QLineEdit, QWizard, QWizardPage, QVBoxLayout, QLabel, QFormLayout, QRadioButton, \
    QComboBox, QPushButton, QListWidget, QCheckBox, QPlainTextEdit, QMessageBox, QFileDialog

from src.base_building_algos import default_config, pcf_config, pcf_config_txt
from src.create_base_spectra_dialog import CreateBaseSpectraTableWidget, load_configs_from_file, \
    create_base_spectra_from_input_data
from src.pcf_tools import readpcf
from src.spectrum_file_reading import BaseSpectraFormatException
from src.rase_settings import RaseSettings, BASE_SPECTRUM_CREATION_CONFIG_DEFAULT
from src.utils import natural_keys, get_bundle_dir


class IntroPage(QWizardPage):
    def __init__(self):
        QWizardPage.__init__(self)
        self.layout = QFormLayout(self)

        self.setWindowTitle("Base Spectra Creation Wizard")
        self.setTitle("Base Spectra Creation Wizard")
        self.setSubTitle("Welcome to the base spectra creation wizard! \n\n "
                         "Please enter the vendor name and the model of the instrument.")

        self.txtVendorID = QLineEdit(self)
        self.lblVendorID = QLabel("Vendor ID")
        self.txtModelID = QLineEdit(self)
        self.lblModelID = QLabel("Instrument Model")
        self.txtVendorID.setValidator(QRegularExpressionValidator(QRegularExpression('[a-zA-Z0-9]{0,10}')))
        self.txtModelID.setValidator(QRegularExpressionValidator(QRegularExpression('[a-zA-Z0-9]{0,10}')))

        self.layout.setWidget(0, QFormLayout.LabelRole, self.lblVendorID)
        self.layout.setWidget(0, QFormLayout.FieldRole, self.txtVendorID)
        self.layout.setWidget(1, QFormLayout.LabelRole, self.lblModelID)
        self.layout.setWidget(1, QFormLayout.FieldRole, self.txtModelID)

        self.registerField('VendorID*', self.txtVendorID)
        self.registerField('ModelID*', self.txtModelID)

    def nextId(self):
        return Pages.method


class MethodPage(QWizardPage):
    def __init__(self):
        QWizardPage.__init__(self)
        self.layout = QVBoxLayout(self)

        self.setWindowTitle("Base Spectra Creation Wizard")
        self.setTitle("Source for Base Spectra")
        self.setSubTitle("RASE can generate base spectra from different input files. \n"
                         "Please select among the following: ")

        self.n42Radio = QRadioButton("n42 files of experimental or simulated data")
        self.n42Radio.setChecked(True)
        self.pcfRadio = QRadioButton("PCF files from GADRAS")
        self.gadrasRadio = QRadioButton("Generate directly with GADRAS")
        self.gadrasRadio.setEnabled(False)

        self.layout.addWidget(self.n42Radio)
        self.layout.addWidget(self.pcfRadio)
        self.layout.addWidget(self.gadrasRadio)

    def nextId(self):
        if self.n42Radio.isChecked():
            self.wizard().file_type = 'n42'
            return Pages.n42Format
        elif self.pcfRadio.isChecked():
            self.wizard().file_type = 'PCF'
            self.wizard().n42_config_dict = pcf_config[pcf_config_txt]  # PCF files are later converted to n42s
            return Pages.PCFLoad
        else:
            self.wizard().file_type = 'GADRAS'
            pass


class n42FormatPage(QWizardPage):
    def __init__(self):
        QWizardPage.__init__(self)
        self.layout = QVBoxLayout(self)

        self.setWindowTitle("Base Spectra Creation Wizard")
        self.setTitle("n42 Format Selection")
        self.setSubTitle("Please select the format from the dropdown menu. \n\n"
                         "RASE has built-in capabilities to process generic n42 files as well as "
                         "custom formats for some instruments. \n\n"
                         "Previously created user-defined custom formats are saved "
                         "in a config file in RASE application path and pre-loaded here too. \n\n"
                         "If you need to define a new custom format, select \"Other\" ")

        self.configs = default_config
        self.comboConfig = QComboBox(self)
        self.comboConfig.currentIndexChanged.connect(self.combo_config_changed)
        self.layout.addWidget(self.comboConfig)

    def initializePage(self):
        if not self.comboConfig.count():  # no need for this if reloading after `back button`
            self.configs = default_config
            if os.path.isfile(self.wizard().user_config_file):
                file_configs = load_configs_from_file(self, self.wizard().user_config_file)
                self.configs = {**self.configs, **file_configs}
            self.comboConfig.addItems([key for key in self.configs.keys()] + ['Other'])

    @Slot(int)
    def combo_config_changed(self, index):
        # This variable is stored directly in the wizard class
        if self.comboConfig.currentText() != 'Other':
            self.wizard().n42_config_dict = self.configs[self.comboConfig.currentText()]

    def nextId(self) -> int:
        if self.comboConfig.currentText() == 'Other':
            return Pages.customFormat
        else:
            return Pages.n42Load


class CustomFormatPage(QWizardPage):
    def __init__(self):
        QWizardPage.__init__(self)
        self.layout = QVBoxLayout(self)

        self.setWindowTitle("Base Spectra Creation Wizard")
        self.setTitle("Specify Custom n42 Format")
        self.setSubTitle("Please enter the custom n42 format as YAML \n"
                         "See the RASE manual for details on the YAML format ")

        self.txtEditor = QPlainTextEdit()
        # use the first entry in default_config as placeholder
        tmp_dict = {'Example n42 parser': default_config[next(iter(default_config))]}
        self.txtEditor.setPlaceholderText(yaml.dump(tmp_dict))
        self.txtEditor.textChanged.connect(lambda: self.completeChanged.emit())
        self.chkBox_saveformat = QCheckBox("Save custom format for future use")
        self.layout.addWidget(self.txtEditor)
        self.layout.addWidget(self.chkBox_saveformat)

    def isComplete(self) -> bool:
        # condition for proceeding is that the text is not empty
        return bool(self.txtEditor.toPlainText().strip())

    def validatePage(self) -> bool:
        try:
            custom_config = yaml.safe_load(self.txtEditor.toPlainText().strip())
        except yaml.YAMLError as err:
            QMessageBox.warning(self, 'Config Error',
                                f'The text entered cannot be parsed. '
                                'Look for YAML format errors.\n' +
                                str(err))
            return False

        if self.chkBox_saveformat.isChecked():
            try:
                # TODO: check if entry with same name already exists in the user config file
                with open(self.wizard().user_config_file, 'a') as file:
                    file.write(f'\n{self.txtEditor.toPlainText().strip()}\n')
            except Exception as err:
                QMessageBox.warning(self, 'Config Save Error',
                                    f'Failed to save the text as a new entry in '
                                    f'{self.wizard().user_config_file}.\n' +
                                    str(err))
                return False

        self.wizard().n42_config_dict = custom_config[next(iter(custom_config))]
        return True

    def nextId(self) -> int:
        return Pages.n42Load


class PCFFileLoadPage(QWizardPage):
    def __init__(self):
        QWizardPage.__init__(self)
        self.layout = QVBoxLayout(self)

        self.setWindowTitle("Base Spectra Creation Wizard")
        self.setTitle("Select PCF Files")
        self.setSubTitle("Click on the button to select the folder containing the PCF files. \n"
                         "The operation can be repeated multiple times to select files "
                         "from multiple folders")

        self.btnLoadSources = QPushButton("Add Files from Folder...")
        self.btnLoadSources.clicked.connect(self.get_path)
        self.pathLabel = QLabel('')
        self.lstPCFFiles = QListWidget(self)

        self.layout.addWidget(self.btnLoadSources)
        self.layout.addWidget(self.pathLabel)
        self.layout.addWidget(self.lstPCFFiles)

    @Slot(bool)
    def get_path(self, checked):
        options = QFileDialog.ShowDirsOnly
        if sys.platform.startswith('win'): options = QFileDialog.DontUseNativeDialog
        path = QFileDialog.getExistingDirectory(self, 'Choose Data Directory',
                                                RaseSettings().getLastDirectory(), options)
        if path:
            self.pathLabel.setText(path)
            self.get_PCF_file_list(True)

    @Slot(bool)
    def get_PCF_file_list(self, checked):
        if self.pathLabel.text():
            filenames = [f for f in os.listdir(self.pathLabel.text()) if f.lower().endswith(".pcf")]
            if not filenames:
                QMessageBox.critical(self, 'Invalid Directory Selection',
                                     'No PCF Files in selected Directory')
                return

            filenames.sort(key=natural_keys)
            self.lstPCFFiles.addItems(filenames)
            self.wizard().file_paths += [(self.pathLabel.text(), f) for f in filenames]
            self.completeChanged.emit()  # verify completion

    def isComplete(self) -> bool:
        # condition for proceeding is that there is at least one file name loaded
        return bool(self.lstPCFFiles.count())

    def nextId(self) -> int:
        return Pages.tableEditing


class n42FileLoadPage(QWizardPage):
    def __init__(self):
        QWizardPage.__init__(self)
        self.layout = QVBoxLayout(self)

        self.setWindowTitle("Base Spectra Creation Wizard")
        self.setTitle("Select n42 Files")
        self.setSubTitle("Click on the button to select the folder containing the n42 files. \n"
                         "The operation can be repeated multiple times to select files "
                         "from multiple folders")

        self.btnLoadSources = QPushButton("Add Files from Folder...")
        self.btnLoadSources.clicked.connect(self.get_path)
        self.pathLabel = QLabel('')
        self.lstn42Files = QListWidget(self)
        self.checkBox_ComboFolder = QCheckBox("Sum sources in subfolders")
        self.checkBox_ComboFolder.toggled.connect(self.clear_and_reload)

        self.layout.addWidget(self.btnLoadSources)
        self.layout.addWidget(self.pathLabel)
        self.layout.addWidget(self.checkBox_ComboFolder)
        self.layout.addWidget(self.lstn42Files)

    @Slot(bool)
    def get_path(self, checked):
        options = QFileDialog.ShowDirsOnly
        if sys.platform.startswith('win'): options = QFileDialog.DontUseNativeDialog
        path = QFileDialog.getExistingDirectory(self, 'Choose Data Directory',
                                                RaseSettings().getLastDirectory(), options)
        if path:
            self.pathLabel.setText(path)
            self.get_n42_file_list(self.checkBox_ComboFolder.isChecked())

    @Slot(bool)
    def clear_and_reload(self, checked):
        self.lstn42Files.clear()
        self.completeChanged.emit()
        self.get_n42_file_list(checked)

    def get_n42_file_list(self, sum_subfolders):
        if self.pathLabel.text():
            if not sum_subfolders:  # normal load
                filenames = [f for f in os.listdir(self.pathLabel.text()) if f.lower().endswith(".n42")]
                if not filenames:
                    QMessageBox.critical(self, 'Invalid Directory Selection',
                                         'No n42 Files in selected Directory')
                    return
            else:
                found_all = True
                bad_dirs = []
                filenames = []
                for it in os.scandir(self.pathLabel.text()):
                    if it.is_dir():
                        filenames.append(os.path.join(it.name, '*.n42'))
                        inputfiles = glob(os.path.join(it.path, '*.n42'))
                        if not bool(inputfiles):
                            found_all = False
                            bad_dirs.append(it.name)
                if not found_all:
                    bad_dir_str = ', '.join(bad_dirs)
                    QMessageBox.critical(self, 'Invalid Directory Selection',
                                         f'Subdirectory(s) {bad_dir_str} does not contain n42 files.')
                    return
            # TODO: check that each n42 is sane otherwise skip the file and notify the user
            filenames.sort(key=natural_keys)
            self.lstn42Files.addItems(filenames)
            self.wizard().file_paths += [(self.pathLabel.text(), f) for f in filenames]
            self.completeChanged.emit()  # verify completion

    def isComplete(self) -> bool:
        # condition for proceeding is that there is at least one file name loaded
        return bool(self.lstn42Files.count())

    def nextId(self) -> int:
        return Pages.tableEditing


class TableEditingPage(QWizardPage):
    def __init__(self):
        QWizardPage.__init__(self)

        self.layout = QVBoxLayout(self)

        self.setWindowTitle("Base Spectra Creation Wizard")
        self.setTitle("Provide Source Details")
        self.setSubTitle("For each file, RASE needs to know the true source ID "
                         "e.g. (\"Cu-60\" or (\"Cs-137\"), the exposure rate and/or source flux. "
                         "If data include background, the file with the representative background "
                         "spectrum should also be selected.")

        self.createBSTable = CreateBaseSpectraTableWidget()
        self.layout.addWidget(self.createBSTable)
        self.createBSTable.sourceTable.cellChanged.connect(lambda r, c: self.completeChanged.emit())

    def initializePage(self) -> None:
        state = False if self.wizard().file_type == 'PCF' else True
        self.createBSTable.initialize_table(state)
        self.createBSTable.set_vendorID_modelID(self.field('VendorID'), self.field('ModelID'))
        for p, f in self.wizard().file_paths:
            if self.wizard().file_type == 'PCF':
                for index, spectrum in enumerate(readpcf(os.path.join(p, f))):
                    self.createBSTable.create_table_row(f, p, index+1, spectrum.title)
            else:
                self.createBSTable.create_table_row(f, p)

    def cleanupPage(self) -> None:
        self.createBSTable.clear_table()

    def isComplete(self) -> bool:
        return self.createBSTable.validate_table_entries()

    def validatePage(self) -> bool:
        self.wizard().table_data = self.createBSTable.get_table_data_as_list()
        self.wizard().background_file_row = self.createBSTable.backgroundFileRow
        return True


class SelectOutputPage(QWizardPage):
    def __init__(self):
        QWizardPage.__init__(self)
        self.layout = QVBoxLayout(self)

        self.setWindowTitle("Base Spectra Creation Wizard")
        self.setTitle("Select Output Folder")
        self.setSubTitle("The base spectra have been processed and are ready to be saved to disk. \n"
                         "Please select the output folder location")

        self.btnOutFolder = QPushButton("Select Output Folder...")
        self.btnOutFolder.clicked.connect(self.get_path)
        self.txtOutFolder = QLineEdit(self)

        self.layout.addWidget(self.btnOutFolder)
        self.layout.addWidget(self.txtOutFolder)

        self.registerField('out_folder*', self.txtOutFolder)

    @Slot(bool)
    def get_path(self, checked):
        options = QFileDialog.ShowDirsOnly
        if sys.platform.startswith('win'): options = QFileDialog.DontUseNativeDialog
        path = QFileDialog.getExistingDirectory(self, 'Choose Output Directory',
                                                RaseSettings().getLastDirectory(), options)
        if path:
            self.txtOutFolder.setText(path)

    def validatePage(self) -> bool:
        print(self.wizard().table_data)
        try:
            create_base_spectra_from_input_data(self.wizard().n42_config_dict,
                                                self.wizard().file_type == 'PCF',
                                                self.wizard().table_data,
                                                self.wizard().background_file_row,
                                                self.field('out_folder'),
                                                self.field('VendorID'),
                                                self.field('ModelID'))
        except BaseSpectraFormatException as e:
            QMessageBox.warning(self, 'Base Spectrum Creation Error', e.args)
            return False
        except Exception as e:
            QMessageBox.warning(self, 'Error', str(e) + traceback.format_exc())
            return False
        QMessageBox.information(self, 'Success!', 'Base spectra creation completed succesfully!')
        return True


class Pages(IntEnum):
    intro = auto()
    method = auto()
    n42Format = auto()
    customFormat = auto()
    PCFLoad = auto()
    n42Load = auto()
    tableEditing = auto()
    selectOutput = auto()


class CreateBaseSpectraWizard(QWizard):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)

        # Shared data variables
        self.user_config_file = BASE_SPECTRUM_CREATION_CONFIG_DEFAULT
        self.file_paths = [] # List of filename and path tuples to use for creating base spectra
        self.file_type = None   # n42, PCF, GADRAS
        self.path = None  # Input Path
        self.n42_config_dict = {}  # n42 config settings as selected by user
        self.table_data = []
        self.background_file_row = None

        self.setPage(Pages.intro, IntroPage())
        self.setPage(Pages.method, MethodPage())
        self.setPage(Pages.n42Format, n42FormatPage())
        self.setPage(Pages.customFormat, CustomFormatPage())
        self.setPage(Pages.PCFLoad, PCFFileLoadPage())
        self.setPage(Pages.n42Load, n42FileLoadPage())
        self.setPage(Pages.tableEditing, TableEditingPage())
        self.page(Pages.tableEditing).setMinimumSize(800, 500)
        self.setPage(Pages.selectOutput, SelectOutputPage())
        self.page(Pages.selectOutput).setMinimumSize(400, 200)
