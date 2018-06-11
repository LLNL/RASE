### Static Parameters ###
# TemplateSpectrum = 'FLIR-ID-2_TemplateSpectrum_CmdLine.n42'
### End of the Static Parameters ###

import os
import xml.etree.ElementTree as ET


def FileListing(TargetDirectory):
    """
    Retrieve directory listing of *.n42 files to be translated

    :param TargetDirectory: Path to directory with the RASE sampled spectra
    :return:
    """
    inSpecraFiles = []
    for file in os.listdir(TargetDirectory):
        if file.endswith('.n42'):
            inSpecraFiles.append(file)
    return inSpecraFiles


def retrieve_FLIR_Results(filepath):
    """

    :param filepath:
    :return:
    """
    it = ET.parse(filepath)
    root = it.getroot()

    # Element.find() finds the child with a particular tag so the following
    # finds the first spectrum which is the item spectrum in RASE base spectra files
    resultsAll = root.find('{http://physics.nist.gov/N42/2011/N42}AnalysisResults').find(
        '{http://physics.nist.gov/N42/2011/N42}NuclideAnalysisResults')
    resultsElements = resultsAll.findall('{http://physics.nist.gov/N42/2011/N42}Nuclide')

    resultsArray = [[], []]

    for element in resultsElements:
        nuclideID = element.find('{http://physics.nist.gov/N42/2011/N42}NuclideName')
        confidenceValue = element.find('{http://physics.nist.gov/N42/2011/N42}NuclideIDConfidenceValue')
        resultsArray[0].append(nuclideID.text)
        resultsArray[1].append(confidenceValue.text)

    return resultsArray


def indent(elem, level=0):
    '''
    copy and paste from http://effbot.org/zone/element-lib.htm#prettyprint
    it basically walks your tree and adds spaces and newlines so the tree is
    printed in a nice way
    '''

    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def write_FLIR_results(resultsArray, outFilepath):
    """

    :param :
    :return:
    """

    # create XML 
    #    root = ET.Element('IdentificationResults')
    #    #root.append(ET.Element('Isotope'))
    #    child1 = ET.Element('Isotope')
    #    child1.text = 'Am-241'
    #    root.append(child1)

    root = ET.Element('IdentificationResults')

    for iso, conf in zip(resultsArray[0], resultsArray[1]):
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
        ResultsArray = retrieve_FLIR_Results(os.path.join(input_dir, fname))

        newFileName = os.path.join(output_dir, fname)

        write_FLIR_results(ResultsArray, newFileName)

    return


if __name__ == "__main__":

    import sys

    if len(sys.argv) < 3:
        print("ERROR: Need input and output folder!")
        sys.exit(1)

    cwd = os.path.dirname(sys.argv[0])
    main(sys.argv[1], sys.argv[2], cwd)
