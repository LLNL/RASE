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
This module provides plotting support for RASE analysis
"""
import glob
import json
import os
import numpy as np
import matplotlib
from sqlalchemy.orm import Session
from uncertainties import ufloat, UFloat

matplotlib.use("QtAgg")
from matplotlib.backends.backend_qt import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.figure import Figure
from matplotlib import rcParams
import matplotlib.patheffects as peff
rcParams.update({'figure.autolayout': True})

import seaborn as sns
sns.set(font_scale=1.5)
sns.set_style("whitegrid")

from PySide6.QtCore import Slot, Qt, QUrl
from PySide6.QtWidgets import QDialog, QVBoxLayout, QMessageBox, QGridLayout, QLabel, QDialogButtonBox, QLineEdit, \
    QCheckBox, QWidget, QComboBox
from PySide6.QtGui import QStandardItemModel, QStandardItem, QValidator
from PySide6.QtWebEngineWidgets import QWebEngineView

from .ui_generated import ui_view_spectra_dialog, ui_results_plotting_dialog, ui_results_plotting_dialog_3d, \
    ui_fit_params_settings_dialog
from src.rase_functions import calc_result_uncertainty, get_sample_dir, readSpectrumFile
import src.s_curve_functions as sCurve
from src.utils import get_bundle_dir, natural_keys
from src.base_spectra_dialog import SharedObject, ReadFileObject
from src.rase_settings import RaseSettings
from src.qt_utils import DoubleValidatorInfinity, DoubleValidator


class BaseSpectraViewerDialog(ui_view_spectra_dialog.Ui_Dialog, QDialog):
    def __init__(self, parent, base_spectra, detector, selected):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.baseSpectra = base_spectra
        self.detector = detector
        self.selected = selected
        self.session = Session()
        self.json_file = os.path.join(get_bundle_dir(), "d3_resources", "spectrum.json")
        self.index = 0

        self.browser = WebSpectraView(self)

        for i, baseSpectrum in enumerate(self.baseSpectra):
            if baseSpectrum.material.name == self.selected:
                self.index = i
                self.plot_spectrum()

        self.plot_layout = QVBoxLayout(self.widget)
        self.plot_layout.addWidget(self.browser)
        self.widget.setFocus()

    def plot_spectrum(self):
        baseSpectrum = self.baseSpectra[self.index]
        with open(self.json_file, "w") as json_file:
            print(baseSpectrum.as_json(), file=json_file)
        self.browser.reload()

    @Slot(bool)
    def on_prevMaterialButton_clicked(self, checked):
        if self.index > 0:
            self.index = self.index - 1
            self.plot_spectrum()

    @Slot(bool)
    def on_nextMaterialButton_clicked(self, checked):
        if self.index < len(self.baseSpectra)-1:
            self.index = self.index + 1
            self.plot_spectrum()


class SampleSpectraViewerDialog(ui_view_spectra_dialog.Ui_Dialog, QDialog):
    def __init__(self, parent, scenario, detector, selected, file_list=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.scenario = scenario
        self.detector = detector
        self.selected = selected
        self.session = Session()
        self.json_file = os.path.join(get_bundle_dir(), "d3_resources", "spectrum.json")
        self.index = selected
        self.file_list = file_list

        if not self.file_list:
            sample_path = get_sample_dir(RaseSettings().getSampleDirectory(), self.detector, self.scenario.id)
            self.file_list = glob.glob(os.path.join(sample_path, "*.n42"))
            self.file_list.sort(key=natural_keys)

        self.browser = WebSpectraView(self)
        self.plot_spectrum()

        self.plot_layout = QVBoxLayout(self.widget)
        self.plot_layout.addWidget(self.browser)
        self.widget.setFocus()

    def plot_spectrum(self):
        filepath = self.file_list[self.index]
        status = []
        sharedObject = SharedObject(True)
        # FIXME: add error handling
        v = readSpectrumFile(filepath, sharedObject, status, requireRASESen=False)
        data = ReadFileObject(*v)

        with open(self.json_file, "w") as json_file:
            json_str = json.dumps([{"title": os.path.basename(filepath),
                            "livetime": data.livetime,
                            "realtime": data.realtime,
                            "xeqn": [data.ecal[0], data.ecal[1], data.ecal[2]],
                            "y": [float(c) for c in data.counts.split(',')],
                            "yScaleFactor": 1,
                            }])
            print(json_str, file=json_file)
        self.browser.reload()

    @Slot(bool)
    def on_prevMaterialButton_clicked(self, checked):
        if self.index >= 0:
            self.index = self.index - 1
            self.plot_spectrum()

    @Slot(bool)
    def on_nextMaterialButton_clicked(self, checked):
        if self.index < len(self.file_list)-1:
            self.index = self.index + 1
            self.plot_spectrum()


class WebSpectraView(QWebEngineView):
    def __init__(self, parent):
        super(WebSpectraView, self).__init__(parent)
        file_path = os.path.join(get_bundle_dir(), "d3_resources", "spectrum.html")
        local_url = QUrl.fromLocalFile(file_path)
        self.load(local_url)


class Result3DPlottingDialog(ui_results_plotting_dialog_3d.Ui_Dialog, QDialog):

    def __init__(self, parent, df, titles):
        QDialog.__init__(self)
        self.setupUi(self)
        self.df = df
        self.titles = titles
        self.colormap = matplotlib.pyplot.get_cmap('RdYlGn')

        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.widget)
        self.ax = self.fig.add_subplot(111)

        self.navi_toolbar = NavigationToolbar(self.canvas, self.widget)

        self.window_layout = QVBoxLayout(self.widget)
        self.window_layout.addWidget(self.canvas)
        self.window_layout.addWidget(self.navi_toolbar)

        matplotlib.pyplot.colorbar(mappable=self.ax.imshow(
                                                np.array(df.T, 'float'),
                                                cmap=self.colormap,
                                                vmin=df.min().min(),
                                                vmax=df.max().max(),
                                                interpolation='bicubic',
                                                aspect='auto'
                                            ), ax=self.ax)

        self.ax.xaxis.set_ticks(np.arange(df.shape[0]))
        self.ax.xaxis.set_ticklabels(df.index)
        self.ax.tick_params(axis='x', labelsize=16)
        self.ax.yaxis.set_ticks(np.arange(df.shape[1]))
        self.ax.yaxis.set_ticklabels(df.columns)
        self.ax.tick_params(axis='y', labelsize=16)

        for x_val in range(df.shape[1]):
            vals = np.array(df.iloc[:, x_val])
            x = np.arange(df.shape[0])
            y = x_val * np.ones_like(x)

            self.ax.plot(x[vals >= .75], y[vals > .75], 'wo', markerfacecolor='none', markersize='16')
            self.ax.plot(x[vals < .75], y[vals < .75], 'wx', markersize='16')

        self.ax.invert_yaxis()
        self.ax.set_xlabel(titles[0], size='16')
        self.ax.set_ylabel(titles[1], size='16')
        self.ax.set_title(titles[2], size='20')

        self.canvas.draw()
        self.widget.setFocus()


class ResultPlottingDialog(ui_results_plotting_dialog.Ui_Dialog, QDialog):

    def __init__(self, parent, x, y, titles, labels, replications, x_err=None, y_err=None):
        QDialog.__init__(self)
        self.setupUi(self)
        self.x = x
        self.y = y
        self.x_err = x_err
        self.y_err = y_err
        self.titles = titles
        self.labels = labels
        self.handles = []
        self.replications = replications
        self.palette = iter(sns.color_palette())
        self.params = [None for _ in range(len(self.x))]
        # # seaborn not compatible with lmfit
        # self.color_array = [['b', "#E5E7E9"], ['r', "#D5DbDb"], ['g', "#CCD1D1"],
        #                     ['m', "#CACFD2"], ['c', "#AAB7B8"], ['k', "#99A3A4"]]

        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.widget)
        self.ax = self.fig.add_subplot(111)

        self.navi_toolbar = NavigationToolbar(self.canvas, self.widget)

        self.window_layout = QVBoxLayout(self.widget)
        self.window_layout.addWidget(self.canvas)
        self.window_layout.addWidget(self.navi_toolbar)

        model = QStandardItemModel()
        for label in self.labels:
            item = QStandardItem(str(label))
            item.setCheckState(Qt.Checked)
            item.setCheckable(True)
            model.appendRow(item)
        self.lstCurves.setModel(model)
        if len(self.labels) == 1:
            self.lstCurves.hide()
            self.lblSelectCurves.hide()

        if len(self.x[0]) < 4 and self.y:
            self.groupBox.setEnabled(False)
            self.groupBox.setToolTip('Cannot plot s-curve with less than four data points.\n'
                                     'Please choose four or more data points to enable s-curve plotting.')

        if not self.y:
            self.groupBox.setEnabled(False)

        self.btnPlotData.clicked.connect(self.plotSelection)

        self.draw()
        self.widget.setFocus()

    def get_selected_labels(self):
        model = self.lstCurves.model()
        selected = [model.item(index).text() for index in range(model.rowCount()) if model.item(index).checkState()]
        return selected

    def draw(self):
        """
        Draws the initial plot of all the data
        """
        self.palette = iter(sns.color_palette())
        self.ax.clear()

        if self.y:
            self.ax.set_ylabel(self.titles[1])
            for i, (x, y, label) in enumerate(zip(self.x, self.y, self.labels)):
                y_err = np.transpose(self.y_err[i]) if i < len(self.y_err) else None
                x_err = np.transpose(self.x_err[i]) if i < len(self.x_err) else None
                color = next(self.palette)
                self.ax.errorbar(x, y, yerr=y_err, xerr=x_err,
                                 color=color, ecolor=color, fmt='o', capsize=3, label=label)
            if len(self.labels) > 1:
                self.ax.legend(bbox_to_anchor=(1.04, 1), loc="upper left", fontsize='xx-small')
        else:
            # min_n_entries = min([len(k) for k in self.x])
            # n_bins = 10 if min_n_entries <= 10 else int(np.sqrt(min_n_entries))
            self.ax.hist(self.x, bins=10, label=self.labels)
            self.ax.legend(fontsize='xx-small')

        self.ax.set_xlabel(self.titles[0])
        if (self.titles[0].startswith('Dose') or self.titles[0].startswith('BkgDose') or
            self.titles[0].startswith('Flux') or self.titles[0].startswith('BkgFlux')):
            self.ax.set_xscale('log')
        if (self.titles[1].startswith('Dose') or self.titles[1].startswith('BkgDose') or
            self.titles[1].startswith('Flux') or self.titles[1].startswith('BkgFlux')):
            self.ax.set_yscale('log')
        self.canvas.draw()

    @Slot(bool)
    def on_btnEditParams_clicked(self, checked):
        dialog = FitParamsSettings(self)
        if dialog.exec():
            self.params = dialog.params

    @Slot(bool)
    def plotSelection(self, checked):
        """
        Executes after the "plot S-curve(s)" button has been pressed and checkboxes have been checked
        (if there are any to be checked)
        """
        self.handles = []
        self.palette = iter(sns.color_palette())

        # to ensure zip and input data to s-curve function work as intended even if there is no data in the error vals
        if not self.x_err:
            x_error = [[None]] * len(self.x)
        else:
            x_error = self.x_err
        if not self.y_err:
            y_error = [[None]] * len(self.y)
        else:
            y_error = self.y_err

        self.ax.clear()
        for i, lab in enumerate([str(l) for l in self.labels]):
            if lab in self.get_selected_labels():
                color = next(self.palette)
                new_params = self.sCurveGen(lab, self.x[i], self.y[i], x_error[i], y_error[i],
                                            self.replications[i], color, self.params[i])
                if new_params:
                    self.params[i] = new_params

    def sCurveGen(self, label, x, y, x_err, y_err, repl, color, params):
        """
        S-curve fitting, analysis, and plotting
        """

        if x_err[0] is None:
            x_err = [None] * len(x)
        if y_err[0] is None:
            y_err = [None] * len(y)

        # compute fit weights from uncertainty in the data points
        errorbars = np.absolute([np.subtract((p, p), calc_result_uncertainty(p, n, alpha=0.32))
                                 for (p, n) in zip(y, repl)])
        weights = np.array([1. / ((h + l) / 2) for (h, l) in errorbars])  # weights by half total error bar length
        if np.isnan(np.sum(weights)):
            weights = None

        # if no user or previous parameters, use defaults and improve initial guesses based on data
        if not params:
            params = sCurve.get_default_fit_parameters()
            # set initial guess for 'M' parameter to the x value of the point closest to PID = 0.5
            params['M'].set(x[y.index(min(y, key=lambda i: abs(0.5 - i)))], min=min(x)/100, max=max(x)*100)
            # set initial guess for 'a1' and 'a2' parameter to the values at the extremes of the array
            y_left = y[x.index(min(x))]
            y_right = y[x.index(max(x))]
            params["a1"].set(y_right, min=y_right-0.3, max=y_right+0.3)
            params["a2"].set(y_left, min=y_left-0.3, max=y_left+0.3)
            # this one is purely empirical from typical s-curves in RASE work
            params['B'].set(params['M']/10.)

        # plot the data points
        if y_err[0] is not None:
            line = self.ax.errorbar(x, y, color=color, yerr=np.transpose(y_err), fmt='o', capsize=3, label=label)
        else:
            line, = self.ax.plot(x, y, color=color, fmt='o', label=label)
        self.handles.append(line)

        r = None
        if all([(not p.vary) for p in params.values()]):
            # all parameters are fixed, so can't really do fit
            x_dense = np.linspace(min(x), max(x), 150000)
            y_dense = sCurve.boltzmann_lin(x_dense, *[p.value for p in params.values()])
            line, = self.ax.plot(x_dense, y_dense, '-', color=color, label='S-curve (fixed params)')
            self.handles.append(line)
            self.txtFitResults.append("------------\n" + str(label) + "\n")
            self.txtFitResults.append('S-curve plotted from fixed parameters.')
        else:
            r = sCurve.s_fit(x, y, weights=weights, params=params)
            self.txtFitResults.append("------------\n" + str(label) + "\n")
            self.txtFitResults.append(r.fit_report(show_correl=False))

        if r:   # if fit happened
            if not r.success:
                QMessageBox.information(self, 'Information', 'Fit did not converge. Perhaps not enough points or '
                                                             "points don\'t follow a Sigmoid curve.")

            if r.covar is not None:
                x_dense = np.linspace(min(x), max(x), 150000)

                # plot fit line
                r_best = r.model.eval(r.params, x=x_dense)
                line, = self.ax.plot(x_dense, r_best, '-', color=color, label='S-curve fit')
                self.handles.append(line)

                # plot confidence band
                delta_y = r.eval_uncertainty(x=x_dense)
                if self.check_confint.isChecked() and not np.isnan(delta_y).any():
                    line = self.ax.fill_between(x_dense, r_best - delta_y, r_best + delta_y,
                                                color=color, alpha=0.3, label='68% fit confidence band')
                    self.handles.append(line)

                # compute and plot id threshold estimate
                if self.check_idshow.isChecked() and r.success:
                    id_mark = self.idThreshBox.value() / 100
                    thres_mark = sCurve.boltzmann_inverse(id_mark,
                                                          ufloat(r.params['a1'].value, r.params['a1'].stderr),
                                                          ufloat(r.params['a2'].value, r.params['a2'].stderr),
                                                          ufloat(r.params['B'].value, r.params['B'].stderr),
                                                          ufloat(r.params['M'].value, r.params['M'].stderr))
                    if (not isinstance(thres_mark, UFloat)) and np.isnan(thres_mark):
                        QMessageBox.information(self, 'Information', 'Cannot compute the ID threshold estimate. ')
                    else:
                        line, = self.ax.plot(thres_mark.nominal_value, id_mark, 'd', color=color, markersize=10,
                                             path_effects=[peff.Stroke(linewidth=2, foreground='black')])
                        if self.titles[0].split(' ')[0] == 'Dose':
                            id_label = str(id_mark * 100) + '%, Dose =\n' + str(thres_mark) + ' \u00B5Sv/hr'
                        elif self.titles[0].split(' ')[0] == 'Flux':
                            id_label = str(id_mark * 100) + '%, Flux =\n' + str(thres_mark) + ' (\u03B3/(cm\u00B2s))'
                        else:
                            id_label = str(id_mark * 100) + '%, ' + self.titles[0].split(' ')[0] + ' = ' + str(thres_mark)
                        line.set_label(id_label)
                        self.handles.append(line)

        self.ax.legend(handles=self.handles, bbox_to_anchor=(1.04, 1), loc="upper left", fontsize='xx-small')
        self.ax.set_title(None)
        self.ax.set_xscale('log')
        self.ax.set_ylim([-0.1, 1.1])

        self.ax.set_xlabel(self.titles[0])
        self.ax.set_ylabel(self.titles[1])
        self.canvas.draw()

        return r.params if (r and r.success) else None


class FitParamsSettings(ui_fit_params_settings_dialog.Ui_Dialog, QDialog):
    """Simple Dialog to customize the initial values and ranges of the s-curve fit parameters

    :param parent: the parent dialog, from which the current parameters are imported
    """
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.params = parent.params

        self.comboList.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        model = parent.lstCurves.model()
        self.sel_indexes = [index for index in range(model.rowCount()) if model.item(index).checkState()]
        self.sel_txts = [model.item(index).text() for index in range(model.rowCount()) if model.item(index).checkState()]
        self.comboList.addItems(self.sel_txts)

        self.pages = []
        self.pages_layouts = []
        self.pages_widgets = []
        for i, param_index in enumerate(self.sel_indexes):
            current_page = QWidget()
            self.pages.append(current_page)
            current_layout = QGridLayout(current_page)
            self.pages_layouts.append(current_layout)

            for k, label in enumerate(['Name', 'Fix', 'Initial Guess', 'Min', 'Max']):
                current_layout.addWidget(QLabel(label, current_page), 0, k)
            self.stackedWidget.addWidget(current_page)

            if not self.params[param_index]:
                self.params[param_index] = sCurve.get_default_fit_parameters()
            params = self.params[param_index]

            pw_dict = {'pname': {}, 'fix': {}, 'value': {}, 'min': {}, 'max': {}}
            self.pages_widgets.append(pw_dict)
            for j, name in enumerate(params, 1):
                pw_dict['pname'][name] = QLineEdit(name)
                current_layout.addWidget(pw_dict['pname'][name], j, 0)

                pw_dict['fix'][name] = QCheckBox()
                pw_dict['fix'][name].setChecked(not params[name].vary)
                current_layout.addWidget(pw_dict['fix'][name], j, 1)

                pw_dict['value'][name] = QLineEdit(f'{params[name].value:.4g}')
                pw_dict['value'][name].setValidator(DoubleValidator(pw_dict['value'][name]))
                pw_dict['value'][name].validator().validationChanged.connect(self.handle_validation_change)
                current_layout.addWidget(pw_dict['value'][name], j, 2)

                pw_dict['min'][name] = QLineEdit(f'{params[name].min:.4g}')
                pw_dict['min'][name].setValidator(DoubleValidatorInfinity(pw_dict['min'][name]))
                pw_dict['min'][name].validator().validationChanged.connect(self.handle_validation_change)
                current_layout.addWidget(pw_dict['min'][name], j, 3)

                pw_dict['max'][name] = QLineEdit(f'{params[name].max:.4g}')
                pw_dict['max'][name].setValidator(DoubleValidatorInfinity(pw_dict['max'][name]))
                pw_dict['max'][name].validator().validationChanged.connect(self.handle_validation_change)
                current_layout.addWidget(pw_dict['max'][name], j, 4)

        self.comboList.currentIndexChanged.connect(self.change_displayed_params)

    @Slot(int)
    def change_displayed_params(self, index):
        self.stackedWidget.setCurrentIndex(index)

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

    @Slot()
    def accept(self):
        """
        Object-level `params` variable is updated from the GUI values
        """
        for k, param_index in enumerate(self.sel_indexes):
            for name in self.params[param_index]:
                value = float(self.pages_widgets[k]['value'][name].text())
                bound_min = float(self.pages_widgets[k]['min'][name].text())
                bound_max = float(self.pages_widgets[k]['max'][name].text())
                vary = not self.pages_widgets[k]['fix'][name].isChecked()
                self.params[param_index][name].set(value, min=bound_min, max=bound_max, vary=vary)
        return QDialog.accept(self)
