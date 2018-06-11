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
This module allows import of instrument base spectra
"""

import os
import sys
from os.path import splitext

from PyQt5.QtCore import Qt, pyqtSlot, QModelIndex
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QDialog, QFileDialog, QTableWidgetItem, QMessageBox, QHeaderView, QInputDialog

from .rase_functions import readSpectrumFile
from .scenario_dialog import MaterialDoseDelegate
from .table_def import Session, MaterialNameTranslation, Material, CccList, CccName, BaseSpectrum, BackgroundSpectrum
from .ui_generated import ui_import_base_spectra_dialog
from .utils import profileit


class BaseSpectraDialog(ui_import_base_spectra_dialog.Ui_Dialog, QDialog):
    def __init__(self, session, settings):
        QDialog.__init__(self)
        self.setupUi(self)
        self.settings = settings
        self.tblSpectra.setColumnCount(2)
        self.tblSpectra.setHorizontalHeaderLabels(['Material Name', 'File Name'])
        self.tblSpectra.setItemDelegateForColumn(0, MaterialDoseDelegate(self.tblSpectra, materialCol=0, editable=True))
        self.tblSpectra.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.txtStatus.setText('')
        self.baseSpectra = []
        self.backgroundSpectra = []
        self.backgroundSpectraType = 0
        self.initializingTable = False
        self.ecal = None
        self.counts = None
        self.session = session
        self.sharedObject = self.SharedObject(True)
        self.specMap = None
        self.bckgrndCorrupted = False
        self.redColor = QColor(255, 0, 0)
        self.blackColor = QColor(0, 0, 0)
    @pyqtSlot(bool)
    def on_btnBrowse_clicked(self, checked, directoryPath = None, secType = None):
        """
        Selects base spectra
        :param directoryPath: optional path input
        :param secType: optional secondary spectrum type
        """
        self.dir = dir = directoryPath
        if self.dir is None:
            options = QFileDialog.ShowDirsOnly
            if sys.platform.startswith('win'): options = QFileDialog.DontUseNativeDialog
            self.dir = dir = QFileDialog.getExistingDirectory(self, 'Choose Base Spectra Directory', self.settings.getDataDirectory(), options)
        if dir:
            self.txtFilepath.setText(dir)
            self.tblSpectra.clearContents()
            filenames = [f for f in os.listdir(dir) if f.lower().endswith(".n42")]
            if not filenames:
                QMessageBox.critical(self, 'Invalid Directory Selection',
                                     'No n42 Files in selected Directory')
                return

            #read the spectra into memory
            try:
              self.specMap = {}
              for filename in filenames:
                  v = readSpectrumFile(dir + os.sep + filename, self.sharedObject, self.txtStatus)
                  if v:
                      self.specMap[filename] = self.ReadFileObject(v[0],v[1],v[2],v[3],v[4],v[5],v[6],v[7],v[8])
            # get ecal, counts, and bckg spetrum parameters for one spectrum
              for filename in self.specMap.keys():
                  rfo = self.specMap[filename]
                  self.counts = rfo.counts
                  self.ecal = rfo.ecal
                  self.countsBckg = rfo.countsBckg
                  self.ecalBckg = rfo.ecalBckg
                  break
                  # make sure ecal, # of channels, and bckg spetrum parameters match for all spectra
              for filename in self.specMap.keys():
                  rfo = self.specMap[filename]
                  if self.counts.count(',') != rfo.counts.count(','):
                      self.txtStatus.append("Mismatch in # of channels between spectra")

                  self.txtStatus.setTextColor(self.redColor)
                  for i in range(len(self.ecal)):
                      if self.ecal[i] != rfo.ecal[i]:
                          self.txtStatus.append("Mismatch in " + str(i) + "th energy calibration parameter between spectra")
                  self.txtStatus.setTextColor(self.blackColor)
                  if self.countsBckg:
                      if self.countsBckg.count(',') != rfo.countsBckg.count(','):
                          self.txtStatus.append("Mismatch in # of channels between background spectra")
                      for i in range(len(self.ecal)):
                          if self.ecalBckg[i] != rfo.ecalBckg[i]:
                              self.txtStatus.append(
                                  "Mismatch in " + str(i) + "th energy calibration parameter between background spectra")
            except Exception as inst:
              print(type(inst))  # the exception instance
              print(inst.args)  # arguments stored in .args
              print(inst)

            # populate material, filename table
            self.initializingTable = True
            spectraCounter = 0
            for filename in self.specMap.keys():
                #if readSpectrumFile(dir + os.sep + filename, self.sharedObject, self.txtStatus):
                    spectraCounter = spectraCounter + 1
                    # TODO: develop more elaborated algorithm to correctly import thing like "HEU" or "WGPu" w/o altering the capitalization
#                    matName = '-'.join(splitext(filename)[0].split('_')[2:]).capitalize()
                    matName = '-'.join(splitext(filename)[0].split('_')[2:])
                    matTranslation = Session().query(MaterialNameTranslation).get(matName)
                    toName = matTranslation.toName if matTranslation else matName
                    row = self.tblSpectra.rowCount()
                    self.tblSpectra.setRowCount(row + 1)

                    # material name
                    item = QTableWidgetItem(toName)
                    item.setData(Qt.UserRole, matName)
                    self.tblSpectra.setItem(row, 0, item)

                    # filename
                    item = QTableWidgetItem(filename)
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    self.tblSpectra.setItem(row, 1, item)

            self.txtStatus.append("Number of base spectra read = " + str(spectraCounter))
            if self.sharedObject:
                if self.sharedObject.chanDataType:
                    self.txtStatus.append("Channel data type is " + self.sharedObject.chanDataType)
                if self.sharedObject.bcgndSpectrumInFile:
                    self.txtStatus.append("Secondary spectrum found in file")
            self.initializingTable = False
            self.tblSpectra.resizeColumnsToContents()
            self.tblSpectra.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

            # Check with the user about the type of the secondary spectrum
            if self.sharedObject.bcgndSpectrumInFile:
                secondary_types = ["Background Spectrum", "Internal Calibration Spectrum"]
                if secType != None:
                    self.backgroundSpectraType = secondary_types.index(secType) + 1
                    self.txtStatus.append("Secondary spectrum identified as " + secType)
                else:
                    s_type, ok = QInputDialog.getItem(self, "Select Secondary Spectrum Type",
                                                  "Secondary Spectrum was found. <br>  Select type or press cancel to disable secondary spectrum:",
                                                  secondary_types, 0, False)
                    if ok:
                        self.backgroundSpectraType = secondary_types.index(s_type) + 1
                        self.txtStatus.append("Secondary spectrum identified as " + s_type)
                    else:
                        self.txtStatus.append("Type of secondary spectrum not provided here")


    @pyqtSlot(QTableWidgetItem)
    def on_tblSpectra_itemChanged(self, item):
        """
        Spectra table change listener
        :param item: changed item is the spectra table
        """
        if not self.initializingTable:
            session = self.session
            origName = item.data(Qt.UserRole)
            matTranslation = session.query(MaterialNameTranslation).get(origName) or \
                             MaterialNameTranslation(name=origName)
            toName = item.text()
            if origName == toName:
                session.delete(matTranslation)
            else:
                matTranslation.toName = item.text()
                session.add(matTranslation)

    @profileit
    @pyqtSlot()
    def accept(self):
      try:
        # check that all material names are filled
        self.tblSpectra.setCurrentIndex((QModelIndex()))
        for row in range(self.tblSpectra.rowCount()):
            if not self.tblSpectra.item(row, 0).text():
                QMessageBox.warning(self, 'Empty Material Names', 'Must have a material name for each element')
                return

        backgroundSpectrum = None
        for row in range(self.tblSpectra.rowCount()):
            # initialize a BaseSpectrum
            # each material gets a default cccList with a single list of a single material name
            materialName = self.tblSpectra.item(row, 0).text()
            material = self.session.query(Material).get(materialName)
            if not material:
                material = Material(name=materialName, associated_spectrum_counter = 0)
                cccList = CccList()
                cccName = CccName(name=materialName)
                cccList.ccc_names.append(cccName)
                material.cccLists.append(cccList)
            material.increment_associated_spectrum_counter()
            baseSpectraFilename = self.tblSpectra.item(row, 1).text()
            baseSpectraFilepath = self.dir + os.sep + baseSpectraFilename
            if "n42" not in baseSpectraFilepath and "N42" not in baseSpectraFilepath:
                continue

            rfo = self.specMap[baseSpectraFilename]

            if self.sharedObject.bcgndSpectrumInFile:
                if row == 0:
                    if rfo.realtimeBckg is None or rfo.livetimeBckg is None or rfo.livetimeBckg is None:
                        self.bckgrndCorrupted = True
                    else:
                        backgroundSpectrum = BackgroundSpectrum(material=material,
                                                            filename=baseSpectraFilepath,
                                                            realtime=rfo.realtimeBckg,
                                                            livetime=rfo.livetimeBckg,
                                                            baseCounts=rfo.countsBckg)
                else:
                    if(self.bckgrndCorrupted == True):
                        backgroundSpectrum = None
                    #if backgroundSpectrum.realtime != rfo.realtimeBckg:
                        #backgroundSpectrum = None
                    if backgroundSpectrum.livetime != rfo.livetimeBckg:
                        if rfo.livetimeBckg > backgroundSpectrum.livetime:
                            backgroundSpectrum = BackgroundSpectrum(material=material,
                                                            filename=baseSpectraFilepath,
                                                            realtime=rfo.realtimeBckg,
                                                            livetime=rfo.livetimeBckg,
                                                            baseCounts=rfo.countsBckg)
                        #backgroundSpectrum = None
                    #if backgroundSpectrum.baseCounts != rfo.countsBckg:
                        #backgroundSpectrum = None

            baseSpectrum = BaseSpectrum(material=material,
                                                    filename=baseSpectraFilepath,
                                                    realtime=rfo.realtime,
                                                    livetime=rfo.livetime,
                                                    sensitivity=rfo.sensitivity,
                                                    baseCounts=rfo.counts)
            self.baseSpectra.append(baseSpectrum)

        self.backgroundSpectra.append(backgroundSpectrum)

      except Exception as inst:
        print(type(inst))  # the exception instance
        print(inst.args)  # arguments stored in .args
        print(inst)

      return QDialog.accept(self)

    class SharedObject():
        def __init__(self, isBckgrndSave):
            self.isBckgrndSave = isBckgrndSave
            self.chanDataType = None
            self.bcgndSpectrumInFile = False

    class ReadFileObject() :
        def __init__(self,counts,ecal,realtime,livetime,sensitivity,countsBckg=None,ecalBckg=None,realtimeBckg=None,livetimeBckg=None):
            self.counts = counts
            self.ecal = ecal
            self.realtime = realtime
            self.livetime = livetime
            self.sensitivity = sensitivity
            self.countsBckg = countsBckg
            self.ecalBckg = ecalBckg
            self.realtimeBckg = realtimeBckg
            self.livetimeBckg = livetimeBckg
