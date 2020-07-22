###############################################################################
# Copyright (c) 2018 Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory
#
# Written by J. Chavez, S. Czyz, G. Kosinovsky, V. Mozin, S. Sangiorgio
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
This module defines the main UI of RASE
"""

import csv
import subprocess

from PyQt5.QtCore import QPoint, Qt, QSize, QObject, pyqtSlot, pyqtSignal
from PyQt5.QtGui import QFont, QTextDocument, QAbstractTextDocumentLayout, QColor
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QMenu, \
    QAction, QMessageBox, QAbstractItemView, QStyledItemDelegate, QStyle, QFileDialog, \
    QHeaderView, QDialog, QProgressDialog, QCheckBox
from matplotlib import rcParams
from sqlalchemy import or_
from sqlalchemy.sql import select
from mako.template import Template
from math import pow
import pandas as pd

from src.correspondence_table_dialog import CorrespondenceTableDialog
from src.detector_dialog import DetectorDialog
from src.rase_functions import *
from src.rase_functions import _getCountsDoseAndSensitivity
from src.progressbar_dialog import ProgressBar
from src.rase_settings import RaseSettings
from src.replay_dialog import ReplayDialog
from src.scenario_dialog import ScenarioDialog
from src.settings_dialog import SettingsDialog
from src.table_def import IdentificationSet, ScenarioGroup, ScenarioMaterial, \
    scen_infl_assoc_tbl, CorrespondenceTableElement, CorrespondenceTable
from src.view_results_dialog import ViewResultsDialog
from src.help_dialog import HelpDialog
from src.qt_utils import QSignalWait

rcParams['backend'] = 'Qt5Agg'
from src.ui_generated import ui_rase, ui_about_dialog, ui_input_random_seed
from src.table_def import Scenario, Detector, Session, ResultsTranslator, Replay, SampleSpectraSeed, \
    BackgroundSpectrum, Material

from .manage_replays_dialog import ManageReplaysDialog
from .random_seed_dialog import RandomSeedDialog
from .create_base_spectra_dialog import CreateBaseSpectraDialog

from itertools import product

SCENARIO_ID, MATER_EXPOS, BCKRND, INFLUENCES, ACQ_TIME, REPLICATION = range(6)
DETECTOR, REPLAY, REPL_SETTS = range(3)

# On Windows platforms, pass this startupinfo to avoid showing the console when running a process via popen
popen_startupinfo = None
if sys.platform.startswith("win"):
    popen_startupinfo = subprocess.STARTUPINFO()
    popen_startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    popen_startupinfo.wShowWindow = subprocess.SW_HIDE


class Rase(ui_rase.Ui_MainWindow, QMainWindow):
    def __init__(self, args):
        QMainWindow.__init__(self)
        self.setupUi(self)
        self.setAcceptDrops(True)
        self.settings = RaseSettings()
        # random seed and "random seed fixed" boolean not retained across sessions
        self.settings.setRandomSeed(self.settings.getRandomSeedDefault())
        self.settings.setRandomSeedFixed(self.settings.getRandomSeedFixedDefault())
        self.help_dialog = None
        self.addIsotopeToCorrTable = False
        self.new_replay = None
        self.result_super_map = None
        self.scenario_stats_df = pd.DataFrame()
        self.setFocusPolicy(Qt.StrongFocus)

        # change fonts if on Mac
        if sys.platform == 'darwin':
            font = QFont()
            font.setPointSize(12)
            self.tblScenario.setFont(font)
            self.tblDetectorReplay.setFont(font)

        # setup table properties
        self.tblScenario.setColumnCount(6)
        self.setTableHeaders()
        self.tblScenario.horizontalHeaderItem(MATER_EXPOS).setToolTip('Dose = (\u00B5Sv/h), <i>Flux = (\u03B3/('
                                                                       'cm\u00B2s))<\i>')
        self.tblScenario.horizontalHeaderItem(BCKRND).setToolTip('Dose = (\u00B5Sv/h), <i>Flux = (\u03B3/('
                                                                       'cm\u00B2s))<\i>')
        self.tblScenario.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tblScenario.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tblScenario.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tblScenario.setItemDelegate(HtmlDelegate())
        self.tblScenario.setSortingEnabled(True)
        self.tblScenario.horizontalHeader().setDefaultSectionSize(140)
        # self.tblScenario.setColumnWidth(2, 140)
        # self.tblScenario.setHorizontalHeaderItem()
        self.tblScenario.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        # self.tblScenario.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
        self.tblScenario.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        # self.tblScenario.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        print(self.tblScenario.columnWidth(2))
        # self.tblScenario.resizeColumnsToContents()

        self.tblDetectorReplay.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tblDetectorReplay.setColumnCount(3)
        self.detectorHorizontalHeaderLabels = ['Instrument', 'Replay', 'Replay Settings']
        self.tblDetectorReplay.setHorizontalHeaderLabels(self.detectorHorizontalHeaderLabels)
        self.tblDetectorReplay.setItemDelegate(HtmlDelegate())
        self.tblDetectorReplay.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tblDetectorReplay.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tblDetectorReplay.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tblDetectorReplay.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        dataDir = self.settings.getDataDirectory()

        if not os.path.exists(dataDir):
            os.makedirs(dataDir, exist_ok=True)
        initializeDatabase(self.settings.getDatabaseFilepath())
        self.populateAll()

        # connect selection changes to updating buttons and tables
        self.tblScenario.itemSelectionChanged.connect(self.updateDetectorColors)
        self.tblDetectorReplay.itemSelectionChanged.connect(self.updateScenarioColors)

        self.corrHash = {}
        #        self.isAfterCorrespondenceTableCall = False
        self.settings.setIsAfterCorrespondenceTableCall(self.settings.getIsAfterCorrespondenceTableCalldDefault())

        self.btnExportInstruments.clicked.connect(self.handleInstrumentExport)
        self.btnExportScenarios.clicked.connect(self.handleScenarioExport)
        self.btnImportScenarios.clicked.connect(self.handleScenarioImport)
        self.btnGenScenario.clicked.connect(self.genScenario)

    def handleInstrumentExport(self):
        """
        Exports Instrument to CSV
        """
        path = QFileDialog.getSaveFileName(self, 'Save File', self.settings.getLastDirectory(), 'CSV (*.csv)')
        if path[0]:
            with open(path[0], mode='w', newline='') as stream:
                writer = csv.writer(stream)
                writer.writerow(self.detectorHorizontalHeaderLabels)
                for row in range(self.tblDetectorReplay.rowCount()):
                    rowdata = []
                    for column in range(self.tblDetectorReplay.columnCount()):
                        item = self.tblDetectorReplay.item(row, column)
                        if item is not None:
                            rowdata.append(item.text())
                        else:
                            rowdata.append('')
                    writer.writerow(rowdata)

    def handleScenarioExport(self):
        """
        Exports Scenarios to XML
        """
        path = QFileDialog.getSaveFileName(self, 'Save File', self.settings.getLastDirectory(), 'XML (*.xml)')
        if path[0]:
            if len(self.tblScenario.selectedIndexes()) > 0:
                scenIds = self.getSelectedScenarioIds()
            else:
                scenIds = self.getAllScenarioIds()
            export_scenarios(scenIds, path[0])

    def handleScenarioImport(self):
        """
        Import Scenarios from XML
        """
        path = QFileDialog.getOpenFileName(self, 'Open File', self.settings.getLastDirectory(), 'XML (*.xml)')
        if path[0]:
            session = Session()
            try:
                # TODO: Obtain the scenario group name and description from the user
                print(str(path[0]))
                scenarios = import_scenarios(path[0], group_name="Imported", group_desc=str(path[0]))
            except Exception as e:
                QMessageBox.critical(self, 'Import Failed', f'Failed to import scenarios from XML<br><br>{str(e)}')
                session.rollback()
            else:
                session.commit()
                self.populateAll()

    def getCorrHash(self):
        """
        Reads the Correspondence Table and creates
        association of isotopes to correct and allowed ids
        :return: association of isotopes to correct and allowed ids
        """
        corrTable = Session().query(CorrespondenceTable).filter_by(is_default=True).one_or_none()
        if not corrTable:
            QMessageBox.critical(self, 'Set Correspondence Table', 'Must specify a Correspondence Table')
            return
        # if the corrHash dict has already been populated and the Correspondence Table Dialog has not
        # been called since it was populated, there is no need to re-populate it
        #        if self.corrHash and not self.isAfterCorrespondenceTableCall:
        if self.corrHash and not self.settings.getIsAfterCorrespondenceTableCall():
            return self.corrHash
        self.corrHash = {}
        # self.isAfterCorrespondenceTableCall = False
        self.settings.setIsAfterCorrespondenceTableCall(False)
        corTableRows = (Session().query(CorrespondenceTableElement).filter_by(corr_table_name=corrTable.name))
        for line in corTableRows:
            isotope = line.isotope.strip()
            # correct_ids is a list of ";" delimited strings
            correct_ids = [l.strip() for l in line.corrList1.split(';') if l.strip()]
            # allowed_ids is a single ";" delimited string
            allowed_ids = [l.strip() for l in line.corrList2.split(';') if l.strip()]
            self.corrHash[isotope] = [correct_ids, allowed_ids]
        return self.corrHash

    def getTpFpFn(self, results, scenarioIsotopes, backgroundIsotopes):
        """
        calculates True Positives, False Positives, False Negatives
        :return: True Positives, False Positives, False Negatives
        """
        allowed_list = []
        Tp = 0
        iso_id_required = 0
        FP_candidates = results
        # store source and background isotopes togeather with source/background info
        isoPairList = []
        for iso in scenarioIsotopes:
            isoPairList.append((iso, "source"))
        for iso in backgroundIsotopes:
            isoPairList.append((iso, "background"))

        for isoP in isoPairList:
            iso = isoP[0]
            if isoP[1] == "source":
                isSource = True
            else:
                isSource = False
            # get the correspondence table entry for this isotope
            # or use default names if nothing is specified
            # print("iso="+iso)
            # for isohash in self.getCorrHash():
            #     print("isohash="+isohash)
            isohash = self.getCorrHash()
            if iso not in isohash:
                if isSource:
                    tmp = re.split('(\d+)', iso)  # split by numbers
                    correct_ids = [iso, tmp[0] + '-' + ''.join(tmp[1:])]  # e.g. Am241 and Am-241
                    # print(correct_ids)
                    allowed_ids = []
                else:
                    correct_ids = []
                    allowed_ids = []

            else:
                correct_ids, allowed_ids = isohash[iso]
                # print("from corr table")
                # print("correct_ids: " + str(correct_ids))
                # print("allowed_ids: " + str(allowed_ids))

            # if the correct_id list for this isotope is empty,
            # then we interpret it as if this isotope does not need to be identified
            if correct_ids: iso_id_required += 1

            # check if any of the correct IDs are within the ID results
            found = [r for r in results if r in correct_ids]
            if found: Tp += 1

            # whatever was not found is a potential false positive
            FP_candidates = list(set(FP_candidates) - set(found))

            # Build the list of all allowed isotopes
            allowed_list += allowed_ids

        # Now remove the allowed isotopes from the false positive candidates
        FP_list = [iso for iso in FP_candidates if iso not in allowed_list]

        # now compute Fn, Fp
        Fn = iso_id_required - Tp
        Fp = len(FP_list)

        # print some debugging
        # print("FP final= ", FP_list)
        # print("allowed_ids= ", allowed_list)
        # print("len(scenarioIsotopes)= ", len(scenarioIsotopes))
        # print("Tp= ", Tp)
        # print("IDRequired= ", iso_id_required)
        # print("Fn= ", Fn)
        # print("# True Positives = " , Tp)
        # print("# False Positives = ", Fp)
        # print("# False Negatives = ", Fn)

        return Tp, Fn, Fp

    def setTableHeaders(self):
        self.scenarioHorizontalHeaderLabels = ['ID', 'Sources', 'Backgrounds',
                                               'Influences', 'AcqTime (s)', 'Replication']
        self.tblScenario.setHorizontalHeaderLabels(self.scenarioHorizontalHeaderLabels)


    def populateAll(self):
        """
        Repopulate scenario, instrument/replay, and scenario-group combo. good to call after initializeDatabase
        """
        self.populateScenarios()
        self.populateDetectorReplays()
        self.populateScenarioGroupCombo()

    def populateScenarioGroupCombo(self):
        currentSelection = self.cmbScenarioGroups.currentText()
        self.cmbScenarioGroups.clear()
        self.cmbScenarioGroups.addItem('All Scenario Groups')
        for scenGrp in Session().query(ScenarioGroup):
            self.cmbScenarioGroups.addItem(scenGrp.name)
        if currentSelection:
            self.cmbScenarioGroups.setCurrentText(currentSelection)

    def populateScenarios(self):
        """shows scenarios in main screen scenario table"""
        # Disable sorting while setting/inserting items to avoid crashes
        self.tblScenario.setSortingEnabled(False)

        session = Session()
        # select scenarios to display based on search criteria
        scenSearch = self.txtScenarioSearch.text()
        if scenSearch:
            scenIds = set()
            connection = Session().get_bind().connect()
            for searchStr in scenSearch.split():
                # materials search
                stmt = select([ScenarioMaterial]).where(ScenarioMaterial.material_name.ilike('%' + searchStr + '%'))
                scenIds |= {row.scenario_id for row in connection.execute(stmt)}

                # influences search
                stmt = select([scen_infl_assoc_tbl]).where(
                    scen_infl_assoc_tbl.c.influence_name.ilike('%' + searchStr + '%'))
                scenIds |= {row.scenario_id for row in connection.execute(stmt)}
            scenarios = {session.query(Scenario).get(scenId) for scenId in scenIds}
        else:
            scenarios = list(session.query(Scenario))

        # select scenarios based on scenario group
        if self.cmbScenarioGroups.currentIndex() > 0:
            scenGrpId = session.query(ScenarioGroup).filter_by(name=self.cmbScenarioGroups.currentText()).first().id
            scenarios = [scenario for scenario in scenarios if scenario.scen_group_id == scenGrpId]

        self.tblScenario.setRowCount(len(scenarios))
        for row, scenario in enumerate(scenarios):
            self.tblScenario.setRowHeight(row, 22)

            item = QTableWidgetItem(scenario.id)
            item.setData(Qt.UserRole, scenario.id)
            self.tblScenario.setItem(row, SCENARIO_ID, item)
            matExp = [f'{scen_mat.material.name}({scen_mat.dose:.5g})' for scen_mat in scenario.scen_materials]
            self.tblScenario.setItem(row, MATER_EXPOS, QTableWidgetItem(', '.join(matExp)))
            # TODO place correct data in BCKRND column
            bckgMatExp = [f'{scen_mat.material.name}({scen_mat.dose:.5g})' for scen_mat in scenario.scen_bckg_materials]
            self.tblScenario.setItem(row, BCKRND, QTableWidgetItem(', '.join(bckgMatExp)))
            self.tblScenario.setItem(row, INFLUENCES,
                                     QTableWidgetItem(', '.join(infl.name for infl in scenario.influences)))
            self.tblScenario.setItem(row, ACQ_TIME, QTableWidgetItem(str(scenario.acq_time)))
            self.tblScenario.setItem(row, REPLICATION, QTableWidgetItem(str(scenario.replication)))

        # color and resize
        self.updateScenarioColors()
        # self.tblScenario.resizeColumnsToContents()
        self.tblScenario.resizeRowsToContents()

        # Re-enable sorting
        self.tblScenario.setSortingEnabled(True)

    def populateDetectorReplays(self):
        """shows scenarios in rase main screen scenario table"""
        # Disable sorting while setting/inserting items to avoid crashes
        self.tblDetectorReplay.setSortingEnabled(False)

        session = Session()
        detSearch = self.txtDetectorSearch.text()
        if detSearch:
            detNames = set()
            connection = Session().get_bind().connect()
            for searchStr in detSearch.split():
                # materials search
                stmt = select([Detector]).where(or_(Detector.name.ilike('%' + searchStr + '%'),
                                                    Detector.replay_name.ilike('%' + searchStr + '%')))
                detNames |= {row.name for row in connection.execute(stmt)}

            detectors = {session.query(Detector).get(detName) for detName in detNames}
        else:
            detectors = list(session.query(Detector))
        self.tblDetectorReplay.setRowCount(len(detectors))

        for row, detector in enumerate(detectors):
            self.tblDetectorReplay.setRowHeight(row, 22)

            item = QTableWidgetItem(detector.name)
            item.setData(Qt.UserRole, detector.name)
            self.tblDetectorReplay.setItem(row, DETECTOR, item)
            if detector.replay:
                item = QTableWidgetItem(detector.replay.name)
                item.setData(Qt.UserRole, detector.replay.name)
                self.tblDetectorReplay.setItem(row, REPLAY, item)
                self.tblDetectorReplay.setItem(row, REPL_SETTS, QTableWidgetItem(detector.replay.settings))
            else:
                empty_item = QTableWidgetItem("")
                empty_item.setData(Qt.UserRole, "")
                self.tblDetectorReplay.setItem(row, REPLAY, empty_item)
                self.tblDetectorReplay.setItem(row, REPL_SETTS, QTableWidgetItem(empty_item))

        self.updateDetectorColors()
        # self.tblDetectorReplay.resizeColumnsToContents()
        self.tblDetectorReplay.resizeRowsToContents()

        # Re-enable sorting
        self.tblDetectorReplay.setSortingEnabled(True)

    def updateDetectorColors(self):
        """
        Updates the colors of the detectors in the instrument list
        """
        session = Session()
        selScenarioIds = self.getSelectedScenarioIds()
        scenario = session.query(Scenario).filter_by(id=selScenarioIds[0]).first() if len(selScenarioIds) == 1 else None

        for row in range(self.tblDetectorReplay.rowCount()):
            item = self.tblDetectorReplay.item(row, DETECTOR)
            detTxt = item.data(Qt.UserRole)
            detector = session.query(Detector).get(detTxt)
            toolTip = None

            detectorColor = 'green'
            procphase = ''
            for scenID in selScenarioIds:
                scenario = session.query(Scenario).filter_by(id=scenID).first()
                if (detectorColor == 'green' and session.query(IdentificationSet).filter_by(
                                                    scenario=scenario, detector=detector).first() and
                    os.path.exists(get_sample_dir(self.settings.getSampleDirectory(), detector, scenario.id)) and
                    glob.glob(get_sample_dir(self.settings.getSampleDirectory(), detector, scenario.id) + '/*/')):
                    procphase = 'Replay'
                elif scenario and os.path.exists(get_sample_dir(self.settings.getSampleDirectory(), detector,
                                                                    scenario.id)) and detectorColor != 'black':
                    detectorColor = 'orange'
                    procphase = 'Spectrum generation'
                else:
                    detectorColor = 'black'

            if len(selScenarioIds) != 0 and detectorColor != 'black':
                detTxt = '<font color=' + detectorColor + '>' + detector.name + '</font>'
                if len(selScenarioIds) == 1:
                    toolTip = procphase + ' results available for ' + detector.name + \
                              ' and scenario: ' + scenario.id
                else:
                    toolTip = procphase + ' results available for ' + detector.name + \
                              ' and selected scenarios'

            item.setText(detTxt)
            item.setToolTip(toolTip)

            # replay
            replay = detector.replay
            if replay:
                replTxt = replay.name
                toolTip = None
                item = self.tblDetectorReplay.item(row, REPLAY)
                if replay and replay.exe_path and replay.is_cmd_line:
                    replTxt = '<font color="green">' + replay.name + '</font>'
                    toolTip = 'Cmd line replay tool available for ' + detector.name
                item.setText(replTxt)
                item.setToolTip(toolTip)

        self.updateActionButtons()

    def updateScenarioColors(self):
        """
        Updates the colors of all the scenarios
        """
        self.tblScenario.setSortingEnabled(False)
        session = Session()
        selDetectorNames = self.getSelectedDetectorNames()

        for row in range(self.tblScenario.rowCount()):

            s_item = self.tblScenario.item(row, SCENARIO_ID)
            scenario = session.query(Scenario).get(s_item.data(Qt.UserRole))
            cTxt = 'g'  # color text (for scenario)
            mbicTxt = False  # material, background, influence color text
            mat_toolTip = []
            bg_toolTip = []
            inf_toolTip = []
            s_toolTip = []
            hold_matColor = [False] * len(scenario.scen_materials)
            hold_bgColor = [False] * len(scenario.scen_bckg_materials)
            hold_inflColor = [False] * len(scenario.influences)

            if not selDetectorNames:
                item = self.tblScenario.item(row, MATER_EXPOS)
                txtExp = []
                for index, scenMat in enumerate(scenario.scen_materials):
                    if scenMat.fd_mode == 'DOSE':
                        scenExpTxt = (f'{scenMat.material_name}({scenMat.dose:.5g})')
                    else:
                        scenExpTxt = ('<i>' + f'{scenMat.material_name}({scenMat.dose:.5g})' + '</i>')
                    txtExp.append(scenExpTxt)
                item.setText(', '.join(txtExp))
                item.setToolTip('')

                item = self.tblScenario.item(row, BCKRND)
                txtExp = []
                for index, scenMat in enumerate(scenario.scen_bckg_materials):
                    if scenMat.fd_mode == 'DOSE':
                        scenExpTxt = (f'{scenMat.material_name}({scenMat.dose:.5g})')
                    else:
                        scenExpTxt = ('<i>' + f'{scenMat.material_name}({scenMat.dose:.5g})' + '</i>')
                    txtExp.append(scenExpTxt)
                item.setText(', '.join(txtExp))
                item.setToolTip('')

                item = self.tblScenario.item(row, INFLUENCES)
                txtExp = []
                for index, scenInfluence in enumerate(scenario.influences):
                    scenExpTxt = scenInfluence.name
                    txtExp.append(scenExpTxt)
                item.setText(', '.join(txtExp))
                item.setToolTip('')

                scenTxt = scenario.id
                s_item.setText(scenTxt)
                s_item.setToolTip('')

            else:
                for det_index, detector_name in enumerate(selDetectorNames):
                    detector = session.query(Detector).filter_by(name=detector_name).first()
                    if detector:
                        det_mats_d = set(baseSpectrum.material.name for baseSpectrum in detector.base_spectra if
                                         isinstance(baseSpectrum.rase_sensitivity, float))
                        det_mats_f = set(baseSpectrum.material.name for baseSpectrum in detector.base_spectra if
                                         isinstance(baseSpectrum.flux_sensitivity, float))
                        detInfluences = [detInfluence.influence for detInfluence in detector.influences]

                        # TODO: combine this and background into one loop
                        # set material/exposure
                        item = self.tblScenario.item(row, MATER_EXPOS)
                        txtExp = []
                        for index, scenMat in enumerate(scenario.scen_materials):
                            if not (((scenMat.material_name in det_mats_d) and scenMat.fd_mode == 'DOSE') or
                                    ((scenMat.material_name in det_mats_f) and scenMat.fd_mode == 'FLUX')):
                                mbicTxt = True
                                expColor = True
                                if detector:
                                    mat_toolTip.append(detector.name + ' is missing base spectra for this scenario')
                                    s_toolTip.append(detector.name + ' is missing base spectra for this scenario')
                            else:
                                expColor = False or hold_matColor[index]
                            if det_index == len(selDetectorNames) - 1:
                                scenExpTxt = '<font color="red">' + scenMat.material.name + '</font>' if expColor \
                                    else scenMat.material.name
                                if scenMat.fd_mode == 'DOSE':
                                    txtExp.append(f'{scenExpTxt}({scenMat.dose:.5g})')
                                else:
                                    txtExp.append('<i>' + f'{scenExpTxt}({scenMat.dose:.5g})' + '</i>')
                            hold_matColor[index] = expColor
                        if det_index == len(selDetectorNames) - 1:
                            item.setText(', '.join(txtExp))
                            item.setToolTip(',\n'.join(mat_toolTip))

                        # set background material/exposure
                        item = self.tblScenario.item(row, BCKRND)
                        txtExp = []
                        for index, scenMat in enumerate(scenario.scen_bckg_materials):
                            if not (((scenMat.material_name in det_mats_d) and scenMat.fd_mode == 'DOSE') or
                                    ((scenMat.material_name in det_mats_f) and scenMat.fd_mode == 'FLUX')):
                                mbicTxt = True
                                expColor = True
                                bg_toolTip.append(detector.name + ' is missing background spectra for this scenario')
                                s_toolTip.append(detector.name + ' is missing background spectra for this scenario')
                            else:
                                expColor = False or hold_bgColor[index]
                            if det_index == len(selDetectorNames) - 1:
                                scenExpTxt = '<font color="red">' + scenMat.material.name + '</font>' if expColor \
                                    else scenMat.material.name
                                if scenMat.fd_mode == 'DOSE':
                                    txtExp.append(f'{scenExpTxt}({scenMat.dose:.5g})')
                                else:
                                    txtExp.append('<i>' + f'{scenExpTxt}({scenMat.dose:.5g})' + '</i>')
                            hold_bgColor[index] = expColor
                        if det_index == len(selDetectorNames) - 1:
                            item.setText(', '.join(txtExp))
                            item.setToolTip(',\n'.join(bg_toolTip))

                        # set influences
                        item = self.tblScenario.item(row, INFLUENCES)
                        txtExp = []
                        for index, scenInfluence in enumerate(scenario.influences):
                            if scenInfluence not in detInfluences:
                                mbicTxt = True
                                expColor = True
                                inf_toolTip.append(detector.name + ' is missing influences for this scenario')
                                s_toolTip.append(detector.name + ' is missing influences for this scenario')
                            else:
                                expColor = False or hold_inflColor[index]
                            if det_index == len(selDetectorNames) - 1:
                                scenExpTxt = '<font color="red">' + scenInfluence.name + '</font>' if expColor else \
                                    scenInfluence.name
                                txtExp.append(scenExpTxt)
                            hold_inflColor[index] = expColor
                        if det_index == len(selDetectorNames) - 1:
                            item.setText(', '.join(txtExp))
                            item.setToolTip(',\n'.join(inf_toolTip))

                        # set scenario
                        if (session.query(IdentificationSet).filter_by(scenario=scenario,
                                                                       detector=detector).first() and
                                            os.path.exists(get_sample_dir(self.settings.getSampleDirectory(),
                                                                          detector, scenario.id)) and
                                            glob.glob(get_sample_dir(self.settings.getSampleDirectory(),
                                                                          detector, scenario.id) + '/*/')):
                            s_toolTip.append('Identification results available for ' + detector.name +
                                             ' and this scenario')
                        elif os.path.exists(get_sample_dir(self.settings.getSampleDirectory(),
                                                           detector, scenario.id)) and cTxt != 'k':
                            cTxt = 'o'
                            s_toolTip.append('Sample spectra available for ' + detector.name + ' and this scenario')
                        else:
                            cTxt = 'k'
                        if det_index == len(selDetectorNames) - 1:
                            if cTxt == 'g':
                                scenTxt = '<font color="green">' + scenario.id + '</font>'
                            elif cTxt == 'o':
                                scenTxt = '<font color="orange">' + scenario.id + '</font>'
                            else:
                                scenTxt = scenario.id
                            s_item.setText(scenTxt)
                            s_item.setToolTip(',\n'.join(s_toolTip))

                if mbicTxt:
                    scenTxt = '<font color="red">' + scenario.id + '</font>'
                    s_item.setText(scenTxt)

        self.updateActionButtons()

        self.tblScenario.setSortingEnabled(True)

    def updateActionButtons(self):
        """
        Handles enabling and disabling of Action Buttons
        """
        scenIds = self.getSelectedScenarioIds()
        selDetectorNames = self.getSelectedDetectorNames()

        if not (len(scenIds) and len(selDetectorNames)):
            # clear buttons
            for button in [self.btnGenScenario, self.btnGenerate, self.btnRunReplay, self.btnViewResults,
                           self.btnRunResultsTranslator, self.btnImportIDResults]:
                button.setEnabled(False)
                button.setToolTip('Must choose scenario and instrument')
            return

        session = Session()

        prev_det_sample = False
        prev_det_replay = False
        prev_det_transl = False
        prev_det_result = False

        for det_index, detector_name in enumerate(selDetectorNames):

            detMissingSpectra = []
            detMissingInfluence = []
            detector = session.query(Detector).filter_by(name=detector_name).first()

            if detector:
                det_mats_d = set(baseSpectrum.material.name for baseSpectrum in detector.base_spectra if
                                isinstance(baseSpectrum.rase_sensitivity, float))
                det_mats_f = set(baseSpectrum.material.name for baseSpectrum in detector.base_spectra if
                                    isinstance(baseSpectrum.flux_sensitivity, float))
                det_infl = set(detInfl.influence.name for detInfl in detector.influences)
            samplesExists = []
            templatedSamplesExists = []
            replayOutputExists = []
            resultsExists = []

            for scenId in scenIds:
                scenario = session.query(Scenario).filter_by(id=scenId).first()
                if scenario:
                    scen_mats = set((scenMat.material.name, scenMat.fd_mode) for scenMat in
                                    scenario.scen_materials + scenario.scen_bckg_materials)
                    scen_infl = set(influence.name for influence in scenario.influences)

                    for instance in scen_mats:
                        if instance[1] == 'DOSE':
                            if instance[0] not in det_mats_d:
                                detMissingSpectra.append(scenId)
                        else:
                            if instance[0] not in det_mats_f:
                                detMissingSpectra.append(scenId)

                    if not scen_infl <= det_infl: detMissingInfluence.append(scenId)

                    samplesExists.append(
                        os.path.exists(get_sample_dir(self.settings.getSampleDirectory(), detector, scenId)))
                    templatedSamplesExists.append(
                        os.path.exists(get_replay_input_dir(self.settings.getSampleDirectory(), detector, scenId)))
                    # Replay tool output files and results files are expected to end in ".n42" or ".res".
                    # Check explicitly in case other output is present (e.g. from replay tool or translator)
                    output_dir = get_replay_output_dir(self.settings.getSampleDirectory(), detector, scenId)
                    replayOutputExists.append(files_endswith_exists(output_dir, (".n42", ".res")))
                    results_dir = get_results_dir(self.settings.getSampleDirectory(), detector, scenId)
                    resultsExists.append(files_endswith_exists(results_dir, (".n42", ".res")))

            #         samplesExists.append(
            #             os.path.exists(get_sample_dir(self.settings.getSampleDirectory(), detector, scenId)))
            #         templatedSamplesExists.append(
            #             os.path.exists(get_replay_input_dir(self.settings.getSampleDirectory(), detector, scenId)))
            #         # Replay tool output files and results files are expected to end in ".n42" or ".res".
            #         # Check explicitly in case other output is present (e.g. from replay tool or translator)
            #         output_dir = get_replay_output_dir(self.settings.getSampleDirectory(), detector, scenId)
            #         replayOutputExists.append(files_endswith_exists(output_dir, (".n42", ".res")))
            #         results_dir = get_results_dir(self.settings.getSampleDirectory(), detector, scenId)
            #         resultsExists.append(files_endswith_exists(results_dir, (".n42", ".res")))

            if detMissingSpectra or detMissingInfluence or prev_det_sample:
                # generate sample is possible only if no missing base spectra or influences
                missingScenarios = missingInfluences = ''
                if detMissingSpectra:
                    missingScenarios = "Missing base spectra for scenarios:<br>" + '<br>'.join(detMissingSpectra)
                if detMissingInfluence:
                    missingInfluences = "<br>Missing influences for scenarios:<br>" + '<br>'.join(detMissingInfluence)
                self.btnGenScenario.setEnabled(False)
                self.btnGenScenario.setToolTip(missingScenarios + missingInfluences)
                self.btnGenerate.setEnabled(False)
                self.btnGenerate.setToolTip(missingScenarios + missingInfluences)
                self.btnRunReplay.setEnabled(False)
                self.btnRunReplay.setToolTip(missingScenarios + missingInfluences)
                self.btnRunResultsTranslator.setEnabled(False)
                self.btnRunResultsTranslator.setToolTip('')
                self.btnImportIDResults.setEnabled(False)
                self.btnImportIDResults.setToolTip('Select only one scenario and generate sample spectra')
                self.btnViewResults.setEnabled(False)
                self.btnViewResults.setToolTip('')
                prev_det_sample = True
            else:
                # generate samples button:
                if not detector.replay:
                    self.btnGenScenario.setEnabled(False)
                    self.btnGenScenario.setToolTip('No replay tool defined.')
                elif not detector.replay.exe_path or not detector.replay.is_cmd_line:
                    self.btnGenScenario.setEnabled(False)
                    self.btnGenScenario.setToolTip('Replay tool is not command line, must execute workflow manually.')
                else:
                    self.btnGenScenario.setEnabled(True)
                    self.btnGenScenario.setToolTip('')
                self.btnGenerate.setEnabled(True)
                self.btnGenerate.setToolTip('')

                # run replay button:
                if not prev_det_replay:
                    if not all(samplesExists) or (
                            (detector.replay and detector.replay.n42_template_path) and not all(templatedSamplesExists)):
                        self.btnRunReplay.setEnabled(False)
                        self.btnRunReplay.setToolTip('Sample spectra have not yet been generated or translated')
                        prev_det_replay = True
                    # FIXME: the following does not consider the case of a replay tool not from the command line
                    elif not (detector.replay and detector.replay.exe_path):
                        self.btnRunReplay.setEnabled(False)
                        self.btnRunReplay.setToolTip('No replay tool defined')
                        prev_det_replay = True
                    else:
                        self.btnRunReplay.setEnabled(True)
                        self.btnRunReplay.setToolTip('')

                # run results translator button:
                if not prev_det_transl:
                    if not (detector.resultsTranslator and detector.resultsTranslator.exe_path
                            and detector.resultsTranslator.is_cmd_line and all(replayOutputExists)):
                        self.btnRunResultsTranslator.setEnabled(False)
                        self.btnRunResultsTranslator.setToolTip('No command line resultsTranslator for selected instrument')
                        prev_det_transl = True
                    else:
                        self.btnRunResultsTranslator.setEnabled(True)
                        self.btnRunResultsTranslator.setToolTip('')

                # import results button:
                if not (len(selDetectorNames) == 1 and len(scenIds) == 1):
                    self.btnImportIDResults.setEnabled(False)
                    self.btnImportIDResults.setToolTip('Can only import one scenario at a time')
                elif not all(samplesExists):
                    self.btnImportIDResults.setEnabled(False)
                    self.btnImportIDResults.setToolTip('Generate samples first')
                else:
                    self.btnImportIDResults.setEnabled(True)
                    self.btnImportIDResults.setToolTip('')

                #view results button
                if not prev_det_result:
                    self.btnViewResults.setEnabled(True)
                    self.btnViewResults.setToolTip('')

                    if detector.resultsTranslator and detector.resultsTranslator.exe_path:
                        if not all(resultsExists):
                            self.btnViewResults.setEnabled(False)
                            self.btnViewResults.setToolTip('Not all results are available')
                            prev_det_result = True
                    else:
                        if not all(replayOutputExists):
                            self.btnViewResults.setEnabled(False)
                            self.btnViewResults.setToolTip('Not all results are available')
                            prev_det_result = True

    def getSelectedScenarioIds(self):
        """
        :return: selected scenario ids
        """
        return [self.tblScenario.item(row, SCENARIO_ID).data(Qt.UserRole)
                for row in set(index.row() for index in self.tblScenario.selectedIndexes())]

    def getAllScenarioIds(self):
        """
        :return: all scenarios ids currently listed in the scenario table
        """
        return [self.tblScenario.item(row, SCENARIO_ID).data(Qt.UserRole) for row in range(self.tblScenario.rowCount())]

    def getSelectedDetectorNames(self):
        """
        :return: Selected Instrument Names
        """
        return [self.tblDetectorReplay.item(row, DETECTOR).data(Qt.UserRole)
                for row in set(index.row() for index in self.tblDetectorReplay.selectedIndexes())]

    def getSelectedReplayNames(self):
        """
        :return: Selected Replay Names
        """
        return [self.tblDetectorReplay.item(row, REPLAY).data(Qt.UserRole)
                for row in set(index.row() for index in self.tblDetectorReplay.selectedIndexes())]

    @pyqtSlot(int, int)
    def on_tblScenario_cellDoubleClicked(self, row, col):
        """
        Listens for Scenario cell double click and launches edit_scenario()
        """
        id = strip_xml_tag(self.tblScenario.item(row, SCENARIO_ID).text())
        self.edit_scenario(id)

    def edit_scenario(self, id):
        """
        Launcehes ScenarionDialog
        """
        dialog = ScenarioDialog(self, id)
        if dialog.exec_():
            self.populateScenarios()
            self.populateScenarioGroupCombo()

    def edit_detector(self, detectorName):
        """
        Launches Instrument Dialog
        """
        if DetectorDialog(self, detectorName).exec_():
            self.populateDetectorReplays()

    @pyqtSlot(int, int)
    def on_tblDetectorReplay_cellDoubleClicked(self, row, col):
        """
        Listens for Instrument or Replay cell click and lunces correponding edit dialogs
        """
        if col == DETECTOR:
            detectorName = strip_xml_tag(self.tblDetectorReplay.item(row, col).text())
            self.edit_detector(detectorName)
        elif col == REPLAY:
            session = Session()
            if self.tblDetectorReplay.item(row, col):
                replay = session.query(Replay).filter_by(
                    name=self.tblDetectorReplay.item(row, col).data(Qt.UserRole)).first()
                resultsTranslator = session.query(ResultsTranslator).filter_by(
                    name=self.tblDetectorReplay.item(row, col).data(Qt.UserRole)).first()
                if ReplayDialog(self, replay, resultsTranslator).exec_() and self.new_replay:
                    # if replay is new, add the replay info to detector
                    detectorName = strip_xml_tag(self.tblDetectorReplay.item(row, DETECTOR).text())
                    detector = session.query(Detector).filter_by(name=detectorName).first()
                    detector.replay = self.new_replay
                    detector.resultsTranslator = session.query(ResultsTranslator).filter(
                        ResultsTranslator.name == detector.replay.name).first()
                    session.commit()
                    self.new_replay = None
                self.populateDetectorReplays()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Delete or e.key() == Qt.Key_Backspace:
            scenIds = self.getSelectedScenarioIds()
            delete_scenario(scenIds, self.settings.getSampleDirectory())
            self.populateAll()

    def focusInEvent(self, e):
        self.updateDetectorColors()
        self.updateScenarioColors()
        self.updateActionButtons()

    @pyqtSlot(QPoint)
    def on_tblDetectorReplay_customContextMenuRequested(self, point):
        """
        Handles "Edit" and "Delete" right click selections on the Instrument table
        """
        current_cell = self.tblDetectorReplay.itemAt(point)
        # show the context menu only if on an a valid part of the table
        if current_cell:
            row = current_cell.row()
            deleteAction = QAction('Delete Instrument', self)
            editAction = QAction('Edit Instrument', self)
            menu = QMenu(self.tblDetectorReplay)
            menu.addAction(deleteAction)
            menu.addAction(editAction)
            action = menu.exec_(self.tblDetectorReplay.mapToGlobal(point))
            session = Session()
            name = strip_xml_tag(self.tblDetectorReplay.item(row, 0).text())
            if action == deleteAction:
                if len(self.getSelectedScenarioIds()):
                    QMessageBox.critical(self, 'Scenario Selected',
                                         'Please Unselect All Scenarios Prior to Deleting Instrument')
                    return
                sssDelete = session.query(SampleSpectraSeed).filter(SampleSpectraSeed.det_name == name)
                sssDelete.delete()
                detReplayDelete = session.query(Detector).filter(Detector.name == name)
                detReplayDelete.delete()
                session.commit()
                self.populateAll()
            elif action == editAction:
                self.edit_detector(name)

    @pyqtSlot()
    def genScenario(self):
        """
        Launches a single button to do all processing (generate, replay, and translate)
        """
        #detector = session.query(Detector).filter_by(name=detNames[0]).first()
        replay_status = False
        translate_status = False
        spec_status = self.genSpectra()
        if spec_status:
            replay_status = self.runReplay()
            if replay_status:
                translate_status = self.runTranslator()
        self.on_action_complete(spec_status and replay_status and translate_status, "Scenarios processing")

    @pyqtSlot(bool)
    def on_btnGenerate_clicked(self, checked):
        status = self.genSpectra()
        self.on_action_complete(status, "Sample spectra generation")

    def genSpectra(self):
        """
        Launches generation of sample spectra
        """
        # get selected conditions
        session = Session()
        scenIds = self.getSelectedScenarioIds()
        detNames = self.getSelectedDetectorNames()

        # List of all [instrument,scenarios] combinations
        detector_scenarios = list(product(detNames, scenIds))

        replications = 0
        checked = False
        # Check if any sample spectra may be overwritten
        for detName, scenId in detector_scenarios:
            detector = session.query(Detector).filter_by(name=detName).first()
            directoryName = get_sample_dir(self.settings.getSampleDirectory(), detector, scenId)
            scenario = session.query(Scenario).filter_by(id=scenId).first()
            if os.path.exists(directoryName):
                if not checked:
                    answer = QMessageBox(QMessageBox.Question, 'Sample spectra already exists',
                                                  'Sample spectra for instrument: ' + detector.name +
                                                    ' and scenario: ' + scenario.id +
                                                  ' already exists.  Select yes to overwrite or no to skip this case')
                    answer.addButton(QMessageBox.Yes)
                    answer.addButton(QMessageBox.No)
                    checkit = QCheckBox("Use this selection for all scenarios")
                    checkit.setEnabled(True)
                    answer.setCheckBox(checkit)
                    ans_hold = answer.exec()
                    if ans_hold == QMessageBox.No:
                        detector_scenarios.remove((detName, scenId))
                        if checkit.isChecked():
                            checked = True
                            overwrite = False
                    elif ans_hold == QMessageBox.Yes:
                        shutil.rmtree(directoryName)
                        if checkit.isChecked():
                            checked = True
                            overwrite = True
                else:
                    if overwrite:
                        shutil.rmtree(directoryName)
                    else:
                        detector_scenarios.remove((detName, scenId))

            replications += scenario.replication
        session.close()

        # Test one single first to make sure things are working
        try:
            SampleSpectraGeneration(detector_scenarios, True).work()
        except Exception as e:
            QMessageBox.critical(self, 'Error!', 'Sample generation failed for ' + detName
                                 + '<br> If n42 template is set, please verify it is formatted correctly.<br><br>'
                                 + str(e))
            shutil.rmtree(directoryName)
            return False

        # now generate all samples
        bar = ProgressBar(self)
        bar.title.setText("Sample spectra generation in progress")
        bar.progress.setMaximum(replications)
        bar.run(SampleSpectraGeneration(detector_scenarios))

        godot = QSignalWait(bar.sig_finished)
        return godot.wait()

    @pyqtSlot(bool)
    def on_btnRunReplay_clicked(self, checked):
        status = self.runReplay()
        self.on_action_complete(status, "Run replay tool")

    def runReplay(self):
        """
        launches replay
        """
        session = Session()
        scenIds = self.getSelectedScenarioIds()
        detNames = self.getSelectedDetectorNames()
        sampleRootDir = self.settings.getSampleDirectory()

        # List of all [instrument,scenarios] combinations
        # detector_scenarios = list(product(detNames, scenIds))
        progress = QProgressDialog('Replay in progress...', None, 0,
                                   len(scenIds) + 1, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setMaximum(len(scenIds) + 1)
        for detName in detNames:
            detector = session.query(Detector).filter_by(name=detName).first()
            if detector.replay and detector.replay.exe_path:
                replayExe = [detector.replay.exe_path]
                progress.setValue(0)
                progress.setLabelText('Replay in progress for ' + detName + '...')
                if detector.replay.is_cmd_line:
                    for i, scenId in enumerate(scenIds, 1):
                        progress.setValue(i)

                        sampleDir = get_replay_input_dir(sampleRootDir, detector, scenId)
                        if not os.path.exists(sampleDir):
                            # TODO: eventually we will generate samples directly from here.
                            pass
                        try:
                            resultsDir = get_replay_output_dir(sampleRootDir, detector, scenId)
                            settingsList = detector.replay.settings.split(" ")
                            # FIXME: the following assumes that INPUTDIR and OUTPUTDIR are present only one time each in the settings
                            if "INPUTDIR" in settingsList:
                                settingsList[settingsList.index("INPUTDIR")] = sampleDir
                            if "OUTPUTDIR" in settingsList:
                                settingsList[settingsList.index("OUTPUTDIR")] = resultsDir

                            if os.path.exists(resultsDir):
                                shutil.rmtree(resultsDir)
                            os.makedirs(resultsDir, exist_ok=True)

                            # The stdout and stderr of the replay tool (if any) are sent to a log file
                            stdout_file = open(
                                os.path.join(get_sample_dir(sampleRootDir, detector, scenId), "replay_tool_output.log"),
                                mode='w')

                            # On Windows, running this from the binary produced by Pyinstaller
                            # with the ``--noconsole`` option requires redirecting everything
                            # (stdin, stdout, stderr) to avoid an OSError exception
                            # "[Error 6] the handle is invalid."
                            # See: https://github.com/pyinstaller/pyinstaller/wiki/Recipe-subprocess
                            # don't pass startup_info because it freezes execution of some replay tools
                            p = subprocess.Popen(replayExe + settingsList, stdin=subprocess.DEVNULL, stderr=stdout_file,
                                                 stdout=stdout_file, shell=False)
                            stdout_file.flush()
                            stdout_file.close()

                            # TODO: consolidate results of errors in one message box
                            stderr, stdout = p.communicate()
                            # if error:
                            #     QMessageBox.critical(self, 'Error','error message: ' + error)
                            #     return
                            importResultsDirectory(resultsDir, scenId, detName)
                        except Exception as e:
                            progress.setValue(len(scenIds) + 1)
                            QMessageBox.critical(self, 'Replay failed', 'Could not execute replay for instrument '
                                                 + detName + ' and scenario ' + scenId + '<br><br>' + str(e))
                            shutil.rmtree(resultsDir)
                            return
                    progress.setValue(len(scenIds) + 1)
                else:
                    for i, scenId in enumerate(scenIds, 1):
                        sampleDir = get_replay_input_dir(sampleRootDir, detector, scenId)
                        if not os.path.exists(sampleDir):
                            # TODO: eventually we will generate samples directly from here.
                            pass
                        resultsDir = get_replay_output_dir(sampleRootDir, detector, scenId)
                        if os.path.exists(resultsDir):
                            shutil.rmtree(resultsDir)
                        os.makedirs(resultsDir, exist_ok=True)
                        importResultsDirectory(resultsDir, scenId, detName)
                        # FIXME: this works only on Windows
                        os.startfile(detector.replay.exe_path)

                        QMessageBox.information(self, 'Manual Replay Tool',
                                                'Replay tool has been opened in a separate window and must be run manually.<br>' +
                                                'Press OK when done.<br><br>' +
                                                'Use the following settings:<br>' +
                                                f'Input folder:<br> {sampleDir}<br><br>' +
                                                f'Output folder:<br> {resultsDir}<br>')
                        # TODO: Check if the progress bar is handled in this case?
                    progress.setValue(len(scenIds) + 1)
                self.updateScenarioColors()
            else:
                progress.setValue(len(scenIds) + 1)
        return True
        # QMessageBox.information(self, 'Success!', 'Replay tool execution completed.')

    @pyqtSlot(bool)
    def on_btnRunResultsTranslator_clicked(self, checked):
        status = self.runTranslator()
        self.on_action_complete(status, "Result translation")

    def runTranslator(self):
        """
        Launches Translate Results
        """
        # user directory
        session = Session()
        scenIds = self.getSelectedScenarioIds()
        detNames = self.getSelectedDetectorNames()
        sampleRootDir = self.settings.getSampleDirectory()

        progress = QProgressDialog('Translation in progress...', None, 0, len(scenIds) + 1, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setMaximum(len(scenIds) + 1)
        for detector_index, detName in enumerate(detNames):
            detector = session.query(Detector).filter_by(name=detName).first()
            if not (detector.resultsTranslator and detector.resultsTranslator.exe_path
                    and detector.resultsTranslator.is_cmd_line):
                progress.setValue(len(scenIds) + 1)
                pass
            else:
                progress.setValue(0)
                progress.setLabelText('Translation in progress for ' + detName + '...')
                repName = self.getSelectedReplayNames()[detector_index]
                for i, scenId in enumerate(scenIds, 1):
                    progress.setValue(i)
                    resultsTranslator = session.query(ResultsTranslator).filter_by(name=repName).first()

                    # input dir to this module
                    input_dir = get_replay_output_dir(sampleRootDir, detector, scenId)
                    output_dir = get_results_dir(sampleRootDir, detector, scenId)

                    if not os.path.exists(input_dir):
                        QMessageBox.critical(self, 'Insufficient Data', 'Must Run Replay First')
                        return False

                    command = [resultsTranslator.exe_path]
                    if resultsTranslator.exe_path.endswith('.py'):
                        command = ["python", resultsTranslator.exe_path]

                    # FIXME: the following assumes that INPUTDIR and OUTPUTDIR are present only one time each in the settings
                    settingsList = resultsTranslator.settings.split(" ")
                    if "INPUTDIR" in settingsList:
                        settingsList[settingsList.index("INPUTDIR")] = input_dir
                    if "OUTPUTDIR" in settingsList:
                        settingsList[settingsList.index("OUTPUTDIR")] = output_dir

                    command = command + settingsList

                    try:
                        # On Windows, running this from the binary produced by Pyinstaller
                        # with the ``--noconsole`` option requires redirecting everything
                        # (stdin, stdout, stderr) to avoid an OSError exception
                        # "[Error 6] the handle is invalid."
                        # See: https://github.com/pyinstaller/pyinstaller/wiki/Recipe-subprocess
                        p = subprocess.run(command, stdout=subprocess.PIPE, stdin=subprocess.PIPE,
                                           stderr=subprocess.STDOUT, encoding='utf-8', check=True,
                                           startupinfo=popen_startupinfo)
                    except subprocess.CalledProcessError as e:
                        progress.setValue(len(scenIds) + 1)
                        log_fname = os.path.join(get_sample_dir(sampleRootDir, detector, scenId),
                                                 'results_translator_output.log')
                        log = open(log_fname, 'w')
                        log.write('### Command: ' + os.linesep)
                        log.write(' '.join(e.cmd) + os.linesep)
                        log.write('### Output: ' + os.linesep)
                        log.write(e.output)
                        log.close()
                        QMessageBox.critical(self, 'Error!',
                                             'Results translation exited with error code ' +
                                             str(e.returncode) + ' when running translator.<br><br>' +
                                             'Output log at: <br>' + log_fname)
                        shutil.rmtree(output_dir, ignore_errors=True)
                        return False
                    except Exception as e:
                        progress.setValue(len(scenIds) + 1)
                        QMessageBox.critical(self, 'Error!',
                                             'Results translation failed for instrument '
                                             + detName + ' and scenario ' + scenId + '<br><br>' + str(
                                                 e))
                        shutil.rmtree(output_dir, ignore_errors=True)
                        return False
                progress.setValue(len(scenIds) + 1)
        return True

    def on_action_complete(self, exit_status, action_str):
        """
        Displays message dialog when an action is completed
        """
        if exit_status:
            title = "Success!"
            message = f"{action_str.capitalize()} completed."
        else:
            title = f"{action_str.capitalize()} aborted"
            message = f"{action_str.capitalize()} aborted. Not all scenarios were processed."
        QMessageBox.information(self, title, message)
        # update the table colors
        self.updateScenarioColors()

    @pyqtSlot(bool)
    def on_actionCorrespondence_Table_triggered(self, checked):
        """
        Launches Correspondence Table Dialog
        """
        CorrespondenceTableDialog().exec_()
        # self.isAfterCorrespondenceTableCall = True
        self.settings.setIsAfterCorrespondenceTableCall(True)

    @pyqtSlot(bool)
    def on_btnImportIDResults_clicked(self, checked):
        """
        Imports output of replay tool by copying files to their expected location within RASE file structure
        """
        session = Session()
        scenId = self.getSelectedScenarioIds()[0]
        detName = self.getSelectedDetectorNames()[0]
        detector = session.query(Detector).filter_by(name=detName).first()
        options = QFileDialog.ShowDirsOnly
        if sys.platform.startswith('win'): options = QFileDialog.DontUseNativeDialog
        dirpath = QFileDialog.getExistingDirectory(self, 'Select folder of results for scenario: ' + scenId +
                                                   ' and instrument: ' + detName,
                                                   get_sample_dir(self.settings.getSampleDirectory(), detector, scenId),
                                                   options)
        if dirpath:
            resultsDir = get_replay_output_dir(self.settings.getSampleDirectory(), detector, scenId)
            if os.path.normpath(dirpath) != os.path.normpath(resultsDir):
                if os.path.exists(resultsDir):
                    shutil.rmtree(resultsDir)
                shutil.copytree(dirpath, resultsDir)

            importResultsDirectory(resultsDir, scenId, detName)

            self.updateScenarioColors()
            self.updateActionButtons()

    @pyqtSlot(bool)
    def on_actionReplay_Software_triggered(self, checked):
        """
        Launches Manage Replays tool
        """
        # ReplayListDialog(self).exec_()
        ManageReplaysDialog().exec_()
        self.populateDetectorReplays()

    @pyqtSlot(bool)
    def on_actionPreferences_triggered(self, checked):
        """
        Launches Preferences Dialog
        """
        dialog = SettingsDialog(self)
        if dialog.exec_():
            if dialog.dataDirectoryChanged:
                initializeDatabase(self.settings.getDatabaseFilepath())
                self.populateAll()

    @pyqtSlot(bool)
    def on_btnAddScenario_clicked(self, checked):
        """
        Handles adding new Scenario
        """
        dialog = ScenarioDialog(self)
        if dialog.exec_():
            self.populateScenarios()
            self.populateScenarioGroupCombo()

    @pyqtSlot(bool)
    def on_btnAddDetector_clicked(self, checked):
        """
        Handles adding new Detetor
        """
        if DetectorDialog(self).exec_():
            self.populateDetectorReplays()

    @pyqtSlot(QPoint)
    def on_tblScenario_customContextMenuRequested(self, point):
        """
        Handles "Edit" and "Delete" right click selections on the Scenario table
        """
        current_cell = self.tblScenario.itemAt(point)

        # show the context menu only if on an a valid part of the table
        if current_cell:
            row = current_cell.row()

            deleteAction = QAction('Delete Scenario', self)
            editAction = QAction('Edit Scenario', self)

            menu = QMenu(self.tblScenario)
            menu.addAction(deleteAction)
            menu.addAction(editAction)

            session = Session()
            id = strip_xml_tag(self.tblScenario.item(row, SCENARIO_ID).text())
            detNames = self.getSelectedDetectorNames()

            # The action to open the sample folders shows up only
            # if the sample folders exists and a detector is selected
            sampleDirs = []
            for detName in detNames:
                detector = session.query(Detector).filter_by(name=detName).first()
                dir = get_sample_dir(self.settings.getSampleDirectory(), detector, id)
                if os.path.exists(dir): sampleDirs.append(dir)
            if len(sampleDirs) > 1:
                action_label = 'Go To Sample Folders'
            else:
                action_label = 'Go To Sample Folder'
            goToFolderAction = QAction(action_label, self)
            if sampleDirs: menu.addAction(goToFolderAction)

            # execute actions
            action = menu.exec_(self.tblScenario.mapToGlobal(point))
            if action == deleteAction:
                delete_scenario([id], self.settings.getSampleDirectory())
                self.populateAll()
            elif action == goToFolderAction:
                for dir in sampleDirs:
                    fileBrowser = 'explorer' if sys.platform.startswith('win') else 'open'
                    subprocess.Popen([fileBrowser, dir])
            elif action == editAction:
                self.edit_scenario(id)

    @pyqtSlot(bool)
    def on_btnSampleDir_clicked(self, checked):
        """
        Opens the generated samples directory in File Explorer
        """
        fileBrowser = 'explorer' if sys.platform.startswith('win') else 'open'
        subprocess.Popen([fileBrowser, self.settings.getSampleDirectory()])

    @pyqtSlot(bool)
    def on_btnViewResults_clicked(self, checked):
        """
        Opens Results table
        """
        # need a correspondence table in order to display results!
        session = Session()
        default_corr_table = session.query(CorrespondenceTable).filter_by(is_default=True).one_or_none()
        if not default_corr_table:
            QMessageBox.critical(self, 'Error!', 'Please set a default correspondence table')
            return
        self.calculateScenarioStats(caller=self)

        ViewResultsDialog(self, self.getSelectedScenarioIds(), self.getSelectedDetectorNames()).exec_()

    def calculateScenarioStats(self, caller):
        """
        Calculates scenario stats
        """
        session = Session()
        corrTable = session.query(CorrespondenceTable).filter_by(is_default=True).one_or_none()
        corrTableRows = session.query(CorrespondenceTableElement).filter_by(corr_table_name=corrTable.name)
        # add background material rows to the correspondence table
        bckg_material_set = set()
        for scenId in self.getSelectedScenarioIds():
            scenario = session.query(Scenario).filter_by(id=scenId).first()
            bckg_material_set.update(scenario.get_bckg_material_names_no_shielding())
        corr_table_iso_set = set()
        for line in corrTableRows:
            corr_table_iso_set.add(line.isotope)
        isCorrTableUpdated = False
        for bckgMaterial in bckg_material_set:
            if bckgMaterial in corr_table_iso_set:
                continue
            print("BCKG NOT IN CORR TABLE")
            cb = QCheckBox("Edit the Correspondence Table Now")
            cb.setEnabled(True)
            msgbox = QMessageBox(QMessageBox.Question, bckgMaterial + ' is currently not in Correspondence Table',
                                 'Would you like to add ' + bckgMaterial + ' to the Correspondence Table?')
            msgbox.addButton(QMessageBox.Yes)
            msgbox.addButton(QMessageBox.No)
            msgbox.setCheckBox(cb)
            self.addIsotopeToCorrTable = msgbox.exec()
            if self.addIsotopeToCorrTable == QMessageBox.Yes:
                corrTsbleEntry = CorrespondenceTableElement(isotope=bckgMaterial, corrList1="", corrList2="")
                corrTable.corr_table_elements.append(corrTsbleEntry)
                # if "edit correspondence" table selected
                if bool(cb.isChecked()): CorrespondenceTableDialog().exec_()
        session.commit()

        sampleRootDir = self.settings.getSampleDirectory()
        session = Session()
        self.result_super_map = {}
        # for scenId in self.getSelectedScenarioIds():
        scen_det_list = list(product(self.getSelectedScenarioIds(), self.getSelectedDetectorNames()))

        columns = ['Det', 'Replay', 'Mat_Dose', 'Bkg_Mat_Dose', 'Mat_Flux', 'Bkg_Mat_Flux', 'Infl', 'AcqTime', 'Repl',
                   'PID', 'PID_L', 'PID_H', 'TP', 'FP', 'FN', 'C&C', 'C&C_L', 'C&C_H', 'Precision', 'Recall', 'F_Score']

        index = [scen_det[0] + "*" + scen_det[1] for scen_det in scen_det_list]
        self.scenario_stats_df = pd.DataFrame(index=index, columns=columns)

        progress = QProgressDialog('Computing results...', None, 0,
                                   len(scen_det_list) + 1, caller)
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)

        for i, scen_det in enumerate(scen_det_list):
            progress.setValue(i)
            # get selected conditions
            scenId = scen_det[0]
            detName = scen_det[1]
            result_super_map_key = scenId + "*" + detName
            scenario = session.query(Scenario).filter_by(id=scenId).first()
            # scen_mats = set(scenMat.material.name for scenMat in scenario.scen_materials)
            scen_mats = scenario.get_material_names_no_shielding()
            scen_bckg_mats = scenario.get_bckg_material_names_no_shielding()
            detector = session.query(Detector).filter_by(name=detName).first()
            res_dir = get_results_dir(sampleRootDir, detector, scenId)
            fc_fileList = [os.path.join(res_dir, f) for f in os.listdir(res_dir) if
                           (f.endswith(".n42") or f.endswith(".res"))]

            pid_total = 0
            tp_perc_total = 0
            fp_total = 0
            fn_total = 0
            CandCtotal = 0
            precision_total = 0
            recall_total = 0
            Fscore_total = 0
            num_files = 0

            result_map = {}
            for file in fc_fileList:
                result_list = []
                num_files = num_files + 1
                results = []
                try:
                    results = readTranslatedResultFile(file)
                except ResultsFileFormatException as ex:
                    print(f"{str(ex)} in file {ntpath.basename(file)}")
                Tp, Fn, Fp = self.getTpFpFn(set(results), scen_mats, scen_bckg_mats)
                result_list.append(str(Tp))
                result_list.append(str(Fn))
                result_list.append(str(Fp))

                pid = 0
                precision = 0
                recall = 0
                Fscore = 0
                CandC = 0

                if Tp == len(scen_mats):
                    pid = 1
                if (Tp + Fn > 0):
                    recall = Tp / (Tp + Fn)
                if (Tp + Fp > 0):
                    precision = Tp / (Tp + Fp)
                if (precision + recall > 0):
                    Fscore = 2 * precision * recall / (precision + recall)
                    if Fscore == 1:
                        CandC = Fscore

                pid_total = pid_total + pid
                tp_perc_total = tp_perc_total + Tp / len(scen_mats)
                fp_total = fp_total + Fp
                fn_total = fn_total + Fn
                CandCtotal = CandC + CandCtotal
                precision_total = precision_total + precision
                result_list.append(str(round(precision, 2)))
                recall_total = recall_total + recall
                result_list.append(str(round(recall, 2)))
                Fscore_total = Fscore_total + Fscore
                result_list.append(str(round(Fscore, 2)))
                result_list.append('; '.join(results))
                result_map[file] = result_list

            self.result_super_map[result_super_map_key] = result_map
            # FIXME: is it possible that num_files becomes zero, thus resulting in an error?
            pid_freq = pid_total / num_files
            (P_CI_p, P_CI_n) = calc_result_uncertainty(pid_freq, num_files)
            tp_freq = tp_perc_total / num_files
            fp_freq = fp_total / num_files
            fn_freq = fn_total / num_files
            CandC_freq = CandCtotal / num_files
            (C_CI_p,C_CI_n) = calc_result_uncertainty(CandC_freq, num_files)
            precision_freq = precision_total / num_files
            recall_freq = recall_total / num_files
            Fscore_freq = Fscore_total / num_files


            mat_dose_dict = {scen_mat.material.name: scen_mat.dose for scen_mat in scenario.scen_materials if
                             scen_mat.fd_mode == 'DOSE'}
            mat_dose_bkg_dict = {scen_mat.material.name: scen_mat.dose for scen_mat in scenario.scen_bckg_materials if
                                 scen_mat.fd_mode == 'DOSE'}
            mat_flux_dict = {scen_mat.material.name: scen_mat.dose for scen_mat in scenario.scen_materials if
                             scen_mat.fd_mode == 'FLUX'}
            mat_flux_bkg_dict = {scen_mat.material.name: scen_mat.dose for scen_mat in scenario.scen_bckg_materials if
                                 scen_mat.fd_mode == 'FLUX'}
            # mat_dose_dict = {scen_mat.material.name: scen_mat.dose for scen_mat in scenario.scen_materials}
            # mat_dose_bkg_dict = {scen_mat.material.name: scen_mat.dose for scen_mat in scenario.scen_bckg_materials}
            self.scenario_stats_df.loc[result_super_map_key] = [detector.name, detector.replay.name,
                                                                  mat_dose_dict, mat_dose_bkg_dict,
                                                                  mat_flux_dict, mat_flux_bkg_dict,
                                                                  [infl.name for infl in scenario.influences],
                                                                  scenario.acq_time,
                                                                  scenario.replication,
                                                                  pid_freq, P_CI_n, P_CI_p,
                                                                  tp_freq, fp_freq, fn_freq,
                                                                  CandC_freq, C_CI_n, C_CI_p,
                                                                  precision_freq, recall_freq, Fscore_freq]


        MatDose_df = self.scenario_stats_df['Mat_Dose'].apply(pd.Series).fillna(0)
        MatDose_df = MatDose_df.add_prefix('Dose_')
        BkgMatDose_df = self.scenario_stats_df['Bkg_Mat_Dose'].apply(pd.Series).fillna(0)
        BkgMatDose_df = BkgMatDose_df.add_prefix('BkgDose_')
        MatFlux_df = self.scenario_stats_df['Mat_Flux'].apply(pd.Series).fillna(0)
        MatFlux_df = MatFlux_df.add_prefix('Flux_')
        BkgMatFlux_df = self.scenario_stats_df['Bkg_Mat_Flux'].apply(pd.Series).fillna(0)
        BkgMatFlux_df = BkgMatFlux_df.add_prefix('BkgFlux_')

        dose_scen_desc = pd.concat([MatDose_df, BkgMatDose_df], axis=1).apply(lambda x: self._create_scenario_desc(x), axis=1)
        flux_scen_desc = pd.concat([MatFlux_df, BkgMatFlux_df], axis=1).apply(lambda x: self._create_scenario_desc(x, italics=True), axis=1)
        self.scenario_stats_df['Scen Desc'] = dose_scen_desc.str.cat(flux_scen_desc, sep=", ")
        self.scenario_stats_df = pd.concat([self.scenario_stats_df[['Det', 'Replay']],
                                            MatDose_df, BkgMatDose_df, MatFlux_df, BkgMatFlux_df,
                                            self.scenario_stats_df.loc[:, 'Infl':]], axis=1)
        # print(self.scenario_stats_df)
        progress.setValue(len(scen_det_list)+1)

    def _create_scenario_desc(self, row, italics=False):
        desc = []
        for k, v in row.items():
            if v > 0:
                k = k.split('_')
                k = "".join(k[1:])
                if italics:
                    desc.append(f'<em>{k}({v:.3g})</em>')
                else:
                    desc.append(f'{k}({v:.3g})')
        return ", ".join(desc)

    @pyqtSlot(str)
    def on_cmbScenarioGroups_currentIndexChanged(self, text):
        self.populateScenarios()

    @pyqtSlot(str)
    def on_txtScenarioSearch_textEdited(self, text):
        self.populateScenarios()

    @pyqtSlot(str)
    def on_txtDetectorSearch_textEdited(self, text):
        self.populateDetectorReplays()

    @pyqtSlot(bool)
    def on_actionHelp_triggered(self, checked):
        """
        Shows help dialog
        """
        if not self.help_dialog:
            self.help_dialog = HelpDialog(self)
        if self.help_dialog.isHidden():
            self.help_dialog.show()
        self.help_dialog.activateWindow()

    @pyqtSlot(bool)
    def on_actionAbout_triggered(self, checked):
        """
        show About Dialog
        """
        AboutRASEDialog(self).exec_()

    @pyqtSlot(bool)
    def on_actionInput_Random_Seed_triggered(self, checked):
        """
        Launches Random Seed Dialog
        """
        dialog = RandomSeedDialog(self)
        dialog.exec_()

    @pyqtSlot(bool)
    def on_actionBase_Spectra_Creation_Tool_triggered(self, checked):
        dialog = CreateBaseSpectraDialog(self)
        dialog.exec_()


class SampleSpectraGeneration(QObject):
    """
    Generates Sample Spectra through its 'work' function
    This class is designed to be moved to a separate thread for background execution
    Signals are emitted for each sample generated and at the end of the process
    Execution can be stopped by setting self.__abort to True
    """
    sig_step = pyqtSignal(int)
    sig_done = pyqtSignal(bool)

    def __init__(self, detector_scenarios, test=False):
        super().__init__()
        self.settings = RaseSettings()
        self.detector_scenarios = detector_scenarios
        self.sampleDir = self.settings.getSampleDirectory()
        self.sampling_algo = self.settings.getSamplingAlgo()
        self.test = test
        self.__abort = False

    @pyqtSlot()
    def work(self):
        count = 0

        session = Session()
        for detName, scenId in self.detector_scenarios:
            detector = session.query(Detector).filter_by(name=detName).first()
            sample_dir = get_sample_dir(self.sampleDir, detector, scenId)
            replay_input_dir = get_replay_input_dir(self.sampleDir, detector, scenId)
            scenario = session.query(Scenario).filter_by(id=scenId).first()

            os.makedirs(sample_dir, exist_ok=True)
            os.makedirs(replay_input_dir, exist_ok=True)

            # generate seed in order to later recreate sampleSpectra
            if (self.settings.getRandomSeed() != self.settings.getRandomSeedDefault()):
                seed = self.settings.getRandomSeed()
            else:
                seed = np.random.randint(0, pow(2, 30))
            sampleSeed = session.query(SampleSpectraSeed).filter_by(scen_id=scenario.id,
                                                                    det_name=detector.name).first() or \
                         SampleSpectraSeed(scen_id=scenario.id, det_name=detector.name)
            sampleSeed.seed = seed
            session.add(sampleSeed)
            session.commit()

            countsDoseAndSensitivity = _getCountsDoseAndSensitivity(scenario, detector)
            secondary_spectrum = (session.query(BackgroundSpectrum).filter_by(detector_name=detector.name)).first()

            n42_template = None
            if detector.replay and detector.replay.n42_template_path:
                n42_template = Template(filename=detector.replay.n42_template_path, input_encoding='utf-8')

            # create 'replication' number of files
            reps = 1 if self.test else scenario.replication
            for filenum in range(reps):
                # This is where the downsampling happens
                sampleCounts = self.sampling_algo(scenario, detector, countsDoseAndSensitivity, seed + filenum)

                # write out to RASE n42 file
                fname = os.path.join(sample_dir,
                                     get_sample_spectra_filename(detector.name, scenario.id, filenum, ".n42"))
                create_n42_file(fname, scenario, detector, sampleCounts, secondary_spectrum)

                # write out to translated file format
                if n42_template:
                    fname = os.path.join(replay_input_dir,
                                         get_sample_spectra_filename(detector.name, scenario.id, filenum,
                                                                     detector.replay.input_filename_suffix))
                    create_n42_file_from_template(n42_template, fname, scenario, detector, sampleCounts,
                                                  secondary_spectrum)

                count += 1
                self.sig_step.emit(count)

                # check if we need to abort the loop; need to process events to receive signals;
                QApplication.processEvents()  # this could cause change to self.__abort

                if self.__abort:
                    # delete current folders since generation was incomplete
                    if os.path.exists(sample_dir):
                        shutil.rmtree(sample_dir)
                    if os.path.exists(replay_input_dir):
                        shutil.rmtree(replay_input_dir)
                    break

        session.close()
        if self.__abort:
            self.sig_done.emit(False)
        else:
            self.sig_done.emit(True)

    def abort(self):
        self.__abort = True


class HtmlDelegate(QStyledItemDelegate):
    '''render html text passed to the table widget item'''

    def paint(self, painter, option, index):
        self.initStyleOption(option, index)

        style = option.widget.style() if option.widget else QApplication.style()

        palette = QApplication.palette()
        color = palette.highlight().color() \
            if option.state & QStyle.State_Selected \
            else palette.base()
        ctx = QAbstractTextDocumentLayout.PaintContext()
        textRect = style.subElementRect(QStyle.SE_ItemViewItemText, option)

        painter.save()
        painter.fillRect(option.rect, color)
        painter.translate(textRect.topLeft())
        painter.setClipRect(textRect.translated(-textRect.topLeft()))

        doc = QTextDocument()
        doc.setHtml(option.text)
        doc.documentLayout().draw(painter, ctx)
        painter.restore()

    def sizeHint(self, option, index):
        fm = option.fontMetrics
        document = QTextDocument()
        document.setDefaultFont(option.font)
        document.setHtml(index.model().data(index))
        return QSize(document.idealWidth() + 20, fm.height())


class AboutRASEDialog(ui_about_dialog.Ui_aboutDialog, QDialog):
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.setupUi(self)
