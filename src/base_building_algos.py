import xml.etree.ElementTree as etree
from src import rase_functions as Rf
import numpy
import copy
import os.path
import re
from sandbox import rebin as rebinner


def remove_control_characters(xml):
    def str_to_int(s, default, base=10):
        if int(s, base) < 0x10000:
            return chr(int(s, base))
        return default
    xml = re.sub(r"&#(\d+);?", lambda c: str_to_int(c.group(1), c.group(0)), xml)
    xml = re.sub(r"&#[xX]([0-9a-fA-F]+);?", lambda c: str_to_int(c.group(1), c.group(0), base=16), xml)
    xml = re.sub(r"[\x00-\x08\x0b\x0e-\x1f\x7f]", "", xml)
    return xml

def insert_RASE_Sensitivity(specElement,Rsens):
    """ Adds RASE Sensitivity to a Spectrum element
    :param specElement:
    :param Rsens:
    :return:
    """
    existing_rsens = specElement.findall('RASE_Sensitivity')
    for rsens in existing_rsens:
        specElement.remove(rsens)
    RsensElement = etree.Element('RASE_Sensitivity')
    RsensElement.text = str(Rsens)
    specElement.append(RsensElement)

def uncompressCountedZeroes(counts):
    """ Standard CountedZeroes uncompress method.
    Similar to implementations elsewhere in RASE code, but this one a) does not confirm CounterZeroes compression
    is in use and b) outputs to a numpy ndarray
    """
    uncompressedCounts = []
    counts_iter = iter(counts)
    for count in counts_iter:
        if count == float(0):
            uncompressedCounts.extend([0] * int(next(counts_iter)))
        else:
            uncompressedCounts.append(count)
    return numpy.fromiter(uncompressedCounts,float)

def get_counts(specEl):
    """Retrieve counts as a numpy ndarray from the first ChannelData element in the given Spectrum element
    Calls Uncompress method if the ChannelData element has an attribute containing
    "compression" equal to "CountedZeroes".
    """
    chandataEl= Rf.requiredElement('ChannelData',specEl)
    counts = numpy.fromstring(chandataEl.text,float,sep=' ')
    for attribute,value in chandataEl.attrib.items():
        if 'COMPRESSION' in attribute.upper() and value=='CountedZeroes':
            return uncompressCountedZeroes(counts)
    else:
        return counts

def get_livetime(specEl):
    """Retrieves Livetime as a float from the Spectrum element
    """
    timetext = Rf.requiredElement(('LiveTimeDuration','LiveTime'),specEl).text
    return Rf.ConvertDurationToSeconds(timetext)

def subtract_spectra(specEl_meas, specEl_bkg):
    """Given two Spectrum elements, returns (as an ndarray) the counts in the first minus the counts in the second
    weighted by the relative livetimes
    """
    livetime_m = get_livetime(specEl_meas)
    counts_m = get_counts(specEl_meas)
    livetime_b = get_livetime(specEl_bkg)
    counts_b = get_counts(specEl_bkg)
    counts_s = counts_m - (counts_b)*(livetime_m/livetime_b)
    return counts_s

def insert_counts(specEl, counts):
    """Adds ChannelData element to Spectrum element with the given counts. Removes all previously existing
    ChannelData elements.
    :param specEl:
    :param counts:
    :return:
    """
    existing_counts = specEl.findall('ChannelData')
    for excounts in existing_counts:
        specEl.remove(excounts)
    countsEl = etree.Element('ChannelData')
    countstxt = ' '.join(f'{count:.0f}' for count in counts)
    countsEl.text = countstxt
    specEl.append(countsEl)

def get_container(ET, id=None, containername='RadMeasurement'):
    """
    Retrieves a RadMeasurement object from the ElementTree (or ET root) by id. id can be an int, picking that index
    from the list of RadMeasurements, or a string to compare to the "id" attribute of the RadMeasurement element.
    :param ET:
    :param id:
    :return:
    """
    if id is None: id=1
    Rf.requiredElement(containername,ET) #require that RadMeasurement exists
    rads = ET.findall(containername)
    return_rads = []
    for rad in rads:
        if isinstance(id, str) and id in rad.get('id',[]):
            return_rads.append(rad)
    if not return_rads:
        try:
            return rads[id-1]
        except TypeError: #id is probably a string
            raise Rf.BaseSpectraFormatException(f'Cannot find {containername} with id/index {id}')
    assert len(return_rads)==1
    return return_rads[0]

def calc_RASE_Sensitivity(counts,livetime,uSievertsph):
    """
    Derived from the documentation formula for calcuating RASE Sensitivity
    :param counts:
    :param livetime:
    :param uSievertsph:
    :return:
    """
    return (counts.sum()/livetime)/uSievertsph

def build_base_ET(ET_orig,radid=None,uSievertsph=None,subtraction_ET=None, subtraction_radid=None, containername='RadMeasurement', spectrum_id=None, subtraction_spectrum_id=None, transform=None):
    '''
    Old base building core that produces output N42s with all original content except an updated RadMeasurement.
    :param ET_orig:
    :param radid:
    :param uSievertsph:
    :param subtraction_ET:
    :param subtraction_radid:
    :param containername:
    :param spectrum_id:
    :param subtraction_spectrum_id:
    :return:
    '''
    ET = copy.deepcopy(ET_orig)
    Rf.strip_namespaces(ET)
    radElement = get_container(ET.getroot(), radid, containername)
    try:
        specElement = get_container(radElement, spectrum_id, 'Spectrum')
    except Rf.BaseSpectraFormatException:
        specElement = get_container(radElement, 1, 'Spectrum')
    counts = get_counts(specElement)
    if subtraction_ET:
        subtraction_ET_clone = copy.deepcopy(subtraction_ET)
        Rf.strip_namespaces(subtraction_ET_clone)
        radElement_b = get_container(subtraction_ET_clone.getroot(), subtraction_radid, containername)
        try:
            specElement_b = get_container(radElement_b, subtraction_spectrum_id, 'Spectrum')
        except Rf.BaseSpectraFormatException:
            specElement_b = get_container(radElement_b, 1, 'Spectrum')
        counts = subtract_spectra(specElement, specElement_b)

    existing_spectra = radElement.findall('Spectrum')
    for spectrum in existing_spectra: radElement.remove(spectrum)
    radElement.append(specElement)
    if (transform):
        counts = transform(counts)

    insert_counts(specElement, counts)
    livetime = get_livetime(specElement)
    if uSievertsph:
        Rsens = calc_RASE_Sensitivity(counts, livetime, uSievertsph)
    else:
        Rsens = 1.
    insert_RASE_Sensitivity(specElement, Rsens)
    ET.getroot().remove(radElement)
    ET.getroot().insert(0,radElement)

    return ET

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


def build_base_clean(ET_orig,radid=None,uSievertsph=None,subtraction_ET=None, subtraction_radid=None, containername='RadMeasurement', spectrum_id=None, subtraction_spectrum_id=None, transform=None):
    '''
    New base builind core that produces a "clean" N42 with only the RadMeasurement.
    :param ET_orig:
    :param radid:
    :param uSievertsph:
    :param subtraction_ET:
    :param subtraction_radid:
    :param containername:
    :param spectrum_id:
    :param subtraction_spectrum_id:
    :return:
    '''
    ET = copy.deepcopy(ET_orig)
    Rf.strip_namespaces(ET)
    radElement = get_container(ET.getroot(), radid, containername)
    try:
        specElement = get_container(radElement,spectrum_id,'Spectrum')
    except Rf.BaseSpectraFormatException:
        specElement = get_container(radElement,1,'Spectrum')
    counts = get_counts(specElement)
    if subtraction_ET:
        subtraction_ET_clone = copy.deepcopy(subtraction_ET)
        Rf.strip_namespaces(subtraction_ET_clone)
        radElement_b = get_container(subtraction_ET_clone.getroot(), subtraction_radid, containername)
        try:
            specElement_b = get_container(radElement_b, subtraction_spectrum_id, 'Spectrum')
        except Rf.BaseSpectraFormatException:
            specElement_b = get_container(radElement_b, 1, 'Spectrum')
        counts = subtract_spectra(specElement,specElement_b)

    existing_spectra = radElement.findall('Spectrum')
    for spectrum in existing_spectra: radElement.remove(spectrum)
    radElement.append(specElement)
    if(transform):
        counts = transform(counts)

    insert_counts(specElement,counts)
    livetime=get_livetime(specElement)
    if uSievertsph: Rsens=calc_RASE_Sensitivity(counts,livetime,uSievertsph)
    else: Rsens=1.
    insert_RASE_Sensitivity(specElement,Rsens)
    newroot = etree.Element(ET.getroot().tag)
    newtree = etree.ElementTree(newroot)
    newroot.insert(0,radElement)
    indent(newroot)
    return newtree

def list_spectra(ET):
    rads = ET.findall('RadMeasurement')
    rad_ids = []
    for rad in rads:
        rad_ids.append(rad.get('id','No id provided'))
    return rad_ids

def write_base_ET(ET,outputfolder,manufacturer,model,source, description=None):
    if len(manufacturer)!=4:  raise ValueError('Use 4-character manufacturer abbreviation')
    if len(model) != 3:       raise ValueError('Use 4-character model abbreviation')
    if(description is not None):
        outputname = f'V{manufacturer}_M{model}_{source}_{description}.n42'
    else:
        outputname = f'V{manufacturer}_M{model}_{source}.n42'
    outputpath = os.path.join(outputfolder,outputname)

    ET.write(outputpath)

def do_all(inputfile,radid,outputfolder,manufacturer,model,source,uSievertsph, subtraction,subtraction_radid, containername='RadMeasurement',spectrum_id=None,subtraction_spectrum_id=None,description=None, transform=None ):
    with open(inputfile,'r') as inputf:
        inputstr = inputf.read()
        inputstr = remove_control_characters(inputstr)
        ET_orig = etree.ElementTree(etree.fromstring(inputstr))
        try:
            with open(subtraction,'r') as subfile:
                substr = subfile.read()
                substr = remove_control_characters(substr)
                subtraction_ET = etree.ElementTree(etree.fromstring(substr))
        except TypeError:
            subtraction_ET = subtraction
        ET = build_base_clean(ET_orig,radid,uSievertsph,subtraction_ET,subtraction_radid,containername=containername,spectrum_id=spectrum_id,subtraction_spectrum_id=subtraction_spectrum_id, transform=transform)
        write_base_ET(ET,outputfolder,manufacturer,model,source,description)

        '''
        input 0-3MeV spectrum
        create x-y points using bin, as in congrid, but do it in integral space
        add extra x-y point at 8MeV with integral = previous max
        interpolate with 2^14 points 0-8MeV
        differentiate to go back to binned events space
        check bin centers and check trivial case
        '''