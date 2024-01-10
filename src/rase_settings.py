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
This module defines RASE settings infrastructure and default settings
"""
import os, sys
import shutil

from PySide6 import QtCore

from src import sampling_algos
from src import table_def
from src.utils import get_bundle_dir

# global variable with the executable application path (rase.exe or rase.pyw)
APPLICATION_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if getattr(sys, 'frozen', False):
    # we are in a pyinstaller bundle
    APPLICATION_PATH = os.path.dirname(sys.executable)

RASE_DATA_DIR_KEY = 'files/data_directory'
# DEFAULT_DATA_DIR = os.path.expanduser(os.path.join('~', 'RaseData'))
DEFAULT_DATA_DIR = os.path.join(APPLICATION_PATH, 'RaseData')

RASE_SAMPLING_ALGO_KEY = "sampling algorithm"
DEFAULT_SAMPLING_ALGO = sampling_algos.generate_sample_counts_poisson

LAST_SCENARIO_GRPNAME_KEY = 'last_scenario_grpname'
DEFAULT_SCENARIO_GRPNAME = 'default_group'

RANDOM_SEED_KEY = "Random Seed"
RANDOM_SEED_DEFAULT = 1

RANDOM_SEED_FIXED_KEY = "Random Seed Fixed"
RANDOM_SEED_FIXED_DEFAULT = False

IS_AFTER_CORRESPONDENCE_TABLE_CALL_KEY = "Is After Correspondence Table Call"
IS_AFTER_CORRESPONDENCE_TABLE_CALL_DEFAULT = False

CONFIDENCE_USED_IN_CALCS_KEY = "Confidence Used In F-score Calcs"
CONFIDENCE_USED_IN_CALCS_DEFAULT = True

MWEIGHTS_USED_IN_CALCS_KEY = "Material Weights Used In F-Score Calcs"
MWEIGHTS_USED_IN_CALCS_DEFAULT = True

RESULTS_TBL_COLS_KEY = "Results Table Columns"
RESULTS_TBL_COLS_DEFAULT = []

BASE_SPECTRUM_CREATION_CONFIG_KEY = 'Base Spectrum Creation Configuration File'
BASE_SPECTRUM_CREATION_CONFIG_DEFAULT = os.path.join(APPLICATION_PATH, 'base_spectra_config.yaml')

WEBID_DRFS_KEY = 'WebID DRFs'
WEBID_DRFS_DEFAULT = []
# WEBID_DRFS_DEFAULT = ['1x1/BGO Side', '1x1/CsI Side', '1x1/LaCl3', '1x1/NaI Front', '1x1/NaI Side', '3x3/NaI AboveSource', '3x3/NaI InCorner', '3x3/NaI LowScat', '3x3/NaI MidScat', '3x3/NaI OnGround', 'ASP-Thermo', 'Apollo/Bottom', 'Apollo/Front', 'Atomex-AT6102', 'D3S', 'Detective', 'Detective-EX', 'Detective-EX100', 'Detective-EX200', 'Detective-Micro', 'Detective-Micro/Variant-LowEfficiency', 'Detective-X', 'Falcon 5000', 'FieldSpec', 'GR130', 'GR135', 'GR135Plus', 'IdentiFINDER-LaBr3', 'IdentiFINDER-N', 'IdentiFINDER-NG', 'IdentiFINDER-NGH', 'IdentiFINDER-R300', 'IdentiFINDER-R500-NaI', 'InSpector 1000 LaBr3', 'InSpector 1000 NaI', 'Interceptor', 'LaBr3Marlow', 'LaBr3PNNL', 'MKC-A03', 'Mirion PDS-100', 'Polimaster PM1704-GN', 'RIIDEyeX-GN1', 'RadEagle', 'RadEye', 'RadPack', 'RadSeeker-NaI', 'Radseeker-LaBr3', 'Raider', 'Ranger', 'SAM-935', 'SAM-945', 'SAM-950GN-N30', 'SAM-Eagle-LaBr3', 'SAM-Eagle-NaI-3x3', 'SpiR-ID/LaBr3', 'SpiR-ID/NaI', 'Thermo ARIS Portal', 'Transpec', 'Verifinder']

class RaseSettings:
    def __init__(self):
        self.settings = QtCore.QSettings('dndo', 'rase_software')

        # Make sure all settings can be read. Bad entries are removed
        for k in self.settings.allKeys():
            try:
                x = self.settings.value(k)
            except:
                self.settings.remove(k)

        # check if data directory initialized
        if not self.settings.value(RASE_DATA_DIR_KEY):
            self.settings.setValue(RASE_DATA_DIR_KEY, DEFAULT_DATA_DIR)

        if not self.settings.value(RASE_SAMPLING_ALGO_KEY):
            self.settings.setValue(RASE_SAMPLING_ALGO_KEY, DEFAULT_SAMPLING_ALGO)

        # Last scenario group used
        if not self.settings.value(LAST_SCENARIO_GRPNAME_KEY):
            self.settings.setValue(LAST_SCENARIO_GRPNAME_KEY, DEFAULT_SCENARIO_GRPNAME)

        if not self.settings.value(RANDOM_SEED_KEY):
            self.settings.setValue(RANDOM_SEED_KEY, RANDOM_SEED_DEFAULT)

        if not self.settings.value(RANDOM_SEED_FIXED_KEY):
            self.settings.setValue(RANDOM_SEED_FIXED_KEY, RANDOM_SEED_FIXED_DEFAULT)

        if self.settings.value(CONFIDENCE_USED_IN_CALCS_KEY):
            self.settings.setValue(CONFIDENCE_USED_IN_CALCS_KEY, CONFIDENCE_USED_IN_CALCS_DEFAULT)

        if self.settings.value(MWEIGHTS_USED_IN_CALCS_KEY):
            self.settings.setValue(MWEIGHTS_USED_IN_CALCS_KEY, MWEIGHTS_USED_IN_CALCS_DEFAULT)

        if not self.settings.value(RESULTS_TBL_COLS_KEY):
            self.settings.setValue(RESULTS_TBL_COLS_KEY, RESULTS_TBL_COLS_DEFAULT)

        if not os.path.isfile(BASE_SPECTRUM_CREATION_CONFIG_DEFAULT):
            shutil.copyfile(os.path.join(get_bundle_dir(), 'tools', 'base_spectra_config.yaml'),
                            BASE_SPECTRUM_CREATION_CONFIG_DEFAULT)
        if not self.settings.value(BASE_SPECTRUM_CREATION_CONFIG_KEY):
            self.settings.setValue(BASE_SPECTRUM_CREATION_CONFIG_KEY, BASE_SPECTRUM_CREATION_CONFIG_DEFAULT)

        if not self.settings.value(WEBID_DRFS_KEY):
            self.settings.setValue(WEBID_DRFS_KEY, WEBID_DRFS_DEFAULT)

        # this is qt internal settings store
        self.qtsettings = QtCore.QSettings(QtCore.QSettings.UserScope, "qtproject")

    # Sample Directory
    def getSampleDirectory(self):
        """
        Returns full path of the SampleSpectra directory
        """
        return os.path.join(self.settings.value(RASE_DATA_DIR_KEY), 'SampledSpectra')

    # Database File
    def getDatabaseFilepath(self):
        """
        Returns full path of the DB file
        """
        return os.path.join(self.settings.value(RASE_DATA_DIR_KEY), table_def.DB_VERSION_NAME + '.sqlite')

    def getDataDirectory(self):
        """
        Returns Rase Data directory
        """
        return self.settings.value(RASE_DATA_DIR_KEY)

    def setDataDirectory(self, path):
        """
        Sets Rase Data directory
        """
        self.settings.setValue(RASE_DATA_DIR_KEY, path)

    def getLastDirectory(self):
        """
        Returns the last visited file from Qt
        """
        # Qt non-native dialogs automatically remember the history of visited paths.
        # In order to use the OS native dialogs, we need to keep track of this manually
        u = QtCore.QUrl(self.qtsettings.value("FileDialog/lastVisited"))
        return u.toLocalFile()

    def getSamplingAlgo(self):
        """
        Returns default Sampling Algo
        """
        return self.settings.value(RASE_SAMPLING_ALGO_KEY)

    def setSamplingAlgo(self, algo):
        """
        Sets default Sampling Algo
        """
        self.settings.setValue(RASE_SAMPLING_ALGO_KEY, algo)

    def getLastScenarioGroupName(self):
        """
        Returns last Scenario Group name
        """
        return self.settings.value(LAST_SCENARIO_GRPNAME_KEY)

    def setLastScenarioGroupName(self, grp_name):
        """
        sets last Scenario Group name
        """
        self.settings.setValue(LAST_SCENARIO_GRPNAME_KEY, grp_name)

    def getRandomSeed(self):
        """
        Returns Random Seed
        """
        return int(self.settings.value(RANDOM_SEED_KEY))

    def setRandomSeed(self, seed):
        """
        Sets Random Seed
        """
        self.settings.setValue(RANDOM_SEED_KEY, seed)

    def getRandomSeedDefault(self):
        """
        Returns Random Seed default value
        """
        return RANDOM_SEED_DEFAULT

    def getRandomSeedFixed(self):
        """
        Returns Random Seed Fixed boolean
        """
        return self.settings.value(RANDOM_SEED_FIXED_KEY, type=bool)

    def setRandomSeedFixed(self, isFixed):
        """
        Sets Random Seed Fixed boolean
        """
        self.settings.setValue(RANDOM_SEED_FIXED_KEY, isFixed)

    def getIsAfterCorrespondenceTableCall(self):
        """
        Returns Is After Correspondence Table Call boolean
        """
        return self.settings.value(IS_AFTER_CORRESPONDENCE_TABLE_CALL_KEY, type=bool)

    def setIsAfterCorrespondenceTableCall(self, isAfterCorrespondenceTableCall):
        """
        Sets Is After Correspondence Table Call boolean
        """
        self.settings.setValue(IS_AFTER_CORRESPONDENCE_TABLE_CALL_KEY, isAfterCorrespondenceTableCall)

    def getUseConfidencesInCalcs(self):
        """
        Returns Use Confidences In Calculations boolean
        """
        return self.settings.value(CONFIDENCE_USED_IN_CALCS_KEY, type=bool)

    def setUseConfidencesInCalcs(self, is_checked):
        """
        Sets Use Confidences In Calculations boolean
        """
        self.settings.setValue(CONFIDENCE_USED_IN_CALCS_KEY, is_checked)

    def getUseConfidencesInCalcsDefault(self):
        """
        Returns Use Confidences In Calculations default boolean value
        """
        return CONFIDENCE_USED_IN_CALCS_DEFAULT

    def getUseMWeightsInCalcs(self):
        """
        Returns Use Confidences In Calculations boolean
        """
        return self.settings.value(MWEIGHTS_USED_IN_CALCS_KEY, type=bool)

    def setUseMWeightsInCalcs(self, is_checked):
        """
        Sets Use Confidences In Calculations boolean
        """
        self.settings.setValue(MWEIGHTS_USED_IN_CALCS_KEY, is_checked)

    def getUseMWeightsInCalcsDefault(self):
        """
        Returns Use Confidences In Calculations default boolean value
        """
        return MWEIGHTS_USED_IN_CALCS_DEFAULT

    def getRandomSeedFixedDefault(self):
        """
        Returns Random Seed Fixed default boolean value
        """
        return RANDOM_SEED_FIXED_DEFAULT

    def getIsAfterCorrespondenceTableCalldDefault(self):
        """
        Returns Is After Correspondence Table Call default boolean value
        """
        return IS_AFTER_CORRESPONDENCE_TABLE_CALL_DEFAULT

    def getAllSettingsAsText(self):
        """
        Returns all settings as text
        """
        return "\n".join([k+" : "+str(self.settings.value(k)) for k in self.settings.allKeys()])

    def getResultsTableSettings(self):
        """
         Returns Results Table Settings
         """
        return self.settings.value(RESULTS_TBL_COLS_KEY)

    def setResultsTableSettings(self, col_list):
        """
        Sets Results Table Settings
        """
        self.settings.setValue(RESULTS_TBL_COLS_KEY, col_list)

    def getBaseSpectrumCreationConfig(self):
        """
        Returns path to base spectrum creation configuration file
        """
        return self.settings.value(BASE_SPECTRUM_CREATION_CONFIG_KEY)

    def setBaseSpectrumCreationConfig(self, path):
        """
        Returns path to base spectrum creation configuration file
        """
        self.settings.setValue(BASE_SPECTRUM_CREATION_CONFIG_KEY, path)

    def getWebIDDRFsList(self):
        """
         Gets List of DRFs in WebID
         """
        return self.settings.value(WEBID_DRFS_KEY)

    def setWebIDDRFsList(self, drf_list):
        """
        Sets List of DRFs in WebID
        """
        self.settings.setValue(WEBID_DRFS_KEY, drf_list)
