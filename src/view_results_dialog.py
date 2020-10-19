###############################################################################
# Copyright (c) 2018 Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory
#
# Written by J. Chavez, S. Czyz, G. Kosinovsky, V. Mozin, S. Sangiorgio.
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
This module displays the complete summary of replay results and subsequent analysis
"""

import traceback
import re
import pandas as pd
from PyQt5.QtCore import pyqtSlot, QAbstractTableModel, Qt, QSize
from PyQt5.QtGui import QColor, QAbstractTextDocumentLayout, QTextDocument
from PyQt5.QtWidgets import QDialog, QMessageBox, QHeaderView, QFileDialog, QCheckBox, QVBoxLayout, QDialogButtonBox, \
    QStyledItemDelegate, QApplication, QStyle

from src.plotting import ResultPlottingDialog
from .ui_generated import ui_results_dialog
from src.detailed_results_dialog import DetailedResultsDialog
from src.correspondence_table_dialog import CorrespondenceTableDialog
from src.rase_settings import RaseSettings

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

        cols = ['Det/Replay', 'Scen Desc'] + mat_cols + bkg_cols + ['Infl', 'AcqTime', 'Repl',
                   'PID', 'PID CI', 'TP', 'FP', 'FN', 'C&C', 'C&C CI',
                   'Precision', 'Recall', 'F_Score']


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
            if self._data.columns[index.column()] in ['PID', 'C&C', 'F_Score']:
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
        comboList = ['', 'Det', 'Replay', 'Source Dose', 'Source Flux', 'Background Dose', 'Background Flux', 'Infl',
                     'AcqTime', 'Repl', 'PID', 'TP', 'FP', 'FN', 'C&C', 'Precision', 'Recall', 'F_Score']
        self.cmbXaxis.addItems(comboList)
        self.cmbYaxis.addItems(comboList)
        comboList = ['', 'Det', 'Replay', 'Source Material', 'Background Material', 'Infl', 'AcqTime', 'Repl',
                     'PID', 'TP', 'FP', 'FN', 'C&C', 'Precision', 'Recall', 'F_Score']
        self.cmbZaxis.addItems(comboList)

        self.matNames_dose = ["".join(s.split("_")[1:]) for s in self.parent.scenario_stats_df.columns.to_list()
                         if s.startswith('Dose_')]
        self.matNames_flux = ["".join(s.split("_")[1:]) for s in self.parent.scenario_stats_df.columns.to_list()
                              if s.startswith('Flux_')]
        self.bkgmatNames_dose = ["".join(s.split("_")[1:]) for s in self.parent.scenario_stats_df.columns.to_list()
                            if s.startswith('BkgDose_')]
        self.bkgmatNames_flux = ["".join(s.split("_")[1:]) for s in self.parent.scenario_stats_df.columns.to_list()
                            if s.startswith('BkgFlux_')]

        self.names_dict = {'Source Dose':self.matNames_dose, 'Source Flux': self.matNames_flux,
                           'Background Dose': self.bkgmatNames_dose, 'Background Flux': self.bkgmatNames_flux}
        self.btnViewPlot.setEnabled(False)

        self.btnClose.clicked.connect(self.closeSelected)
        self.buttonExport.clicked.connect(self.handleExport)
        self.buttonCorrTable.clicked.connect(lambda: self.openCorrTable(scenIds, detNames))

        self.results_model = ResultsTableModel(self.parent.scenario_stats_df)
        self.tblResView.setModel(self.results_model)
        self.tblResView.doubleClicked.connect(self.showDetailView)
        self.tblResView.setSortingEnabled(True)
        if self.results_model.scenario_desc_col_index() is not None:
            self.tblResView.setItemDelegateForColumn(self.results_model.scenario_desc_col_index(), HtmlDelegate())
        self.tblResView.resizeColumnsToContents()
        self.tblResView.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)

    def openCorrTable(self, scenIds, detNames):
        """
        Launches Correspondence Table Dialog
        """
        CorrespondenceTableDialog().exec_()
        self.parent.settings.setIsAfterCorrespondenceTableCall(True)
        self.parent.calculateScenarioStats(caller=self, selected_scenarios=scenIds,
                                           selected_detectors=detNames)
        self.results_model.reset_data(self.parent.scenario_stats_df)

    def handleExport(self):
        """
        Exports Results Dataframe to CSV format
        """
        path = QFileDialog.getSaveFileName(self, 'Save File', RaseSettings().getDataDirectory(), 'CSV (*.csv)')
        if path[0]:
            df = self.parent.scenario_stats_df.copy()
            df['Scen Desc'] = df['Scen Desc'].apply(lambda x: re.sub('<[^<]+?>', '', x))
            df.to_csv(path[0])

    def closeSelected(self):
        """
        Closes Dialog
        """
        super().accept()

    def showDetailView(self, index):
        scen_det_key = self.results_model.headerData(index.row(), Qt.Vertical, Qt.UserRole)
        resultMap = self.parent.result_super_map[scen_det_key]
        DetailedResultsDialog(resultMap).exec_()

    @pyqtSlot(str)
    def on_cmbXaxis_currentTextChanged(self, text):
        """
        Listens for X column change
        """
        self.show_material_cmb('X', text)
        self.btnViewPlot_change_status()

    @pyqtSlot(str)
    def on_cmbYaxis_currentTextChanged(self, text):
        """
        Listens for Y column change
        """
        self.show_material_cmb('Y', text)
        self.btnViewPlot_change_status()

    def show_material_cmb(self, axis, text):
        """
        Shows or hides the material combo boxes based on the values of the corresponding axis combo box selected
        :param axis: 'X' or 'Y'
        :param text: text of the axis combo box
        """
        cmbMat = getattr(self, 'cmb' + axis + 'mat')
        txtMat = getattr(self, 'txt' + axis + 'mat')
        txtMat.hide()
        cmbMat.hide()

        if text == 'Influence':
            pass
        elif text in ['Source Dose', 'Source Flux', 'Background Dose', 'Background Flux']:
            cmbMat.clear()
            names = self.names_dict[text]
            cmbMat.addItems([''] + names)
            cmbMat.show()
            txtMat.show()

    def btnViewPlot_change_status(self):
        """
        Enables or disables the ViewPlot button
        """
        if self.cmbXaxis.currentText() and self.cmbYaxis.currentText():
            self.btnViewPlot.setEnabled(True)
        else:
            self.btnViewPlot.setEnabled(False)

    @pyqtSlot(bool)
    def on_btnViewPlot_clicked(self, checked):
        """
        Prepares data for plotting and launches the plotting dialog
        """
        df = self.parent.scenario_stats_df
        titles = []
        ax_vars = []
        x = []
        y = []
        x_err = []
        y_err = []
        repl = []

        for axis in ['X', 'Y']:
            cmbAxis = getattr(self, 'cmb' + axis + 'axis').currentText()
            matName = getattr(self, 'cmb' + axis + 'mat').currentText()

            if cmbAxis in ['Source Dose']:
                title = 'Dose' + f" {matName}"
                ax_var = 'Dose' + f"_{matName}"
            elif cmbAxis in ['Source Flux']:
                title = 'Flux' + f" {matName}"
                ax_var = 'Flux' + f"_{matName}"
            elif cmbAxis in ['Background Dose']:
                title = 'BkgDose' + f" {matName}"
                ax_var = 'BkgDose' + f"_{matName}"
            elif cmbAxis in ['Background Flux']:
                title = 'BkgFlux' + f" {matName}"
                ax_var = 'BkgFlux' + f"_{matName}"
            else:
                title = cmbAxis
                ax_var = cmbAxis

            ax_vars.append(ax_var)
            titles.append(title)

        if len(titles) >= 2:
            for i, ax_title in enumerate(titles):
                if ax_title.startswith('Dose') or ax_title.startswith('BkgDose'):
                    titles[i] = ax_title + (' (\u00B5Sv/h)')
                elif ax_title.startswith('Flux') or ax_title.startswith('BkgFlux'):
                    titles[i] = ax_title + (' (\u03B3/(cm\u00B2s))')

        try:
            cat = self.cmbZaxis.currentText()
            categories = []
            if cat:
                if self.cmbZaxis.currentText() == 'Source Material':
                    categories = [s for s in df.columns.to_list() if s.startswith('Dose_') or s.startswith('Flux_')]
                elif self.cmbZaxis.currentText() == 'Background Material':
                    categories = [s for s in df.columns.to_list() if
                                  s.startswith('BkgDose_') or s.startswith('BkgFlux_')]
                else:
                    categories = pd.unique(df[cat].values).tolist()

            for v in ['PID','C&C']:
                df[f'{v}_H_err'] = (df[v] - df[f'{v}_H']).abs()
                df[f'{v}_L_err'] = (df[v] - df[f'{v}_L']).abs()

            if not cat:
                x.append(df[ax_vars[0]].to_list())
                if ax_vars[0] in ['PID', 'C&C']:
                    x_err.append([(l, h) for (l, h) in zip(df[f'{ax_vars[0]}_L_err'], df[f'{ax_vars[0]}_H_err'])])
                if ax_vars[1]:
                    y.append(self.parent.scenario_stats_df[ax_vars[1]].to_list())
                    if ax_vars[1] in ['PID', 'C&C']:
                        y_err.append([(l, h) for (l, h) in zip(df[f'{ax_vars[1]}_L_err'], df[f'{ax_vars[1]}_H_err'])])
                    repl.append(df['Repl'].tolist())
            else:
                for cat_label in categories:
                    if isinstance(cat_label, str) and \
                            (cat_label.startswith('Dose') or cat_label.startswith('Flux') or
                             cat_label.startswith('BkgDose') or cat_label.startswith('BkgFlux')):
                        df = self.parent.scenario_stats_df.loc[self.parent.scenario_stats_df[cat_label] != 0]
                        x.append(df[cat_label].to_list())
                    else:
                        df = self.parent.scenario_stats_df.loc[self.parent.scenario_stats_df[cat] == cat_label]
                        x.append(df[ax_vars[0]].to_list())
                        repl.append(df['Repl'].tolist())
                        if ax_vars[0] in ['PID', 'C&C']:
                            x_err.append([(l, h) for (l, h) in zip(df[f'{ax_vars[0]}_L_err'], df[f'{ax_vars[0]}_H_err'])])
                    if ax_vars[1]:
                        y.append(df[ax_vars[1]].to_list())
                        if ax_vars[1] in ['PID', 'C&C']:
                            y_err.append([(l, h) for (l, h) in zip(df[f'{ax_vars[1]}_L_err'], df[f'{ax_vars[1]}_H_err'])])
        except Exception as e:
            # TODO: log the error instead of printing
            print(traceback.format_exc())
            QMessageBox.information(self, "Info", "Sorry, the requested plot cannot be generated.")
            return

        dialog = ResultPlottingDialog(self, x, y, titles, categories, repl, x_err, y_err)
        dialog.exec_()

    @pyqtSlot(bool)
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
                     'Infl', 'AcqTime', 'Repl', 'PID', 'PID CI', 'TP', 'FP', 'FN', 'C&C', 'C&C CI',
                     'Precision', 'Recall', 'F_Score']
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
            if cb.text() == 'Scen Desc':
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

    @pyqtSlot()
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
