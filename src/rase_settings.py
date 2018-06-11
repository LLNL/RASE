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

CORRESPONDENCE_TABLE_KEY = "correspondence table"

LAST_SCENARIO_GRPNAME_KEY = 'last_scenario_grpname'
DEFAULT_SCENARIO_GRPNAME = 'default_group'


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

        if not self.settings.value(CORRESPONDENCE_TABLE_KEY):
            self.settings.setValue(CORRESPONDENCE_TABLE_KEY, None)

        # Last scenario group used
        if not self.settings.value(LAST_SCENARIO_GRPNAME_KEY):
            self.settings.setValue(LAST_SCENARIO_GRPNAME_KEY, DEFAULT_SCENARIO_GRPNAME)

    # Sample Directory
    def getSampleDirectory(self):
        """
        Returns full path of the SampleSpectra directory
        """
        return os.path.join(self.settings.value(RASE_DATA_DIR_KEY), 'SampleSpectra')

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

    def setDataDirectory(self, dir):
        """
        Sets Rase Data directory
        """
        self.settings.setValue(RASE_DATA_DIR_KEY, dir)

    def getCorrespondenceTable(self):
        """
        Returns default Correspondence Table name
        """
        return self.settings.value(CORRESPONDENCE_TABLE_KEY)

    def setCorrespondenceTable(self, table):
        """
        Sets default Correspondence Table name
        """
        self.settings.setValue(CORRESPONDENCE_TABLE_KEY, table)

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

    def getAllSettingsAsText(self):
        """
        Returns all settings as text
        """
        return "\n".join([k+" : "+str(self.settings.value(k)) for k in self.settings.allKeys()])
