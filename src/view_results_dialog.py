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
This module desplays the complete summary of replay results and subsequent analysis
"""

import csv

from functools import partial

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QDialog, QTableWidgetItem, QHBoxLayout, QHeaderView, QFileDialog

from .plotting import LinePlot
from .table_def import Session, Scenario, Detector, IdentificationSet
from .ui_generated import ui_results_dialog
from src.detailed_results_dialog import DetailedResultsDialog
from src.correspondence_table_dialog import CorrespondenceTableDialog
from src.rase_settings import RaseSettings

NUM_COL = 9
INST_REPL, SCEN_ID, SCEN_DESC, ACQ_TIME, REPL, INFL, PRECISION, RECALL, FSCORE  = range(NUM_COL)

class ViewResultsDialog(ui_results_dialog.Ui_dlgResults, QDialog):
    def __init__(self, parent, scenIds, detNames):

        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.parent = parent
#        self.stats = scenario_stats
#        self.result_super_map = result_super_map
        self.columnLabelList = [None]*NUM_COL
        self.columnLabelList[INST_REPL] = 'Instrument/Replay'
        self.columnLabelList[SCEN_ID] = 'Scen Id'
        self.columnLabelList[SCEN_DESC] = 'Scen Desc'
        self.columnLabelList[ACQ_TIME] = 'Acq. time (s)'
        self.columnLabelList[REPL] = 'Replications'
        self.columnLabelList[INFL] = 'Influences'
        self.columnLabelList[PRECISION] = 'Precision'
        self.columnLabelList[RECALL] = 'Recall'
        self.columnLabelList[FSCORE] = 'Fscore'
        self.tblResults.setColumnCount(len(self.columnLabelList))
        self.tblResults.setHorizontalHeaderLabels(self.columnLabelList)
        self.tableData = self.getResultsTable(scenIds, detNames)
        comboList = ['','Detector', 'Replay', 'Dose', 'Time', 'Influence',
                     'IC', 'IM', 'IR', 'IMR', 'CCC',
                     'False Positives', 'False Negatives', 'Correct Matches']
        self.cmbXaxis.addItems(comboList)
        self.cmbYaxis.addItems(comboList)
        self.cmbZaxis.addItems(comboList)

        matNames = set()
        for dataRow in self.tableData:
            matNames.update(list(dataRow['materialAndExposure'].keys()))
        matNames =  [''] + list(matNames)
        for axis in ['X', 'Y', 'Z']:
            cmbMat = getattr(self, 'cmb' + axis + 'mat')
            cmbMat.addItems(matNames)

        self.populateResultsTable(self.tableData)
        self.tblResults.doubleClicked.connect(self.showDetails)
        self.btnClose.clicked.connect(self.closeSelected)
        self.buttonExport.clicked.connect(self.handleExport)
        self.buttonCorrTable.clicked.connect(self.openCorrTable)
#        self.buttonCorrTable.setDisabled(True)

    def openCorrTable(self):
        """
        Launches Correspondence Table Dialog
        """
        CorrespondenceTableDialog().exec_()
        self.parent.calculateScenarioStats()
        self.populateResultsTable(self.tableData)
        self.parent.settings.setIsAfterCorrespondenceTableCall(True)

    def handleExport(self):
        """
        Exports to CSV
        """
        path = QFileDialog.getSaveFileName(self, 'Save File', RaseSettings().getDataDirectory(), 'CSV (*.csv)')
        if path[0]:
            with open(path[0], mode='w', newline='') as stream:
                writer = csv.writer(stream)
                writer.writerow(self.columnLabelList)
                for row in range(self.tblResults.rowCount()):
                    rowdata = []
                    for column in range(self.tblResults.columnCount()):
                        item = self.tblResults.item(row, column)
                        if item is not None:
                            rowdata.append(item.text())
                        else:
                            rowdata.append('')
                    writer.writerow(rowdata)

    def closeSelected(self):
        """
        Closes Dialog
        """
        super().accept()

    def showDetails(self):
        """
        Displayes detailed results for the selected row in the result table
        """
        detName = self.tblResults.item(self.tblResults.currentRow(),0).text().split("/")[0]
        scenId = self.tblResults.item(self.tblResults.currentRow(),1).text()
        for key in self.parent.result_super_map:
            print("key="+key)
        resultMap = self.parent.result_super_map[scenId+"*"+detName]
        DetailedResultsDialog(resultMap).exec_()
        print(self.tblResults.item(self.tblResults.currentRow(),2).text())

    def populateResultsTable(self, tableData):
        """
        Populates Results table
        :param tableData: result table data structure
         """
        self.tblResults.setRowCount(0)
        for row, dataRow in enumerate(tableData):
            self.tblResults.insertRow(row)
            self.tblResults.setItem(row, INST_REPL, QTableWidgetItem(dataRow['detectorName'] + '/' + dataRow['replayName']))
            self.tblResults.setItem(row, SCEN_ID,   QTableWidgetItem(dataRow['scenId']))
            self.tblResults.setItem(row, SCEN_DESC, QTableWidgetItem(', '.join('{}({})'.format(matName, dataRow['materialAndExposure'][matName]) for matName in dataRow['materialAndExposure'])))
            self.tblResults.setItem(row, INFL,      QTableWidgetItem(', '.join(infl for infl in dataRow['influences'])))
            self.tblResults.setItem(row, ACQ_TIME,  QTableWidgetItem(str(dataRow['acqTime'])))
            self.tblResults.setItem(row, REPL,      QTableWidgetItem(str(dataRow['replication'])))
            self.tblResults.setItem(row, PRECISION, QTableWidgetItem(self.parent.scenario_stats[dataRow['scenId']][0]))
            self.tblResults.setItem(row, RECALL,    QTableWidgetItem(self.parent.scenario_stats[dataRow['scenId']][1]))
            self.tblResults.setItem(row, FSCORE,    QTableWidgetItem(self.parent.scenario_stats[dataRow['scenId']][2]))
        self.tblResults.resizeColumnsToContents()
        self.tblResults.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)


    def getResultsTable(self, scenIds, detNames):
        """
        Returns results table data structure
        :param scenIds: scenario ids
        :param detNames: detector names
        :return: results table data structure
        """
        session = Session()
        dataRows = []
        for scenId in scenIds:
            scenario = session.query(Scenario).filter_by(id = scenId).first()
            for detName in detNames:
                detector = session.query(Detector).filter_by(name = detName).first()
                idSet = session.query(IdentificationSet).filter_by(scenario = scenario,
                                                                   detector = detector).first()
                if idSet:
                    dataRow = {}
                    dataRow['detectorName']    = detector.name
                    dataRow['replayName']      = detector.replay.name
                    dataRow['scenId']          = scenario.id
                    dataRow['materialAndExposure'] = {scen_mat.material.name: scen_mat.dose for scen_mat in scenario.scen_materials}
                    dataRow['materialAndExposure'].update({scen_mat.material.name: scen_mat.dose for scen_mat in scenario.scen_bckg_materials})
                    dataRow['influences']      = [infl.name for infl in scenario.influences]
                    dataRow['acqTime']         = scenario.acq_time
                    dataRow['replication']     = scenario.replication
                    dataRows.append(dataRow)
        return dataRows


    def getPlotData(self, getX, getY, getZ=None):
        x, y, z = [],[],[]
        for dataRow in self.tableData:
            _x, _y, _z = getX(dataRow), getY(dataRow), getZ(dataRow) if getZ else None
            if _x is not None and _y is not None and (getZ is None or _z is not None):
                x.append(_x)
                y.append(_y)
                z.append(_z)
        if getZ: return x, y, z
        else: return x, y


    def getDetector(self, dataRow):
        """
        Returns detector name for the given data row
        :param dataRow: data row in the result table
        :return: detector name
        """
        return dataRow['detectorName']


    def getReplayName(self, dataRow):
        """
        Returns replay name for the given data row
        :param dataRow: data row in the result table
        :return: replay name
        """
        return dataRow['replayName']


    def getDose(self, dataRow, matName):
        """
        Returns material dose for the given data row
        :param dataRow: data row in the result table
        :param matName: material name
        :return: dose
        """
        return dataRow['materialAndExposure'].get(matName, 0)


    def getAcqTime(self, dataRow):
        """
        Returns acquisition time for the given data row
        :param dataRow: data row in the result table
        :return: acquisition time
        """
        return dataRow['acqTime']


    def getInfluence(self, dataRow, filterSet):
        """
        Returns influences for the given data row and filter set
        :param dataRow: data row in the result table
        :param filterSet: filter Set
        :return: influences
        """
        influences = list(set(dataRow['influences']) & filterSet)
        if influences: return influences[0]


    def getReportScore(self, dataRow, which):
        '''
        :param dataRow:
        :param which: either 'ir', 'im', 'imr', 'ccc', 'ic'
        :return:
        '''

        return dataRow['reportScores'][which.lower()]


    def getReportCounts(self, dataRow, which, matName):
        """
        :param dataRow:
        :param which: either 'falsePositives', 'falseNegatives', 'correctMatches'
        :param matName: material name of interest
        :return: number of reports that had the matetial show up in one of the 3 lists above
        """
        resultKeys = {'False Positives':'falsePositives',
                      'False Negatives':'falseNegatives',
                      'Correct Matches':'correctMatches'}

        return sum(1 for result in dataRow['compiledResults'] if matName in result[resultKeys[which]])

    @pyqtSlot(str)
    def on_cmbXaxis_currentTextChanged(self, text):
        """
        Listens for X column change
        """
        self.firstColumnChanged('X', text)

    @pyqtSlot(str)
    def on_cmbYaxis_currentTextChanged(self, text):
        """
        Listens for Y column change
        """
        self.firstColumnChanged('Y', text)

    @pyqtSlot(str)
    def on_cmbZaxis_currentTextChanged(self, text):
        """
        Listens for Z column change
        """
        self.firstColumnChanged('Z', text)

    def firstColumnChanged(self, axis, text):
        cmbMat = getattr(self, 'cmb' + axis + 'mat')
        txtMat = getattr(self, 'txt' + axis + 'mat')
        txtMat.hide()
        cmbMat.hide()

        if text == 'Influence': pass

        elif text in ['Dose', 'False Positives', 'False Negatives', 'Correct Matches']:
            cmbMat.show()
            txtMat.show()

    @pyqtSlot(bool)
    def on_btnViewPlot_clicked(self, checked):
        funcs = []
        titles = []
        for axis in ['X', 'Y', 'Z']:
            cmbAxis = getattr(self, 'cmb' + axis + 'axis').currentText()
            matName = getattr(self, 'cmb' + axis + 'mat').currentText()

            title = cmbAxis

            if cmbAxis in ['False Positives', 'False Negatives', 'Correct Matches']:
                func = partial(self.getReportCounts, which=cmbAxis, matName=matName)
                title += ' of ' + matName

            elif cmbAxis == 'Dose':
                func = partial(self.getDose, matName=matName)
                title += ' Rate ' + matName

            elif cmbAxis in ['IC', 'IM', 'IR', 'IMR', 'CCC']:
                func = partial(self.getReportScore, which=cmbAxis)

            elif cmbAxis == 'Detector':
                func = self.getDetector

            elif cmbAxis == 'Replay':
                func = self.getReplayName

            elif cmbAxis == 'Time':
                func = self.getAcqTime

            funcs.append(func)
            titles.append(title)
        data = self.getPlotData(*funcs)
        dialog = QDialog()
        layout = QHBoxLayout()
        layout.addWidget(LinePlot(data, titles))
        dialog.setLayout(layout)
        dialog.exec_()

