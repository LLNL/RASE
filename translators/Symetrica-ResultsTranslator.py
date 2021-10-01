### Static Parameters ###
# TemplateSpectrum = 'Symetrica_SN33N_template.n42'
### End of the Static Parameters ###

import os
import xml.etree.ElementTree as ET

from src.rase_functions import write_results


def retrieve_Symetrica_Results(filepath):
    """

    :param filepath:
    :return:
    """
    it = ET.parse(filepath)
    root = it.getroot()

    resultsArray = []

    resultsAll = root.find('.//{http://physics.nist.gov/N42/2011/N42}NuclideAnalysisResults')

    if resultsAll:
        resultsElements = resultsAll.findall('{http://physics.nist.gov/N42/2011/N42}Nuclide')
        for element in resultsElements:
            nuclideID = element.find('{http://physics.nist.gov/N42/2011/N42}NuclideName')
            confidenceValue = element.find('{http://physics.nist.gov/N42/2011/N42}NuclideIDConfidenceValue')
            resultsArray.append((nuclideID.text, confidenceValue.text))

    return resultsArray


def main(input_dir, output_dir):
    in_files = [f for f in os.listdir(input_dir) if f.lower().endswith(".n42")]

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for fname in in_files:
        ResultsArray = retrieve_Symetrica_Results(os.path.join(input_dir, fname))
        write_results(ResultsArray, os.path.join(output_dir, fname))
    return


if __name__ == "__main__":

    import sys

    if len(sys.argv) < 3:
        print("ERROR: Need input and output folder!")
        sys.exit(1)

    main(sys.argv[1], sys.argv[2])
