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
from shutil import copyfile

from translators.translator_functions import write_results


def FileListing(TargetDirectory):
    """
    Retrieve directory listing of *.N42 files to be translated

    :param TargetDirectory: Path to directory with the RASE sampled spectra
    :return:
    """
    inSpecraFiles = []
    for file in os.listdir(TargetDirectory):
        if file.endswith('.n42'):
            if file.find('_AA_') != -1 or file.find('_AN_') != -1:
                inSpecraFiles.append(file)
    return inSpecraFiles


def CopyResults(input_dir, inSpecraFiles):
    """
    This function creates a copy of the results file in a separate directory. 
    This is to be consistent with the command-line replay tool folder structure.
    
    """
    results_dir = input_dir #+ '_results'

    if not os.path.exists(results_dir):
        os.makedirs(results_dir)

    for fname in inSpecraFiles:
         copyfile(os.path.join(input_dir[:-8], fname), os.path.join(results_dir, fname))


def retrieve_ORTEC_StdAlone_Results(filepath):
    """

    :param filepath:
    :return:
    """
    it = ET.parse(filepath)
    root = it.getroot()

    # Element.find() finds the child with a particular tag so the following
    # finds the first spectrum which is the item spectrum in RASE base spectra files
    resultsAll = root.find('AnalysisResults').find('RadiationDataAnalysis')

    resultsElements = resultsAll.findall('Nuclide')
   
    resultsArray = []

    for element in resultsElements:
        nuclideID = element.find('NuclideName')
        confidenceValue = element.find('NuclideIDConfidence')
        resultsArray.append(nuclideID.text, confidenceValue.text)

    return resultsArray


def main(input_dir, output_dir):
    in_files = FileListing(input_dir[:-8])
    CopyResults(input_dir, inSpecraFiles)
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    for fname in in_files:
        ResultsArray = retrieve_ORTEC_StdAlone_Results(os.path.join(input_dir, fname))
        write_results(ResultsArray, os.path.join(output_dir, fname))
    return


if __name__ == "__main__":

    import sys

    if len(sys.argv) < 3:
        print("ERROR: Need input and output folder!")
        sys.exit(1)
    
    main(sys.argv[1], sys.argv[2])
