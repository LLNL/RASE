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
This module displays the complete summary of replay results and subsequent analysis
"""
import logging
import traceback
import re

import numpy as np
import pandas as pd
from collections import Counter

from matplotlib.backends.backend_qt import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.figure import Figure
import seaborn as sns

from PySide6.QtCore import Slot, QAbstractTableModel, Qt, QSize, QPoint
from PySide6.QtGui import QColor, QAbstractTextDocumentLayout, QTextDocument, QKeySequence, QAction, QDoubleValidator, \
    QValidator
from PySide6.QtWidgets import QDialog, QMessageBox, QHeaderView, QFileDialog, QCheckBox, QVBoxLayout, QDialogButtonBox, \
    QStyledItemDelegate, QApplication, QStyle, QMenu, QTableWidget, QTableWidgetItem, QWidget

from src.plotting import ResultPlottingDialog, Result3DPlottingDialog
from src.table_def import Scenario, Detector, Session
from .qt_utils import DoubleValidator
from .ui_generated import ui_results_dialog
from src.detailed_results_dialog import DetailedResultsDialog
from src.correspondence_table_dialog import CorrespondenceTableDialog
from src.manage_weights_dialog import ManageWeightsDialog
from src.rase_settings import RaseSettings
from src.help_dialog import HelpDialog

NUM_COL = 16
INST_REPL, SCEN_ID, SCEN_DESC, ACQ_TIME, REPL, INFL, PD, PD_CI, TP, FP, FN, CANDC, CANDC_CI, PRECISION, RECALL, \
FSCORE  = range(NUM_COL)

# color scale from https://colorbrewer2.org/#type=diverging&scheme=RdYlGn&n=11
STOPLIGHT_COLORS = ['#a50026','#d73027','#f46d43','#fdae61','#fee08b','#ffffbf','#d9ef8b','#a6d96a','#66bd63','#1a9850','#006837']


class ResultsTableModel(QAbstractTableModel):
    """Table Model for the Identification Results

    The underline data is the pandas dataframe produced in rase.py.
    The input dataframe is copied as some of the formatting applied does not need to propagate to the original

    :param data: the new input pandas dataframe from the identification results analysis
    """
    def __init__(self, data):
        super(ResultsTableModel, self).__init__()
        self._data = data.copy()
        self.col_settings = RaseSettings().getResultsTableSettings()
        self._reformat_data()

    def _reformat_data(self):
        """
        Reformat underlying data for prettier display and downselect only the columns requested by the user
        """
        self._data['Det/Replay'] = self._data['Det'] + '/' + self._data['Replay']
        self._data['PID CI'] = [str(round(abs(l), 2)) + ' - ' + str(round(h, 2)) for h, l in zip(self._data['PID_H'], self._data['PID_L'])]
        self._data['C&C CI'] = [str(round(abs(l), 2)) + ' - ' + str(round(h, 2)) for h, l in zip(self._data['C&C_H'], self._data['C&C_L'])]
        # self._data.drop(columns=['Det', 'Replay', 'PID_L', 'PID_H', 'C&C_L', 'C&C_H'], inplace=True)
        mat_cols = [s for s in self._data.columns.to_list() if (s.startswith('Dose_') or s.startswith('Flux_'))]
        bkg_cols = [s for s in self._data.columns.to_list() if (s.startswith('BkgDose_') or s.startswith('BkgFlux_'))]

        cols = ['Det/Replay', 'Scen Desc'] + mat_cols + bkg_cols + ['Infl', 'AcqTime', 'Repl', 'Comment',
                   'PID', 'PID CI', 'C&C', 'C&C CI', 'TP', 'FP', 'FN', 'Precision', 'Recall', 'F_Score',
                                                     'wTP', 'wFP', 'wFN', 'wPrecision', 'wRecall', 'wF_Score']


        if self.col_settings:
            cols = [c for c in cols if (c.startswith('Dose') or c.startswith('BkgDose')
                                        or c.startswith('Flux') or c.startswith('BkgFlux')) or c in self.col_settings]
            if 'Dose' not in self.col_settings:
                cols = [c for c in cols if not c.startswith('Dose')]
            if 'Background Dose' not in self.col_settings:
                cols = [c for c in cols if not c.startswith('BkgDose')]
            if 'Flux' not in self.col_settings:
                cols = [c for c in cols if not c.startswith('Flux')]
            if 'Background Flux' not in self.col_settings:
                cols = [c for c in cols if not c.startswith('BkgFlux')]
        self._data = self._data[cols]
        # self._data = self._data.rename(columns={'PID':'Prob. ID'})

    def reset_data(self, data):
        """
        Reset and reformat the data.
        Should be called always after the data have been recomputed or columns selection changed
        :param data: the new input pandas dataframe from the identification results analysis
        """
        self.layoutAboutToBeChanged.emit()
        self._data = data.copy()
        self.col_settings = RaseSettings().getResultsTableSettings()
        self._reformat_data()
        self.layoutChanged.emit()

    def data(self, index, role):
        if role == Qt.DisplayRole:
            value = self._data.iloc[index.row(), index.column()]
            if isinstance(value, float):
                return f'{value:.3g}'
            else:
                return str(value)

        if role == Qt.DecorationRole:
            # stopchart blocks
            if self._data.columns[index.column()] in ['PID', 'C&C', 'F_Score', 'wF_Score']:
                value = self._data.iloc[index.row(), index.column()]
                if value < 0: value = 0
                if value > 1: value = 1
                value = int(value * (len(STOPLIGHT_COLORS) -1))
                return QColor(STOPLIGHT_COLORS[value])

        if role == Qt.TextAlignmentRole:
            return Qt.AlignCenter

    def rowCount(self, index):
        return self._data.shape[0]

    def columnCount(self, index):
        return self._data.shape[1]

    def headerData(self, section, orientation, role):
        # section is the index of the column/row.
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                h = str(self._data.columns[section]).split('_')
                if h[0] == "Dose" or h[0] == "BkgDose" or h[0] == "Flux" or h[0] == "BkgFlux":
                    desc = "".join(h[1:]).split('-')
                    return f'{h[0]}\n{desc[0]}\n{"".join(desc[1:])}'
                else:
                    return str(self._data.columns[section])

            if orientation == Qt.Vertical:
                return str(self._data.index[section].split("*")[0])

        if role == Qt.UserRole:
            if orientation == Qt.Vertical:
                return str(self._data.index[section])

    def sort(self, column: int, order: Qt.SortOrder = ...) -> None:
        self.layoutAboutToBeChanged.emit()
        if len(self._data.columns):
            self._data.sort_values(by=[self._data.columns[column]],
                                   ascending=not order, inplace=True)
        self.layoutChanged.emit()

    def scenario_desc_col_index(self):
        if 'Scen Desc' in self._data.columns:
            return self._data.columns.values.tolist().index('Scen Desc')
        return None


class ViewResultsDialog(ui_results_dialog.Ui_dlgResults, QDialog):
    """Dialog to display identification results and select variables for plotting

    :param parent: the parent dialog
    """
    def __init__(self, parent, scenIds, detNames):

        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.parent = parent
        self.help_dialog = None
        comboList = ['', 'Det', 'Replay', 'Source Dose', 'Source Flux',
                     'Distance (given dose)', 'Distance (given flux)',
                     'Background Dose', 'Background Flux', 'Infl',
                     'AcqTime', 'Repl', 'PID', 'C&C', 'TP', 'FP', 'FN', 'Precision', 'Recall', 'F_Score', 'wTP', 'wFP',
                     'wFN', 'wPrecision', 'wRecall', 'wF_Score']
        self.cmbXaxis.addItems(comboList)
        self.cmbYaxis.addItems(comboList)
        comboList = ['', 'PID', 'C&C', 'TP', 'FP', 'FN', 'Precision', 'Recall', 'F_Score', 'wTP', 'wFP', 'wFN',
                     'wPrecision', 'wRecall', 'wF_Score']
        self.cmbZaxis.addItems(comboList)
        comboList = ['', 'Det', 'Replay', 'Source Material', 'Background Material', 'Infl', 'AcqTime', 'Repl',
                     'PID', 'C&C', 'TP', 'FP', 'FN', 'Precision', 'Recall', 'F_Score', 'wTP', 'wFP', 'wFN',
                     'wPrecision', 'wRecall', 'wF_Score']
        self.cmbGroupBy.addItems(comboList)
        self.cmbGroupBy.setEnabled(False)

        for wdgt in [getattr(self, f'txtRef{l}{a}') for a in ['X', 'Y'] for l in ['Dose', 'Distance']]:
            wdgt.setValidator(DoubleValidator(wdgt))
            wdgt.textChanged.connect(self.set_view_plot_btn_status)
            wdgt.validator().setBottom(1.e-6)
            wdgt.validator().validationChanged.connect(self.handle_validation_change)

        self.matNames_dose = ["".join(s.split("_")[1:]) for s in self.parent.scenario_stats_df.columns.to_list()
                         if s.startswith('Dose_')]
        self.matNames_flux = ["".join(s.split("_")[1:]) for s in self.parent.scenario_stats_df.columns.to_list()
                              if s.startswith('Flux_')]
        self.bkgmatNames_dose = ["".join(s.split("_")[1:]) for s in self.parent.scenario_stats_df.columns.to_list()
                            if s.startswith('BkgDose_')]
        self.bkgmatNames_flux = ["".join(s.split("_")[1:]) for s in self.parent.scenario_stats_df.columns.to_list()
                            if s.startswith('BkgFlux_')]

        self.names_dict = {'Source Dose': self.matNames_dose, 'Source Flux': self.matNames_flux,
                           'Distance (given dose)': self.matNames_dose, 'Distance (given flux)': self.matNames_flux,
                           'Background Dose': self.bkgmatNames_dose, 'Background Flux': self.bkgmatNames_flux}
        self.btnViewPlot.setEnabled(False)
        self.btnFreqAnalysis.setEnabled(False)

        self.btnInfoDistanceX.clicked.connect(self.open_help)
        self.btnInfoDistanceY.clicked.connect(self.open_help)

        self.btnClose.clicked.connect(self.closeSelected)
        self.buttonExport.clicked.connect(self.handleExport)
        self.buttonCorrTable.clicked.connect(lambda: self.openCorrTable(scenIds, detNames))
        self.buttonManageWeights.clicked.connect(lambda: self.openWeightsTable(scenIds, detNames))
        self.btnFreqAnalysis.clicked.connect(self.show_freq_results)

        self.results_model = ResultsTableModel(self.parent.scenario_stats_df)
        self.tblResView.setModel(self.results_model)
        self.tblResView.doubleClicked.connect(self.showDetailView)
        self.tblResView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tblResView.setSortingEnabled(True)
        if self.results_model.scenario_desc_col_index() is not None:
            self.tblResView.setItemDelegateForColumn(self.results_model.scenario_desc_col_index(), HtmlDelegate())
        self.tblResView.resizeColumnsToContents()
        self.tblResView.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tblResViewSelect = self.tblResView.selectionModel()
        self.tblResViewSelect.selectionChanged.connect(self.btnFreqAnalysis_change_status)

    @Slot(QValidator.State)
    def handle_validation_change(self, state):
        if state == QValidator.Invalid:
            color = 'red'
        elif state == QValidator.Intermediate:
            color = 'gold'
        elif state == QValidator.Acceptable:
            color = 'green'
        sender = self.sender().parent()
        sender.setStyleSheet(f'border: 2px solid {color}')
        # QtCore.QTimer.singleShot(1000, lambda: sender.setStyleSheet(''))

    def openCorrTable(self, scenIds, detNames):
        """
        Launches Correspondence Table Dialog
        """
        CorrespondenceTableDialog().exec_()
        self.parent.settings.setIsAfterCorrespondenceTableCall(True)
        self.parent.calculateScenarioStats(caller=self, selected_scenarios=scenIds,
                                           selected_detectors=detNames)
        self.results_model.reset_data(self.parent.scenario_stats_df)

    def openWeightsTable(self, scenIds, detNames):
        """
        Launches Correspondence Table Dialog
        """
        ManageWeightsDialog().exec_()
        self.parent.calculateScenarioStats(caller=self, selected_scenarios=scenIds,
                                           selected_detectors=detNames)
        self.results_model.reset_data(self.parent.scenario_stats_df)

    def handleExport(self):
        """
        Exports Results Dataframe to CSV format. Includes ID Frequencies
        """
        path = QFileDialog.getSaveFileName(self, 'Save File', RaseSettings().getDataDirectory(), 'CSV (*.csv)')
        if path[0]:
            df = self.parent.scenario_stats_df.copy()
            df['Scen Desc'] = df['Scen Desc'].apply(lambda x: re.sub('<[^<]+?>', '', x))
            df['ID Frequencies'] = [self.compute_freq_results([scen_det_key,]) for scen_det_key in df.index]
            df.to_csv(path[0])

    def closeSelected(self):
        """
        Closes Dialog
        """
        super().accept()

    def showDetailView(self, index):
        scen_det_key = self.results_model.headerData(index.row(), Qt.Vertical, Qt.UserRole)
        resultMap = self.parent.result_super_map[scen_det_key]
        scen_id = scen_det_key.split('*')[0]
        det_name = "".join(scen_det_key.split('*')[1:])
        scenario = Session().query(Scenario).filter_by(id=scen_id).first()
        detector = Session().query(Detector).filter_by(name=det_name).first()
        DetailedResultsDialog(resultMap, scenario, detector).exec_()

    @Slot(QPoint)
    def on_tblResView_customContextMenuRequested(self, point):
        """
        Handles right click selections on the results table
        """
        index = self.tblResView.indexAt(point)
        # show the context menu only if on an a valid part of the table
        if index:
            detail_view_action = QAction('Show Detailed Results Table', self)
            show_freq_action = QAction(f'Show Identification Results Frequency of Selected Row'
                                       f'{"s"  if len(self.tblResViewSelect.selectedRows()) > 1 else ""}', self)
            menu = QMenu(self.tblResView)
            menu.addAction(detail_view_action)
            menu.addAction(show_freq_action)
            action = menu.exec_(self.tblResView.mapToGlobal(point))
            if action == show_freq_action:
                self.show_freq_results()
            elif action == detail_view_action:
                self.showDetailView(index)

    def compute_freq_results(self, scen_det_keys: list):
        """
        Compute sorted frequency of all identification result strings for the given list of `scenario*detector` keys
        """
        freq_result_dict = {}
        if scen_det_keys:
            result_strings = []
            num_entries = 0
            for scen_det_key in scen_det_keys:
                if scen_det_key in self.parent.result_super_map:
                    result_map = self.parent.result_super_map[scen_det_key]
                    key_result_strings = [(x.strip() if x else "No ID") for res in result_map.values()
                                          for x in res[-1].split(';')]
                    result_strings += key_result_strings
                    num_entries += len(result_map)
            if num_entries:
                result_string_counter = Counter(result_strings)
                freq_result_dict = {k: f'{v / num_entries:.4g}' for k, v in sorted(result_string_counter.items(),
                                                                                   key=lambda item: item[1], reverse=True)}
        return freq_result_dict

    def show_freq_results(self):
        """
        Shows the frequency of all identification result strings for the selected rows in the results table
        """
        if self.tblResViewSelect.hasSelection():
            scen_det_keys = [self.results_model.headerData(i.row(), Qt.Vertical, Qt.UserRole) for i in self.tblResViewSelect.selectedRows()]
            freq_result_dict = self.compute_freq_results(scen_det_keys)
            freq_result_table = FrequencyTableDialog(self, freq_result_dict)
            freq_result_table.exec_()

    def btnFreqAnalysis_change_status(self):
        """
        Enables or disables the Frequency Analysis button
        """
        if self.tblResViewSelect.hasSelection():
            self.btnFreqAnalysis.setEnabled(True)
        else:
            self.btnFreqAnalysis.setEnabled(False)


    @Slot(str)
    def on_cmbXaxis_currentTextChanged(self, text):
        """
        Listens for X column change
        """
        self.show_material_cmb('X', text)
        for cmb in [self.cmbYaxis, self.cmbGroupBy]:
            cmb.setEnabled(True if text else False)
            if not text:
                cmb.setCurrentIndex(0)
        self.set_view_plot_btn_status()

    @Slot(str)
    def on_cmbYaxis_currentTextChanged(self, text):
        """
        Listens for Y column change
        """
        self.show_material_cmb('Y', text)
        self.cmbZaxis.setEnabled(True if text else False)
        if not text: self.cmbZaxis.setCurrentIndex(0)
        self.cmbGroupBy.setEnabled(True)
        self.set_view_plot_btn_status()

    @Slot(str)
    def on_cmbZaxis_currentTextChanged(self, text):
        """
        Listens for Z column change
        """
        if text:
            self.cmbGroupBy.setCurrentIndex(0)
        self.cmbGroupBy.setEnabled(False if text else True)

    def show_material_cmb(self, axis, text):
        """
        Shows or hides the material combo boxes based on the values of the corresponding axis combo box selected
        :param axis: 'X' or 'Y'
        :param text: text of the axis combo box
        """
        cmbMat = getattr(self, 'cmb' + axis + 'mat')
        txtMat = getattr(self, 'txt' + axis + 'mat')
        distanceWdg = getattr(self, 'distanceRef' + axis + 'Widget')
        txtMat.hide()
        cmbMat.hide()
        distanceWdg.hide()

        if text == 'Influence':
            pass
        elif text in ['Source Dose', 'Source Flux', 'Distance (given dose)', 'Distance (given flux)',
                      'Background Dose', 'Background Flux']:
            cmbMat.clear()
            names = self.names_dict[text]
            cmbMat.addItems(names)
            cmbMat.show()
            txtMat.show()
            if text in ['Distance (given dose)', 'Distance (given flux)']:
                getattr(self, f'labelDose{axis}').setText(f"with {'dose' if 'dose' in text else 'flux'} of")
                getattr(self, f'labelDoseUnit{axis}').setText('\u00B5Sv/h at' if 'dose' in text else '\u03B3/(cm\u00B2s) at')
                distanceWdg.show()

    @Slot(str)
    def set_view_plot_btn_status(self, t=''):
        status = True
        text_x = self.cmbXaxis.currentText()
        if not text_x or (text_x.startswith('Distance (given')
                          and not (self.txtRefDoseX.hasAcceptableInput() and self.txtRefDistanceX.hasAcceptableInput())):
            status = False
        text_y = self.cmbYaxis.currentText()
        if text_y.startswith('Distance (given') \
                and not (self.txtRefDoseY.hasAcceptableInput() and self.txtRefDistanceY.hasAcceptableInput()):
            status = False
        self.btnViewPlot.setEnabled(status)

    @Slot(bool)
    def on_btnViewPlot_clicked(self, checked):
        """
        Prepares data for plotting and launches the plotting dialog
        """
        df = self.parent.scenario_stats_df.copy()
        unappended_titles = []
        titles = []
        ax_vars = []
        x = []
        y = []
        x_err = []
        y_err = []
        repl = []

        for axis in ['X', 'Y', 'Z']:
            cmbAxis = getattr(self, 'cmb' + axis + 'axis').currentText()
            matName = getattr(self, 'cmb' + axis + 'mat').currentText() if axis in ['X', 'Y'] else ''

            if cmbAxis in ['Source Dose']:
                title = 'Dose' + f" {matName}"
                unappended_title = 'Dose_' + f"{matName}"
                ax_var = 'Dose' + f"_{matName}"
            elif cmbAxis in ['Source Flux']:
                title = 'Flux' + f" {matName}"
                unappended_title = 'Flux_' + f"{matName}"
                ax_var = 'Flux' + f"_{matName}"
            elif cmbAxis in ['Background Dose']:
                title = 'BkgDose' + f" {matName}"
                unappended_title = 'BkgDose_' + f"{matName}"
                ax_var = 'BkgDose' + f"_{matName}"
            elif cmbAxis in ['Background Flux']:
                title = 'BkgFlux' + f" {matName}"
                unappended_title = 'BkgFlux_' + f"{matName}"
                ax_var = 'BkgFlux' + f"_{matName}"
            elif cmbAxis in ['Distance (given dose)', 'Distance (given flux)']:
                title = f'Distance from {matName} source [cm]'
                unappended_title = f"Dose_{matName}" if 'dose' in cmbAxis else f'Flux_{matName}'
                ax_var = f'Distance_{matName}_Dose' if 'dose' in cmbAxis else f'Distance_{matName}_Flux'
                txtRefDistance = getattr(self, 'txtRefDistance' + axis)
                txtRefDose = getattr(self, 'txtRefDose' + axis)
                ref_distance = float(txtRefDistance.text())
                ref_dose = float(txtRefDose.text())
                df[ax_var] = ref_distance * np.sqrt(ref_dose / df[unappended_title])  # simple 1/r^2
            else:
                title = cmbAxis
                unappended_title = cmbAxis
                ax_var = cmbAxis

            unappended_titles.append(unappended_title)
            titles.append(title)
            ax_vars.append(ax_var)

        if len(titles) >= 3:
            for i, ax_title in enumerate(titles):
                if ax_title.startswith('Dose') or ax_title.startswith('BkgDose'):
                    titles[i] = ax_title + (' (\u00B5Sv/h)')
                elif ax_title.startswith('Flux') or ax_title.startswith('BkgFlux'):
                    titles[i] = ax_title + (' (\u03B3/(cm\u00B2s))')

        try:
            if self.cmbZaxis.currentText():     # 3D plotting case
                if self.cb_removezero.isChecked():
                    df_3dplot = df.loc[~((df[unappended_titles[0]] == 0) |
                                         (df[unappended_titles[1]] == 0))].pivot(values=unappended_titles[2],
                                                                                index=unappended_titles[0],
                                                                                columns=unappended_titles[1])
                else:
                    df_3dplot = df.pivot(values=unappended_titles[2],
                                        index=unappended_titles[0],
                                        columns=unappended_titles[1])

                dialog = Result3DPlottingDialog(self, df_3dplot, titles)
                dialog.exec_()
            else:   # 1D and 2D plotting
                cat = self.cmbGroupBy.currentText()
                if cat:
                    if self.cmbGroupBy.currentText() == 'Source Material':
                        if ax_vars[0].startswith('Distance_'):
                            categories = [s for s in df.columns.to_list() if s.startswith('Distance_')]
                        else:
                            categories = [s for s in df.columns.to_list() if s.startswith('Dose_') or s.startswith('Flux_')]
                    elif self.cmbGroupBy.currentText() == 'Background Material':
                        categories = [s for s in df.columns.to_list() if
                                      s.startswith('BkgDose_') or s.startswith('BkgFlux_')]
                    else:
                        categories = pd.unique(df[cat].values).tolist()
                else:
                    categories = [ax_vars[0]]

                for v in ['PID','C&C']:
                    df[f'{v}_H_err'] = (df[v] - df[f'{v}_H']).abs()
                    df[f'{v}_L_err'] = (df[v] - df[f'{v}_L']).abs()

                for cat_label in categories:
                    if isinstance(cat_label, str) and (cat_label.startswith('Dose') or cat_label.startswith('BkgDose') or
                                                       cat_label.startswith('Flux') or cat_label.startswith('BkgFlux')
                                                       or cat_label.startswith('Distance')):
                        if cat_label.startswith('Distance'):
                            df_tmp = df.loc[df[cat_label] != float('inf')]
                        else:
                            df_tmp = df.loc[df[cat_label] != 0]
                        x.append(df_tmp[cat_label].to_list())
                    else:
                        df_tmp = df.loc[df[cat] == cat_label] if cat else df
                        x.append(df_tmp[ax_vars[0]].to_list())
                        if ax_vars[0] in ['PID', 'C&C']:
                            x_err.append([(l, h) for (l, h) in zip(df_tmp[f'{ax_vars[0]}_L_err'],
                                                                   df_tmp[f'{ax_vars[0]}_H_err'])])
                    repl.append(df_tmp['Repl'].tolist())
                    if ax_vars[1]:
                        y.append(df_tmp[ax_vars[1]].to_list())
                        if ax_vars[1] in ['PID', 'C&C']:
                            y_err.append([(l, h) for (l, h) in zip(df_tmp[f'{ax_vars[1]}_L_err'],
                                                                   df_tmp[f'{ax_vars[1]}_H_err'])])

                dialog = ResultPlottingDialog(self, x, y, titles, categories, repl, x_err, y_err)
                dialog.exec_()

        except Exception as e:
            traceback.print_exc()
            logging.exception("Handled Exception", exc_info=True)
            QMessageBox.information(self, "Info", "Sorry, the requested plot cannot be generated because:\n" + str(e))
            return

    def open_help(self):
        if not self.help_dialog:
            self.help_dialog = HelpDialog(page='Use_distance.html')
        if self.help_dialog.isHidden():
            self.help_dialog.load_page(page='Use_distance.html')
            self.help_dialog.show()
        self.help_dialog.activateWindow()

    @Slot(bool)
    def on_btnSettings_clicked(self, checked):
        """
        Launches the results table settings dialog
        """
        idx = self.results_model.scenario_desc_col_index()
        dialog = ResultsTableSettings(self)
        dialog.exec_()
        self.results_model.reset_data(self.parent.scenario_stats_df)
        if idx is not None:
            self.tblResView.setItemDelegateForColumn(idx, QStyledItemDelegate())
        if self.results_model.scenario_desc_col_index() is not None:
            self.tblResView.setItemDelegateForColumn(self.results_model.scenario_desc_col_index(), HtmlDelegate())
        self.tblResView.resizeColumnsToContents()
        self.tblResView.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)


class ResultsTableSettings(QDialog):
    """Simple Dialog to allow the user to select which column to display in the results table

    The settings are stored persistently in the RaseSettings class

    :param parent: the parent dialog
    """
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        cols_list = ['Det/Replay', 'Scen Desc', 'Dose', 'Flux', 'Background Dose', 'Background Flux',
                     'Infl', 'AcqTime', 'Repl', 'Comment', 'PID', 'PID CI', 'C&C', 'C&C CI', 'TP', 'FP', 'FN',
                     'Precision', 'Recall', 'F_Score', 'wTP', 'wFP', 'wFN', 'wPrecision', 'wRecall', 'wF_Score']
        # QT treats the ampersand symbol as a special character, so it needs special treatment
        self.cb_list = [QCheckBox(v.replace('&', '&&')) for v in cols_list]
        layout = QVBoxLayout()
        for cb in self.cb_list:
            # if not (cb.text() == self.not_fd_mode):
            layout.addWidget(cb)
        self.buttonBox = QDialogButtonBox(self)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)
        if RaseSettings().getResultsTableSettings():
            self.set_current_settings()
        else:
            self.set_default()

    def set_default(self):
        """
        Sets default selection
        """
        for cb in self.cb_list:
            if cb.text() == 'Scen Desc' or cb.text() == 'Comment':
                cb.setChecked(False)
            else:
                cb.setChecked(True)

    def set_current_settings(self):
        """
        Loads and apply the stored settings
        """
        for cb in self.cb_list:
            if cb.text().replace('&&', '&') in RaseSettings().getResultsTableSettings():
                cb.setChecked(True)
            else:
                cb.setChecked(False)

    @Slot()
    def accept(self):
        """
        Stores the selected values in the RaseSettings class
        """
        selected = [cb.text().replace('&&', '&') for cb in self.cb_list if cb.isChecked()]
        RaseSettings().setResultsTableSettings(selected)
        return QDialog.accept(self)


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
        document.setHtml(index.model().data(index, Qt.DisplayRole))
        return QSize(document.idealWidth() + 20, fm.height())


class FrequencyTableDialog(QDialog):
    """Display a table of data from an input dictionary

    :param data: the input dictionary data
    :param parent: the parent dialog
    """
    def __init__(self, parent, data):
        QDialog.__init__(self, parent)
        self.setWindowTitle("Results Frequency Analysis")

        self.data = data
        self.tableWidget = QTableWidget()
        self.tableWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tableWidget.customContextMenuRequested.connect(self.show_context_menu)
        self.setData()

        self.buttonBox = QDialogButtonBox(self)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Ok)
        self.buttonBox.accepted.connect(self.accept)

        self.widget = QWidget(self)
        self.widget.setMinimumSize(QSize(300, 300))
        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.widget)
        self.ax = self.fig.add_subplot(111)
        self.navi_toolbar = NavigationToolbar(self.canvas, self.widget)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.tableWidget)
        self.layout.addWidget(self.canvas)
        self.layout.addWidget(self.navi_toolbar)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

        self.draw()

    def setData(self):
        self.tableWidget.setRowCount(len(self.data.keys()))
        self.tableWidget.setColumnCount(2)
        for n, k in enumerate(self.data.keys()):
            for col, value in enumerate([k, str(self.data[k])]):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignCenter)
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                self.tableWidget.setItem(n, col, item)
        self.tableWidget.setHorizontalHeaderLabels(['Material', 'Frequency'])

    def draw(self):
        """
        Draws the bar plot with the frequency results
        """
        self.ax.clear()
        values = [float(v)*100 for v in self.data.values()]
        sns.barplot(x=values, y=list(self.data.keys()), ax=self.ax)
        self.ax.set_xlabel('Frequency [%]')
        self.ax.set_ylabel('ID Result Label')
        self.canvas.draw()

    def get_selected_cells_as_text(self):
        """
        Returns the selected cells of the table as plain text
        """
        selected_rows = self.tableWidget.selectedIndexes()
        text = ""
        # show the context menu only if on an a valid part of the table
        if selected_rows:
            cols = set(index.column() for index in self.tableWidget.selectedIndexes())
            for row in set(index.row() for index in self.tableWidget.selectedIndexes()):
                text += "\t".join([self.tableWidget.item(row, col).text() for col in cols])
                text += '\n'
        return text

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Copy or e.key == QKeySequence(QKeySequence.Copy) or e.key() == 67:
            QApplication.clipboard().setText(self.get_selected_cells_as_text())

    @Slot(QPoint)
    def show_context_menu(self, point):
        """
        Handles "Copy" right click selections on the table
        """
        copy_action = QAction('Copy', self)
        menu = QMenu(self.tableWidget)
        menu.addAction(copy_action)
        action = menu.exec_(self.tableWidget.mapToGlobal(point))
        if action == copy_action:
            QApplication.clipboard().setText(self.get_selected_cells_as_text())
