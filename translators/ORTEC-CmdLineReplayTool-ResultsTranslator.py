import os
import xml.etree.ElementTree as ET
import re

from src.rase_functions import write_results


def retrieveResults(filepath):
    """

    :param filepath:
    :return:
    """
    it = ET.parse(filepath)
    root = it.getroot()

    # Element.find() finds the child with a particular tag so the following
    # finds the first spectrum which is the item spectrum in RASE base spectra files

    resultsArray = [[], []]

    nuclideID = root.find('Isotope')
    confidenceValue = root.find('ConfidenceIndex')

    # split all identifications using regex
    resultsArray[0] = [m.strip() for mm in re.findall('"([^"]*)"|( [^"]\S*)|(^[^"]\S*)', nuclideID.text) for m in mm if m]

    resultsArray[1] = confidenceValue.text.split()

    return resultsArray


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
