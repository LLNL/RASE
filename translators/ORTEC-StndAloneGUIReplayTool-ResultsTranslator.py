import os
import xml.etree.ElementTree as ET
from shutil import copyfile

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
    This is to be consistent with the comman-line replay tool folder structure.
    
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
   
    resultsArray = [[],[]]
    
    for element in resultsElements:
        nuclideID = element.find('NuclideName')
        confidenceValue = element.find('NuclideIDConfidence')
        resultsArray[0].append(nuclideID.text)
        resultsArray[1].append(confidenceValue.text)
    
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

def write_ORTEC_StdAlone_results(resultsArray, outFilepath):
    """

    :param :
    :return:
    """
        
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

    inSpecraFiles = FileListing(input_dir[:-8])

    CopyResults(input_dir, inSpecraFiles)

    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    for fname in inSpecraFiles:

        ResultsArray = retrieve_ORTEC_StdAlone_Results(os.path.join(input_dir, fname))
        newFileName = os.path.join(output_dir, fname)
        write_ORTEC_StdAlone_results(ResultsArray, newFileName)

    return


if __name__ == "__main__":

    import sys

    if len(sys.argv) < 3:
        print("ERROR: Need input and output folder!")
        sys.exit(1)
    
    cwd = os.path.dirname(sys.argv[0])
    main(sys.argv[1], sys.argv[2], cwd)
