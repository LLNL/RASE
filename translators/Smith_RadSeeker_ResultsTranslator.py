#!/usr/bin/python3
### Static Parameters ###
# TemplateSpectrum = 'FLIR-ID-2_TemplateSpectrum_CmdLine.n42'
### End of the Static Parameters ###

import os
import xml.etree.ElementTree as ET

from src.rase_functions import write_results


def retrieve_results(filepath):
    """

    :param filepath:
    :return:
    """
    it = ET.parse(filepath)
    resultsArray=[]
    for nuclide in it.iter('Nuclide'):
        nucname = nuclide.find('NuclideName').text
        confidenceValue = nuclide.find('NuclideIDConfidence').text
        resultsArray.append((nucname,confidenceValue))

    return resultsArray


def main(input_dir, output_dir):
    in_files = [f for f in os.listdir(input_dir) if f.lower().endswith(".n42")]

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for fname in in_files:
        ResultsArray = retrieve_results(os.path.join(input_dir, fname))
        write_results(ResultsArray, os.path.join(output_dir, fname))
    return


if __name__ == "__main__":

    import sys

    if len(sys.argv) < 3:
        print("ERROR: Need input and output folder!")
        sys.exit(1)

    main(sys.argv[1], sys.argv[2])
