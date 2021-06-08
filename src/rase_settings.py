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
This module defines RASE settings infrastructure and default settings
"""
import os

from PyQt5 import QtCore

from src import sampling_algos
from src import table_def

RASE_DATA_DIR_KEY = 'files/data_directory'
DEFAULT_DATA_DIR = os.path.expanduser(os.path.join('~', 'RaseData'))

RASE_SAMPLING_ALGO_KEY = "sampling algorithm"
DEFAULT_SAMPLING_ALGO = sampling_algos.generate_sample_counts_inversion

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
