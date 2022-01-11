###############################################################################
# Copyright (c) 2018-2022 Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory
#
# Written by J. Brodsky, J. Chavez, S. Czyz, G. Kosinovsky, V. Mozin, S. Sangiorgio.
# RASE-support@llnl.gov.
#
# LLNL-CODE-819515, LLNL-CODE-829509
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

import xml.etree.ElementTree as etree
from src import rase_functions as Rf
import numpy
import copy
import os.path
import re


def remove_control_characters(xml):
    def str_to_int(s, default, base=10):
        if int(s, base) < 0x10000:
            return chr(int(s, base))
        return default

    xml = re.sub(r"&#(\d+);?", lambda c: str_to_int(c.group(1), c.group(0)), xml)
    xml = re.sub(r"&#[xX]([0-9a-fA-F]+);?", lambda c: str_to_int(c.group(1), c.group(0), base=16), xml)
    xml = re.sub(r"[\x00-\x08\x0b\x0e-\x1f\x7f]", "", xml)
    return xml


def insert_Sensitivity(specElement, Rsens, flag):
    """ Adds RASE Sensitivity to a Spectrum element
    :param specElement:
    :param Rsens:
    :return:
    """
    existing_rsens = specElement.findall(flag)
    for rsens in existing_rsens:
        specElement.remove(rsens)
    RsensElement = etree.Element(flag)
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
    return numpy.fromiter(uncompressedCounts, float)


def get_counts(specEl):
    """Retrieve counts as a numpy ndarray from the first ChannelData element in the given Spectrum element
    Calls Uncompress method if the ChannelData element has an attribute containing
    "compression" equal to "CountedZeroes".
    """
    chandataEl = Rf.requiredElement('ChannelData', specEl)
    # print(etree.tostring(chandataEl, encoding='unicode', method='xml'))

    try:
        dataEl = Rf.requiredElement('Data', chandataEl)
    except Rf.BaseSpectraFormatException:
        dataEl = chandataEl

    counts = numpy.fromstring(dataEl.text, float, sep=' ')
    for attribute, value in dataEl.attrib.items():
        if 'COMPRESSION' in attribute.upper() and value == 'CountedZeroes':
            return uncompressCountedZeroes(counts)
    else:
        return counts


def get_livetime(specEl):
    """Retrieves Livetime as a float from the Spectrum element
    """
    timetext = Rf.requiredElement(('LiveTimeDuration', 'LiveTime'), specEl).text
    return Rf.ConvertDurationToSeconds(timetext)


def subtract_spectra(specEl_meas, specEl_bkg):
    """Given two Spectrum elements, returns (as an ndarray) the counts in the first minus the counts in the second
    weighted by the relative livetimes. Negative values are set to zero.
    """
    # FIXME: should allow correction for different effects of dead times between the two spectra
    livetime_m = get_livetime(specEl_meas)
    counts_m = get_counts(specEl_meas)
    livetime_b = get_livetime(specEl_bkg)
    counts_b = get_counts(specEl_bkg)
    counts_s = counts_m - (counts_b) * (livetime_m / livetime_b)
    counts_s[counts_s < 0] = 0
    return counts_s


def insert_counts(specEl, counts):
    """Adds ChannelData element to Spectrum element with the given counts. Removes all previously existing
    ChannelData elements.
    :param specEl:
    :param counts:
    :return:
    """
    for parent in specEl.findall('.//ChannelData/..'):
        for element in parent.findall('ChannelData'):
            parent.remove(element)
    countsEl = etree.Element('ChannelData')
    countstxt = ' '.join(f'{count:.4f}' for count in counts)
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
    if id is None: id = 1
    Rf.requiredElement(containername, ET)  # require that RadMeasurement exists
    rads = ET.findall(f".//{containername}")
    return_rads = []
    for rad in rads:
        if isinstance(id, str) and id in rad.get('id', []):
            return_rads.append(rad)
    if not return_rads:
        try:
            return rads[id - 1]
        except TypeError:  # id is probably a string
            raise Rf.BaseSpectraFormatException(f'Cannot find {containername} with id/index {id}')
    assert len(return_rads) == 1
    return return_rads[0]


def calc_RASE_Sensitivity(counts, livetime, source_act_fact):
    """
    Derived from the documentation formula for calcuating RASE Sensitivity.
    For dose, source_act_fact is microsieverts/hour
    For flux, source_act_fact is counts*cm^-2*s-1 in the photopeak of interest
    :param counts:
    :param livetime:
    :param uSievertsph:
    :return:
    """
    return (counts.sum() / livetime) / source_act_fact


def build_base_ET(ET_orig, radid=None, uSievertsph=None, fluxValue=None, subtraction_ET=None, subtraction_radid=None,
                  containername='RadMeasurement', spectrum_id=None, subtraction_spectrum_id=None, transform=None):
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
    parent_map = {c: p for p in ET.iter() for c in p}
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

    for parent in radElement.findall('.//Spectrum/..'):
        for element in parent.findall('Spectrum'):
            parent.remove(element)
    radElement.append(specElement)
    if (transform):
        counts = transform(counts)
    insert_counts(specElement, counts)
    livetime = get_livetime(specElement)
    if uSievertsph:
        Rsens = calc_RASE_Sensitivity(counts, livetime, uSievertsph)
        insert_Sensitivity(specElement, Rsens, 'RASE_Sensitivity')
    if fluxValue:
        Rsens = calc_RASE_Sensitivity(counts, livetime, fluxValue)
        insert_Sensitivity(specElement, Rsens, 'FLUX_Sensitivity')
    if not (uSievertsph or fluxValue):
        Rsens = 1
        insert_Sensitivity(specElement, Rsens, 'RASE_Sensitivity')
    parent = parent_map[radElement]
    parent.remove(radElement)
    parent.insert(0, radElement)
    indent(ET.getroot())

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


def build_base_clean(ET_orig, radid=None, uSievertsph=None, fluxValue=None, subtraction_ET=None, subtraction_radid=None,
                     containername='RadMeasurement', spectrum_id=None, subtraction_spectrum_id=None, transform=None):
    '''
    New base building core that produces a "clean" N42 with only the RadMeasurement.
    :param ET_orig:
    :param radid:
    :param uSievertsph:
    :param fluxValue:
    :param subtraction_ET:
    :param subtraction_radid:
    :param containername:
    :param spectrum_id:
    :param subtraction_spectrum_id:
    :return:
    '''
    # FIXME: The secondary spectrum is not propagated to the new base spectrum
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

    for parent in radElement.findall('.//Spectrum/..'):
        for element in parent.findall('Spectrum'):
            parent.remove(element)
    if transform:
        counts = transform(counts)

    newroot = etree.Element(ET.getroot().tag)
    newroot.insert(0, radElement)
    radElement.insert(0, specElement)
    livetime = get_livetime(specElement)
    insert_counts(specElement, counts)
    # TODO: Make so that if the user puts nothing in dose or flux an error gets thrown
    if uSievertsph:
        Rsens = calc_RASE_Sensitivity(counts, livetime, uSievertsph)
        insert_Sensitivity(specElement, Rsens, 'RASE_Sensitivity')
    if fluxValue:
        Rsens = calc_RASE_Sensitivity(counts, livetime, fluxValue)
        insert_Sensitivity(specElement, Rsens, 'FLUX_Sensitivity')
    if not (uSievertsph or fluxValue):
        Rsens = 1
        insert_Sensitivity(specElement, Rsens, 'RASE_Sensitivity')
        insert_Sensitivity(specElement, Rsens, 'FLUX_Sensitivity')

    indent(newroot)

    return etree.ElementTree(newroot)


def list_spectra(ET):
    rads = ET.findall('.//RadMeasurement')
    rad_ids = []
    for rad in rads:
        rad_ids.append(rad.get('id', 'No id provided'))
    return rad_ids


def base_output_filename(manufacturer, model, source, description=None):
    # if len(manufacturer) >=5:  raise ValueError('Use 4-character manufacturer abbreviation')
    # if len(model) >= 5:        raise ValueError('Use 4-character model abbreviation')
    if description:
        outputname = f'V{manufacturer}_M{model}_{source}_{description}.n42'
    else:
        outputname = f'V{manufacturer}_M{model}_{source}.n42'
    return outputname


def write_base_ET(ET, outputfolder, outputfilename):
    outputpath = os.path.join(outputfolder, outputfilename)
    ET.write(outputpath, encoding="unicode", method='xml', xml_declaration=True)


def get_ET_from_file(inputfile):
    with open(inputfile, 'r') as inputf:
        inputstr = inputf.read()
        inputstr = remove_control_characters(inputstr)
        return etree.ElementTree(etree.fromstring(inputstr))


def do_all(inputfile, radid, outputfolder, manufacturer, model, source, uSievertsph, fluxValue, subtraction,
           subtraction_radid,
           containername='RadMeasurement', spectrum_id=None, subtraction_spectrum_id=None, description=None,
           transform=None):
    ET_orig = get_ET_from_file(inputfile)
    try:
        subtraction_ET = get_ET_from_file(subtraction)
    except TypeError:
        subtraction_ET = subtraction
    ET = build_base_ET(ET_orig, radid, uSievertsph, fluxValue, subtraction_ET, subtraction_radid,
                       containername=containername, spectrum_id=spectrum_id,
                       subtraction_spectrum_id=subtraction_spectrum_id, transform=transform)
    outputfilename = base_output_filename(manufacturer, model, source, description)
    write_base_ET(ET, outputfolder, outputfilename)

    '''
    input 0-3MeV spectrum
    create x-y points using bin, as in congrid, but do it in integral space
    add extra x-y point at 8MeV with integral = previous max
    interpolate with 2^14 points 0-8MeV
    differentiate to go back to binned events space
    check bin centers and check trivial case
    '''
