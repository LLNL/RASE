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
This module provides plotting support for RASE analysis
"""

from itertools import groupby, cycle

import numpy as np
import matplotlib

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

from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QSizePolicy, QMessageBox
from PyQt5.QtGui import QStandardItemModel, QStandardItem

from .ui_generated import ui_view_spectra_dialog, ui_results_plotting_dialog
from src.rase_functions import calc_result_uncertainty
import src.s_curve_functions as sCurve


class SpectraViewerDialog(ui_view_spectra_dialog.Ui_Dialog, QDialog):
    def __init__(self, parent, session, base_spectra, selected):
        QDialog.__init__(self)
        self.setupUi(self)
        self.baseSpectra = base_spectra
        self.selected = selected
        self.session = session
        # self.setParent(parent)

        self.label.setText(self.selected)

        counts = np.array([])
        for baseSpectrum in self.baseSpectra:
            if baseSpectrum.material.name == self.selected:
                counts = baseSpectrum.get_counts_as_np()

        self.plot_layout = QVBoxLayout(self.widget)
        self.plot_canvas = SpectrumPlot(counts, self.widget, width=5, height=4, dpi=100)
        self.navi_toolbar = NavigationToolbar(self.plot_canvas, self)
        self.plot_layout.addWidget(self.plot_canvas)  # the matplotlib canvas
        self.plot_layout.addWidget(self.navi_toolbar)

        self.widget.setFocus()


class SpectrumPlot(FigureCanvas):
    """
    Plots Spectrum
    """

    def __init__(self, counts, parent=None, width=5, height=4, dpi=100):

        self.counts = counts

        fig = Figure(figsize=(width, height), dpi=dpi)
        self.ax = fig.add_subplot(111)

        self.plot_initial_figure()

        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def plot_initial_figure(self):
        self.ax.set_yscale("log", nonposy='clip')
        self.ax.plot(self.counts)


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
            for index, (lab, x_vals, y_vals, err_x, err_y) in enumerate(zip(self.labels, self.x, self.y, x_error, y_error)):
                if str(lab) in self.get_selected_labels():
                    color, color_hash = self.color_array[index % 6]
                    self.sCurveGen(lab, x_vals, y_vals, err_x, err_y, color, color_hash)
        else:
            self.ax.clear()
            self.sCurveGen('Data', self.x[0], self.y[0], x_error[0], y_error[0], 'b', '#e5e7e9')

    def sCurveGen(self, label, x, y, x_err, y_err, color, color_hash):

        # TODO: Automatically trim off all (x, y) pairs that are above the first 1 and below the last 0 to prevent
        #  fits from failing to converge or giving wonky results
        if x_err[0] is None:
            x_err = [None] * len(x)
        if y_err[0] is None:
            y_err = [None] * len(y)

        id_mark = self.idThreshBox.value() / 100
        alpha = self.alphaCBox.itemData(self.alphaCBox.currentIndex())
        s = 1
        Q = 1
        if self.combo_fitspace.currentText() == 'Logarithmic':
            logfit = True
        else:
            logfit = False

        errorbars = np.absolute([np.subtract((p, p), calc_result_uncertainty(p, n, alpha))
                                 for (p, n) in zip(y, self.replications)])
        weights = np.array([1. / ((h + l) / 2) for (h, l) in errorbars])  # weights by half total error bar length
        if np.isnan(np.sum(weights)):
            weights = None
        r = sCurve.s_fit(x, y, weights, [s, Q], logfit)
        # TODO: Throw message if nothing can be fit alerting the user
        p = [r.params[u].value for u in r.var_names]
        try:
            (a1, a2, s, Q) = sCurve.correlated_values(p, r.covar)
        except:
            (a1, a2, s, Q) = (0, 0, 0, 0)

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
            thresh_mark_nom, thresh_mark_stdev = sCurve.thresh_mark(a1, a2, s, Q, id_mark, logfit)
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
