###############################################################################
# Copyright (c) 2018-2022 Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory
#
# Written by J. Brodsky, J. Chavez, S. Czyz, G. Kosinovsky, V. Mozin, S. Sangiorgio.
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
This module defines the top level executable of RASE
"""
import sys
import traceback
import os
import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMessageBox
from src.rase import Rase
from src.rase_settings import RaseSettings

RASE_VERSION = 'v2.3'

if getattr(sys, 'frozen', False):
    # we are in a pyinstaller bundle
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

# configure the logger
# TODO: Remember to update the version number at each release!
logFile = os.path.join(application_path, "rase.log")
FORMAT = '%(asctime)-15s RASE' + RASE_VERSION + ' %(levelname)s %(message)s'
logging.basicConfig(filename=logFile, level=logging.DEBUG, format=FORMAT)

# hide annoying matplotlib debug logs
logging.getLogger("matplotlib.backends.backend_pdf").setLevel(logging.ERROR)
logging.getLogger("matplotlib.colorbar").setLevel(logging.ERROR)
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
logging.getLogger("matplotlib.ticker").setLevel(logging.ERROR)

def log_except_hook(eType, eValue, tracebackobj):
    """
    Custom handler to catch and log unhandled exceptions.

    @param eType exception type
    @param eValue exception value
    @param tracebackobj traceback object
    """
    # log the exception
    logging.exception("Unhandled Exception", exc_info=(eType, eValue, tracebackobj))
    logging.info("RASE Settings:\n" + RaseSettings().getAllSettingsAsText())

    # In case there is a connected console, print exception to stderr
    traceback.print_exception(eType, eValue, tracebackobj)

    # Tell the user
    msg_box = QMessageBox()
    msg_box.setText('An unhandled exception occurred.')
    notice = \
        """Please report the problem """ \
        """via email to rase-support@llnl.gov.\n\n""" \
        """A log has been written to \n "%s".""" % logFile
    msg_box.setInformativeText(notice)
    err_msg = ''.join(traceback.format_exception(eType, eValue, tracebackobj))
    msg_box.setDetailedText(err_msg)
    msg_box.setIcon(QMessageBox.Critical)
    msg_box.exec()

    # quit
    sys.exit(1)


# Install custom exception handler
sys.excepthook = log_except_hook


if __name__ == '__main__':
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)  # enable highdpi scaling
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)  # use highdpi icons
    app = QApplication(sys.argv)
    win = Rase(sys.argv)
    win.show()
    app.exec()

