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

import os
import sys
from shutil import copy2

dirname = os.path.abspath(os.path.dirname(__file__))
buildpath = os.path.join(dirname, "..", "build", "translators")
distpath = os.path.join(dirname, "..", "dist", "translators")

if not os.path.exists(distpath):
     os.makedirs(distpath)

# Naming convention: <Vendor><Model>-<Notes>_ResultsTranslator.py
translators = ['FLIRIdentiFinder_ResultsTranslator.py',
               'KromekD5_ResultsTranslator.py',
               'KromekD5-data_ResultsTranslator.py',
               'ORTEC-CmdLineReplayTool_ResultsTranslator.py',
               'ORTEC-StndAloneGUIReplayTool_ResultsTranslator.py',
               'SmithRadSeeker_ResultsTranslator.py',
               'Symetrica_ResultsTranslator.py',
               ]
translators = map(lambda x: os.path.join(dirname, x), translators)

for translator in translators:
    os.system(sys.executable + " -m PyInstaller -a -y -F -c --clean --noupx" +
          " --distpath " + distpath +
          " --workpath " + buildpath +
          " --specpath=" + dirname +
          " " + translator)
    print("\n\n")
