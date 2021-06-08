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
This module provides plotting support for RASE analysis
"""
import glob
import json
from itertools import cycle
import os
import numpy as np
import matplotlib
from sqlalchemy.orm import Session

matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.figure import Figure
from matplotlib import rcParams
import matplotlib.patheffects as peff
rcParams.update({'figure.autolayout': True})

import seaborn as sns
sns.set(font_scale=1.5)
sns.set_style("whitegrid")

from PyQt5.QtCore import pyqtSlot, Qt, QUrl
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QMessageBox
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWebEngineWidgets import QWebEngineView

from .ui_generated import ui_view_spectra_dialog, ui_results_plotting_dialog
from src.rase_functions import calc_result_uncertainty, get_sample_dir, readSpectrumFile
import src.s_curve_functions as sCurve
from src.utils import get_bundle_dir, natural_keys
from src.base_spectra_dialog import SharedObject, ReadFileObject
from src.rase_settings import RaseSettings


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
            print(baseSpectrum.as_json(self.detector), file=json_file)
        self.browser.reload()

    @pyqtSlot(bool)
    def on_prevMaterialButton_clicked(self, checked):
        if self.index > 0:
            self.index = self.index - 1
            self.plot_spectrum()

    @pyqtSlot(bool)
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

    @pyqtSlot(bool)
    def on_prevMaterialButton_clicked(self, checked):
        if self.index >= 0:
            self.index = self.index - 1
            self.plot_spectrum()

    @pyqtSlot(bool)
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
        self.replications = replications
        self.palette = None
        # seaborn not compatible with lmfit
        self.color_array = [['b', "#E5E7E9"], ['r', "#D5DbDb"], ['g', "#CCD1D1"],
                            ['m', "#CACFD2"], ['c', "#AAB7B8"], ['k', "#99A3A4"]]

        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.widget)
        self.ax = self.fig.add_subplot(111)

        self.navi_toolbar = NavigationToolbar(self.canvas, self.widget)

        self.alphaCBox.addItem('\u03B1 = 0.01 (99%)', 0.01)
        self.alphaCBox.addItem('\u03B1 = 0.05 (95%)', 0.05)
        self.alphaCBox.addItem('\u03B1 = 0.1 (90%)', 0.1)
        self.alphaCBox.addItem('\u03B1 = 0.32 (68%)', 0.32)
        self.alphaCBox.setCurrentIndex(1)

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
        if not self.labels:
            self.lstCurves.hide()
            self.lblSelectCurves.hide()

        if len(self.x[0]) < 4:
            self.groupBox.setEnabled(False)
            self.groupBox.setToolTip('Cannot plot s-curve with less than four data points.\n'
                                     'Please choose four or more data points to enable s-curve plotting.')

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
        self.palette = cycle(sns.color_palette())
        self.ax.clear()

        if self.y:
            self.ax.set_ylabel(self.titles[1])
            if self.labels:
                for i, (x, y, label) in enumerate(zip(self.x, self.y, self.labels)):
                    y_err = np.transpose(self.y_err[i]) if i < len(self.y_err) else None
                    x_err = np.transpose(self.x_err[i]) if i < len(self.x_err) else None
                    color = next(self.palette)
                    self.ax.errorbar(x, y, yerr=y_err, xerr=x_err,
                                     color=color, ecolor=color, fmt='o', capsize=3, label=label)
                self.ax.legend(bbox_to_anchor=(1.04, 1), loc="upper left", fontsize='xx-small')
            else:
                y_err = np.transpose(self.y_err[0]) if self.y_err else None
                x_err = np.transpose(self.x_err[0]) if self.x_err else None
                color = next(self.palette)
                self.ax.errorbar(self.x[0], self.y[0], yerr=y_err, xerr=x_err,
                                 color=color, ecolor=color, fmt='o', capsize=3)
        else:
            QMessageBox.information(self, "Info", "Histogram plotting not yet implemented!")

        self.ax.set_xlabel(self.titles[0])
        if (self.titles[0].startswith('Dose') or self.titles[0].startswith('BkgDose') or
            self.titles[0].startswith('Flux') or self.titles[0].startswith('BkgFlux')):
            self.ax.set_xscale('log')
        if (self.titles[1].startswith('Dose') or self.titles[1].startswith('BkgDose') or
            self.titles[1].startswith('Flux') or self.titles[1].startswith('BkgFlux')):
            self.ax.set_yscale('log')
        self.canvas.draw()

    @pyqtSlot(bool)
    def plotSelection(self, checked):
        """
        Executes after the "plot S-curve(s)" button has been pressed and checkboxes have been checked
        (if there are any to be checked)
        """
        self.ax_text = []

        # to ensure zip and input data to s-curve function work as intended even if there is no data in the error vals
        if not self.x_err:
            x_error = [[None]] * len(self.x)
        else:
            x_error = self.x_err
        if not self.y_err:
            y_error = [[None]] * len(self.y)
        else:
            y_error = self.y_err

        if self.labels:
            self.ax.clear()
            self.draw()
            for index, (lab, x_vals, y_vals, err_x, err_y, repl) in \
                    enumerate(zip(self.labels, self.x, self.y, x_error, y_error, self.replications)):
                if str(lab) in self.get_selected_labels():
                    color, color_hash = self.color_array[index % 6]
                    self.sCurveGen(lab, x_vals, y_vals, err_x, err_y, repl, color, color_hash)
        else:
            self.ax.clear()
            self.sCurveGen('Data', self.x[0], self.y[0], x_error[0], y_error[0], self.replications[0], 'b', '#e5e7e9')

    def sCurveGen(self, label, x, y, x_err, y_err, repl, color, color_hash):

        # TODO: Automatically trim off all (x, y) pairs that are above the first 1 and below the last 0 to prevent
        #  fits from failing to converge or giving wonky results
        if x_err[0] is None:
            x_err = [None] * len(x)
        if y_err[0] is None:
            y_err = [None] * len(y)

        id_mark = self.idThreshBox.value() / 100
        alpha = self.alphaCBox.itemData(self.alphaCBox.currentIndex())
        B = 1
        Q = 1
        if self.combo_fitspace.currentText() == 'Logarithmic':
            logfit = True
        else:
            logfit = False

        errorbars = np.absolute([np.subtract((p, p), calc_result_uncertainty(p, n, alpha))
                                 for (p, n) in zip(y, repl)])
        weights = np.array([1. / ((h + l) / 2) for (h, l) in errorbars])  # weights by half total error bar length
        if np.isnan(np.sum(weights)):
            weights = None

        r = sCurve.s_fit(x, y, weights, [B, Q], logfit)
        p = [r.params[u].value for u in r.var_names]
        try:
            (a1, a2, B, Q) = sCurve.correlated_values(p, r.covar)
        except:
            (a1, a2, B, Q) = (0, 0, 0, 0)

        self.txtFitResults.append("------------\n" + str(label) + "\n")
        self.txtFitResults.append(r.fit_report(show_correl=False))
        self.ax_text.append(label)
        self.ax.plot(x, y, 'o', color=color, label='_nolegend_')

        if r.covar is not None:
            r.plot_fit(datafmt=' ', fitfmt=color + '-', yerr=[0] * (len(y)), ax=self.ax, numpoints=150000)
            x_dense = np.linspace(min(x), max(x), 150000)
            delta_y = r.eval_uncertainty(x=x_dense)
            r_best = r.model.eval(r.params, x=x_dense)
            if self.check_confint.isChecked():
                self.ax.fill_between(x_dense, r_best - delta_y, r_best + delta_y, color=color_hash)
        else:
            # no confidence band to plot, so don't make fit
            self.ax.plot(x, y, color + 'o')

        if not y_err[0] is None:
            self.ax.errorbar(x, y, color=color, yerr=np.transpose(y_err), fmt='none', capsize=3)

        if self.check_idshow.isChecked():
            thresh_mark_nom, thresh_mark_stdev = sCurve.thresh_mark(a1, a2, B, Q, id_mark, logfit)
            if thresh_mark_nom == thresh_mark_stdev == 0:
                pass
            else:
                self.ax.plot(thresh_mark_nom, id_mark, color + 'd', label=str(id_mark * 100) + '%: ' +
                                                                          str(thresh_mark_nom), markersize=10,
                             path_effects=[peff.Stroke(linewidth=2, foreground='black')])
                if self.titles[0].split(' ')[0] == 'Dose':
                    self.ax_text.append(str(id_mark * 100) + '%, Dose =\n' +
                                        str(sCurve.ufloat(thresh_mark_nom, thresh_mark_stdev)) + ' \u00B5Sv/hr')
                elif self.titles[0].split(' ')[0] == 'Flux':
                    self.ax_text.append(str(id_mark * 100) + '%, Flux =\n' +
                                        str(sCurve.ufloat(thresh_mark_nom,
                                                          thresh_mark_stdev)) + ' (\u03B3/(cm\u00B2s))')
                else:
                    self.ax_text.append(str(id_mark * 100) + '%, ' + self.titles[0].split(' ')[0] + ' = ' +
                                        str(sCurve.ufloat(thresh_mark_nom, thresh_mark_stdev)))

        self.ax.legend(self.ax_text, bbox_to_anchor=(1.04, 1), loc="upper left", fontsize='xx-small')
        self.ax.set_title(None)
        self.ax.set_xscale('log')
        self.ax.set_ylim([-0.1, 1.1])

        self.ax.set_xlabel(self.titles[0])
        self.ax.set_ylabel(self.titles[1])
        self.canvas.draw()
