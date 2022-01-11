import os
import xml.etree.ElementTree as ET
import re

def FileListing(TargetDirectory):
    """
    Retrieve directory listing of *.res files to be translated

    :param TargetDirectory: Path to directory with the RASE sampled spectra
    :return:
    """
    inSpecraFiles = []
    for file in os.listdir(TargetDirectory):
        if file.endswith('.res'):
            inSpecraFiles.append(file)
    return inSpecraFiles


def retrieveResults(filepath):
    """

    :param filepath:
    :return:
    """
    it = ET.parse(filepath)
    root = it.getroot()

    # Element.find() finds the child with a particular tag so the following
    # finds the first spectrum which is the item spectrum in RASE base spectra files

    resultsArray = [[],[]]

    nuclideID = root.find('Isotope')
    confidenceValue = root.find('ConfidenceIndex')

    # split all identifications using regex
    resultsArray[0] = [m.strip() for mm in re.findall('"([^"]*)"|( [^"]\S*)|(^[^"]\S*)', nuclideID.text) for m in mm if m]

    resultsArray[1] = confidenceValue.text.split()

    return resultsArray


def indent(elem, level=0):
  i = "\n" + level*"  "
  if len(elem):
    if not elem.text or not elem.text.strip():
      elem.text = i + "  "
    if not elem.tail or not elem.tail.strip():
      elem.tail = i
    for elem in elem:
      indent(elem, level+1)
    if not elem.tail or not elem.tail.strip():
      elem.tail = i
  else:
    if level and (not elem.tail or not elem.tail.strip()):
      elem.tail = i


def writeResults(resultsArray, outFilepath):
    """

    :param :
    :return:
    """

    # create XML
    root = ET.Element('IdentificationResults')

    for iso, conf in zip(resultsArray[0],resultsArray[1]):
        identification = ET.SubElement(root, 'Identification')
        isotope = ET.SubElement(identification, 'IDName')
        isotope.text = iso
        confidence = ET.SubElement(identification, 'IDConfidence')
        confidence.text = conf

    indent(root)
    tree = ET.ElementTree(root)
    # write entire XML out to new file
    tree.write(outFilepath, encoding='utf-8', xml_declaration=True, method='xml')

    return

def main(input_dir, output_dir, template_dir="./"):

    inSpecraFiles = FileListing(input_dir)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for fname in inSpecraFiles:

        ResultsArray = retrieveResults(os.path.join(input_dir, fname))

        newFileName = os.path.join(output_dir, fname[:-4] + '.n42')

        writeResults(ResultsArray, newFileName)

    return


if __name__ == "__main__":

    import sys

    if len(sys.argv) < 3:
        print("ERROR: Need input and output folder!")
        sys.exit(1)

    cwd = os.path.dirname(sys.argv[0])
    main(sys.argv[1], sys.argv[2], cwd)
#   main('./ORTEC CmdLine_results','./ORTEC CmdLine_translatedResults')