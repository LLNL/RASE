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
This module provides information and documentation about RASE
"""

import os, sys

from PyQt5.QtCore import QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView
from src.utils import get_bundle_dir


class HelpDialog(QWebEngineView):
    def __init__(self, parent):
        super(HelpDialog, self).__init__()

        self.resize(1200, 800)
        self.setWindowTitle('RASE Help')

        self.setZoomFactor(1.0)

        index_path = os.path.join(get_bundle_dir(), "doc", "_build", "html", "index.html")
        self.load(QUrl.fromLocalFile(index_path))


