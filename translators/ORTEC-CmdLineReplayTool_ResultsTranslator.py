###############################################################################
# Copyright (c) 2018-2023 Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory
#
# Written by J. Brodsky, J. Chavez, S. Czyz, G. Kosinovsky, V. Mozin,
#            S. Sangiorgio.
#
# RASE-support@llnl.gov.
#
# LLNL-CODE-858590, LLNL-CODE-829509
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
import xml.etree.ElementTree as ET
import re

from translators.translator_functions import write_results


def retrieveResults(filepath):
    """

    :param filepath:
    :return:
    """
    it = ET.parse(filepath)
    root = it.getroot()

    # Element.find() finds the child with a particular tag so the following
    # finds the first spectrum which is the item spectrum in RASE base spectra files

    nuclideID = root.find('Isotope')
    confidenceValue = root.find('ConfidenceIndex')

    # split all identifications using regex
    nuclides = [m.strip() for mm in re.findall('"([^"]*)"|( [^"]\S*)|(^[^"]\S*)', nuclideID.text) for m in mm if m]
    confidences = confidenceValue.text.split()

    return list(zip(nuclides, confidences))


def main(input_dir, output_dir):
    in_files = [f for f in os.listdir(input_dir) if f.lower().endswith(".res")]

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for fname in in_files:
        ResultsArray = retrieveResults(os.path.join(input_dir, fname))
        newFileName = os.path.join(output_dir, fname[:-4] + '.n42')
        write_results(ResultsArray, newFileName)
    return


if __name__ == "__main__":

    import sys

    if len(sys.argv) < 3:
        print("ERROR: Need input and output folder!")
        sys.exit(1)

    main(sys.argv[1], sys.argv[2])
#   main('./ORTEC CmdLine_results','./ORTEC CmdLine_translatedResults')
