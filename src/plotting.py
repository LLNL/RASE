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
This module provides plotting support for RASE analysis
"""

from itertools import groupby

import numpy as np
import matplotlib

matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.figure import Figure

from .ui_generated import ui_view_spectra_dialog
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QSizePolicy


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



class HistPlot(FigureCanvas):
    """
    Plots Histogram
    """

    def __init__(self, data, titles):
        fig = Figure()
        FigureCanvas.__init__(self, fig)
        x = data[0]
        y = data[1]

        ind = np.arange(len(x)) + .1

        ax = fig.add_subplot(111)
        rects1 = ax.bar(ind, y)

        # add some text for labels, title and axes ticks
        ax.set_xlabel(titles[0])
        ax.set_ylabel(titles[1])
        #ax.set_title('Correct by scenario and detector')
        ax.set_xticks(ind+.5)
        ax.set_xticklabels(x)

class LinePlot(FigureCanvas):
    """
    Plots Line Plot
    """

    def __init__(self, data, titles):
        fig = Figure()
        FigureCanvas.__init__(self, fig)
        ax = fig.add_subplot(111)
        # add some text for labels, title and axes ticks
        ax.set_xlabel(titles[0])
        ax.set_ylabel(titles[2])
        #ax.set_title('Correct by scenario and detector')
        data = groupby(sorted(zip(*data), key=lambda point: point[1]), lambda point: point[1])
        for k,g in data:
            x, y, z = (zip(*g))
