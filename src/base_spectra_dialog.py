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
This module allows import of instrument base spectra
"""
import logging
import os
import sys
import traceback
from os.path import splitext
from typing import Sequence
from PySide6.QtCore import Qt, Slot, QModelIndex
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QDialog, QFileDialog, QTableWidgetItem, QMessageBox, QHeaderView, QInputDialog, QApplication

from .spectrum_file_reading import readSpectrumFile, yield_spectra
from .spectrum_file_reading import all_spec as read_spec
from .rase_functions import get_or_create_material, get_ET_from_file
from .table_def import BaseSpectrum, BackgroundSpectrum, SecondarySpectrum
from .ui_generated import ui_import_base_spectra_dialog
from .utils import profileit
from .rase_settings import RaseSettings


class BaseSpectraDialog(ui_import_base_spectra_dialog.Ui_Dialog, QDialog):

    def __init__(self, session):
        QDialog.__init__(self)
        self.setupUi(self)
        self.settings = RaseSettings()
        self.tblSpectra.setColumnCount(3)
        self.tblSpectra.setHorizontalHeaderLabels(['Material Name',  'File Name', 'Fgnd Includes\nIntrinsic Source'])
        self.tblSpectra.hideColumn(2)
        # self.tblSpectra.setItemDelegateForColumn(0, MaterialDoseDelegate(self.tblSpectra, materialCol=0, editable=True))
        self.tblSpectra.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.txtStatus.setText('')
        self.baseSpectra = []
        self.backgroundSpectrum = None
        self.backgroundSpectrumType = None
        self.ecal = None
        self.counts = None
        self.session = session
        self.sharedObject = SharedObject(True)
        self.specMap = None
        self.bckgrndCorrupted = False
        self.redColor = QColor(Qt.red)
        self.textColor = QApplication.palette().text().color()
        self.secondary_spectra = []

    def validate_spectra(self, spectra):
        #NOT validating spectra have same ecal. This should be OK, and we rebin to correct for it later if necessary.

        #validate same spectra length

        detectorchannellist = [rfo.counts.count(',') for rfo in spectra.values()]
        detectorchannelvalid = detectorchannellist.count(detectorchannellist[0]) == len(detectorchannellist)
        bkgchannelslist = [rfo.countsBckg.count(',') for rfo in spectra.values() if rfo.countsBckg is not None]
        ecalbkglist = [rfo.ecalBckg for rfo in spectra.values() if rfo.ecalBckg is not None]

        self.txtStatus.setTextColor(self.redColor)
        if not detectorchannelvalid:
            self.txtStatus.append("Mismatch in # of channels between spectra")
        self.txtStatus.setTextColor(self.textColor)
        if bkgchannelslist:
            bkgchannelsvalid = bkgchannelslist.count(bkgchannelslist[0]) == len(bkgchannelslist)
            if not bkgchannelsvalid:
                self.txtStatus.append("Mismatch in # of channels between background spectra")
        if ecalbkglist:
            ecalbkgvalid = ecalbkglist.count(ecalbkglist[0]) == len(ecalbkglist)
            if not ecalbkgvalid:
                self.txtStatus.append("Mismatch in energy calibration parameters between background spectra")

    @Slot(bool)
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

                try:
                    firstroot = get_ET_from_file(dir + os.sep + filenames[0]).getroot()
                    spectra = yield_spectra(firstroot, read_spec)
                    self.secondary_spectra = [spec for spec in spectra if isinstance(spec,SecondarySpectrum)]
                except Exception as e:
                    pass

                for filename in filenames:
                  v = readSpectrumFile(dir + os.sep + filename, self.sharedObject, self.txtStatus, requireRASESen=True,
                                       only_one_secondary=self.secondary_spectra is None)
                  if v:
                      self.specMap[filename] = ReadFileObject(v[0],v[1],v[2],v[3],v[4],v[5],v[6],v[7],v[8],v[9])
                        #TODO: replace background elements of the RFO with the background from the secondary spectra list if it's present
            except Exception as e:
                traceback.print_exc()
                logging.exception("Handled Exception", exc_info=True)
                # get ecal, counts, and bckg spetrum parameters for one spectrum
            self.validate_spectra(self.specMap)

            firstrfo = self.specMap[filenames[0]]
            self.counts = firstrfo.counts
            self.ecal = firstrfo.ecal


            #check if new secondary spectra include a background
            background_sec = [spec for spec in self.secondary_spectra if spec.classcode =='Background']
            if len(background_sec):
                first_bgs = background_sec[0]
                # really is first spectrum in self.specMap
                firstrfo.countsBckg = first_bgs.baseCounts
                firstrfo.ecalBckg = first_bgs.ecal
                firstrfo.livetimeBckg = first_bgs.livetime
                firstrfo.realtimeBckg = first_bgs.realtime

            # populate material, filename table
            self.tblSpectra.blockSignals(True)
            spectraCounter = 0
            for filename in self.specMap.keys():
                #if readSpectrumFile(dir + os.sep + filename, self.sharedObject, self.txtStatus):
                    spectraCounter = spectraCounter + 1
                    # TODO: develop more elaborated algorithm to correctly import thing like "HEU" or "WGPu" w/o altering the capitalization
#                    matName = '-'.join(splitext(filename)[0].split('_')[2:]).capitalize()
                    matName = '-'.join(splitext(filename)[0].split('_')[2:])
                    row = self.tblSpectra.rowCount()
                    self.tblSpectra.setRowCount(row + 1)

                    # material name
                    item = QTableWidgetItem(matName)
                    self.tblSpectra.setItem(row, 0, item)

                    # filename
                    item = QTableWidgetItem(filename)
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    self.tblSpectra.setItem(row, 1, item)

                    # has intrinsic source?
                    item = QTableWidgetItem()
                    item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                    item.setCheckState(Qt.Unchecked)
                    self.tblSpectra.setItem(row, 2, item)

            self.txtStatus.append("Number of base spectra read = " + str(spectraCounter))
            if self.sharedObject:
                if self.sharedObject.chanDataType:
                    self.txtStatus.append("Channel data type is " + self.sharedObject.chanDataType)
                if self.sharedObject.bkgndSpectrumInFile:
                    self.txtStatus.append("Secondary spectrum found in file")
            self.tblSpectra.blockSignals(False)
            self.tblSpectra.resizeColumnsToContents()
            self.tblSpectra.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

            # Check with the user about the type of the secondary spectrum
            self.tblSpectra.showColumn(2)
            if self.sharedObject.bkgndSpectrumInFile:
                if len(self.secondary_spectra) > 1:
                    self.txtStatus.append('Secondary spectra identified in base spectra files.')
                else:
                    self.txtStatus.append('Secondary spectrum identified in base spectra files.')
                no_known_classcode = True
                for secondary in self.secondary_spectra:
                    if type(secondary.classcode) == str:
                        if secondary.classcode.lower() == 'foreground':
                            self.txtStatus.append('An additional foreground was identified.')
                            no_known_classcode = False
                        elif secondary.classcode.lower() == 'calibration':
                            self.txtStatus.append('An internal calibration source spectrum was identified.')
                            no_known_classcode = False
                        elif secondary.classcode.lower() == 'intrinsicactivity':
                            self.txtStatus.append('An intrinsic activity spectrum was identified.')
                            no_known_classcode = False
                        elif secondary.classcode.lower() == 'background':
                            self.txtStatus.append('A background spectrum was identified.')
                            no_known_classcode = False
                        elif secondary.classcode.lower() == 'notspecified':
                            self.txtStatus.append('A spectrum with an unspecified classcode was identified.')
                if no_known_classcode:
                    self.txtStatus.append('Could not determine type of secondary spectrum.')

                self.backgroundSpectrumType = 0


    @profileit
    @Slot()
    def accept(self):
      try:
        # check that all material names are filled
        self.tblSpectra.setCurrentIndex((QModelIndex()))
        for row in range(self.tblSpectra.rowCount()):
            if not self.tblSpectra.item(row, 0).text():
                QMessageBox.warning(self, 'Empty Material Names', 'Must have a material name for each element')
                return
        self.intrinsic_is_included = False
        self.backgroundSpectrum = None
        for row in range(self.tblSpectra.rowCount()):
            # initialize a BaseSpectrum
            materialName = self.tblSpectra.item(row, 0).text()
            intrinsic_included = bool(self.tblSpectra.item(row, 2).checkState() == Qt.CheckState.Checked)
            material = get_or_create_material(self.session, materialName, intrinsic_included)
            self.intrinsic_is_included = self.intrinsic_is_included or intrinsic_included
            baseSpectraFilename = self.tblSpectra.item(row, 1).text()
            baseSpectraFilepath = self.dir + os.sep + baseSpectraFilename
            if "n42" not in baseSpectraFilepath and "N42" not in baseSpectraFilepath:
                continue

            rfo = self.specMap[baseSpectraFilename]

            if self.sharedObject.bkgndSpectrumInFile:# and self.backgroundSpectrumType is not None:
                if row == 0:
                    if rfo.realtimeBckg is None or rfo.livetimeBckg is None or rfo.livetimeBckg is None:
                        self.bckgrndCorrupted = True
                    else:
                        self.backgroundSpectrum = BackgroundSpectrum(material=material,
                                                                     filename=baseSpectraFilepath,
                                                                     realtime=rfo.realtimeBckg,
                                                                     livetime=rfo.livetimeBckg,
                                                                     baseCounts=rfo.countsBckg,
                                                                     ecal=rfo.ecalBckg)
                else:
                    if(self.bckgrndCorrupted == True):
                        self.backgroundSpectrum = None
                    if self.backgroundSpectrum.livetime != rfo.livetimeBckg:
                        if rfo.livetimeBckg > self.backgroundSpectrum.livetime:
                            self.backgroundSpectrum = BackgroundSpectrum(material=material,
                                                                         filename=baseSpectraFilepath,
                                                                         realtime=rfo.realtimeBckg,
                                                                         livetime=rfo.livetimeBckg,
                                                                         baseCounts=rfo.countsBckg,
                                                                         ecal=rfo.ecalBckg)

            baseSpectrum = BaseSpectrum(material=material, filename=baseSpectraFilepath, realtime=rfo.realtime,
                         livetime=rfo.livetime, rase_sensitivity=rfo.rase_sensitivity,
                         flux_sensitivity=rfo.flux_sensitivity, baseCounts=rfo.counts, ecal=rfo.ecal)

            self.baseSpectra.append(baseSpectrum)

      except Exception as e:
          traceback.print_exc()
          logging.exception("Handled Exception", exc_info=True)

      return QDialog.accept(self)


class SharedObject:
    def __init__(self, isBckgrndSave):
        self.isBckgrndSave = isBckgrndSave
        self.chanDataType = None
        self.bkgndSpectrumInFile = False


class ReadFileObject:
    def __init__(self, counts, ecal, realtime, livetime, rase_sensitivity, flux_sensitivity, countsBckg=None,
                    ecalBckg=None, realtimeBckg=None, livetimeBckg=None):
        self.counts = counts
        self.ecal = ecal
        self.realtime = realtime
        self.livetime = livetime
        self.rase_sensitivity = rase_sensitivity
        self.flux_sensitivity = flux_sensitivity
        self.countsBckg = countsBckg
        self.ecalBckg = ecalBckg
        self.realtimeBckg = realtimeBckg
        self.livetimeBckg = livetimeBckg
