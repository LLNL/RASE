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
This module defines the top level executable of RASE
"""
import sys
import traceback
import os
import logging

from PyQt5.QtWidgets import QApplication, QMessageBox
from src.rase import Rase
from src.rase_settings import RaseSettings

RASE_VERSION = 'v1.0b2'

# configure the logger
# TODO: Remember to update the version number at each release!
logFile = os.path.expanduser(os.path.join("~", "rase.log"))
FORMAT = '%(asctime)-15s' + RASE_VERSION + '%(levelname)s %(message)s'
logging.basicConfig(filename=logFile, level=logging.DEBUG, format=FORMAT)


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
    notice = \
        """An unhandled exception occurred. \n\n """ \
        """Please report the problem\n""" \
        """via email to rase-support@llnl.gov.\n""" \
        """A log has been written to "%s".\n\n""" \
        """Error information:\n""" % logFile
    errmsg = '%s: \n%s' % (str(eType), str(eValue))
    QMessageBox().critical(None, "Unhandled Exception", notice + errmsg)

    # quit
    sys.exit(1)


# Install custom exception handler
sys.excepthook = log_except_hook


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = Rase(sys.argv)
    win.show()
    app.exec_()

