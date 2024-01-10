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

from typing import Union
from lxml import etree
from src import rase_functions as Rf
from src import spectrum_file_reading as reading
from src.rase_functions import get_ET_from_file
from src.utils import indent
import numpy
import os.path
from glob import glob
from mako.template import Template
from src.table_def import SecondarySpectrum

base_template = '''<?xml version="1.0"?>
<RadInstrumentData>
  <RadMeasurement id="Foreground">
    <MeasurementClassCode>Foreground</MeasurementClassCode>
    <RealTimeDuration>${realtime}</RealTimeDuration>
    <Spectrum>
      <LiveTimeDuration Unit="sec">${livetime}</LiveTimeDuration>
      <ChannelData>${spectrum}</ChannelData>
      ${RASE_sens} ${FLUX_sens}
    </Spectrum>
  </RadMeasurement>
  <EnergyCalibration>
    <CoefficientValues>${ecal}</CoefficientValues>
  </EnergyCalibration>
%for name, secondary in secondaries.items():
  <RadMeasurement id="${name}">
    <MeasurementClassCode>${secondary.classcode}</MeasurementClassCode>
    <RealTimeDuration>PT${secondary.realtime}S</RealTimeDuration>
    <Spectrum>
      <LiveTimeDuration Unit="sec">PT${secondary.livetime}S</LiveTimeDuration>
      <ChannelData>${secondary.get_counts_as_str()}</ChannelData>
    </Spectrum>
  </RadMeasurement>
%endfor
%for line in additional.splitlines():
  ${line}
%endfor${additional}
</RadInstrumentData>
'''

# Expected yaml fields:
# measurement_spectrum_xpath
# realtime_xpath
# livetime_xpath
# calibration
# subtraction_spectrum_xpath (optional)
# secondary_spectrum_xpath (optional)

pcf_config_txt = 'PCF File'
default_config = {
    'default n42':
        {
            'measurement_spectrum_xpath': './RadMeasurement[MeasurementClassCode="Foreground"]/Spectrum',
            'realtime_xpath': './RadMeasurement[MeasurementClassCode="Foreground"]/RealTimeDuration',
            'livetime_xpath': './RadMeasurement[MeasurementClassCode="Foreground"]/Spectrum/LiveTimeDuration',
            'calibration': './EnergyCalibration/CoefficientValues',
            'subtraction_spectrum_xpath': './RadMeasurement[@id="Foreground"]/Spectrum',
            'additionals': ['./RadMeasurement[MeasurementClassCode="Background"]',
                            './RadMeasurement[MeasurementClassCode="IntrinsicActivity"]'
                            ]
        },
    'rase n42':
        {
            'measurement_spectrum_xpath': './RadMeasurement[@id="Foreground"]/Spectrum',
            'realtime_xpath': './RadMeasurement[@id="Foreground"]/RealTimeDuration',
            'livetime_xpath': './RadMeasurement[@id="Foreground"]/Spectrum/LiveTimeDuration',
            'calibration': './EnergyCalibration/CoefficientValues',
            'subtraction_spectrum_xpath': './RadMeasurement[@id="Foreground"]/Spectrum',
            'additionals': ['./RadMeasurement[MeasurementClassCode="Background"]',
                            './RadMeasurement[MeasurementClassCode="IntrinsicActivity"]'
                            ]
        }
}

pcf_config = {
    pcf_config_txt:     # We will translate PCF files into n42s
        {
            'measurement_spectrum_xpath': './RadMeasurement/Spectrum',
            'realtime_xpath': './RadMeasurement/Spectrum/RealTimeDuration',
            'livetime_xpath': './RadMeasurement/Spectrum/LiveTimeDuration',
            'calibration': './EnergyCalibration/CoefficientValues',
            'subtraction_spectrum_xpath': './RadMeasurement/Spectrum',
        }
}


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
    chandataEl = reading.requiredElement('ChannelData', specEl)
    # print(etree.tostring(chandataEl, encoding='unicode', method='xml'))

    try:
        dataEl = reading.requiredElement('Data', chandataEl)
    except reading.BaseSpectraFormatException:
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
    timetext = reading.requiredElement(('LiveTimeDuration', 'LiveTime'), specEl).text
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
    if all(counts.astype(float) == counts.astype(int)):
    #TODO: Make a switch to decide whether int or float
        countstxt = ' '.join(f'{round(count)}' for count in [0 if c < 0 else c for c in counts])
    else:
        countstxt = ' '.join(f'{count:.4f}' for count in counts)
    countsEl.text = countstxt
    specEl.append(countsEl)


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

def sensitivity_text(counts, livetime, uSievertsph = None, fluxValue = None, ):
    # TODO: Make so that if the user puts nothing in dose or flux an error gets thrown
    RASE_sensitivity = ''
    FLUX_sensitivity = ''
    if uSievertsph:
        Rsens = calc_RASE_Sensitivity(counts, livetime, uSievertsph)
        RASE_sensitivity = f'<RASE_Sensitivity>{Rsens}</RASE_Sensitivity>'
    if fluxValue:
        Rsens = calc_RASE_Sensitivity(counts, livetime, fluxValue)
        FLUX_sensitivity = f'<FLUX_Sensitivity>{Rsens}</FLUX_Sensitivity>'
    if not (uSievertsph or fluxValue):
        Rsens = 1
        RASE_sensitivity = f'<RASE_Sensitivity>{Rsens}</RASE_Sensitivity>'
        FLUX_sensitivity = f'<FLUX_Sensitivity>{Rsens}</FLUX_Sensitivity>'
    return RASE_sensitivity, FLUX_sensitivity


def build_base_ET(ET, measureXPath, realtimeXPath, livetimeXPath,
                  subtraction_ET, subtractionXpath, calibration, additionals=[], secondaries_dict=None, uSievertsph=None, fluxValue=None, transform=None):

    specElements = ET.xpath(measureXPath)
    countslist = []
    livetimes = []
    realtimes = []
    for specElement in specElements:
        counts = get_counts(specElement)
        if subtraction_ET:
            specElement_b = subtraction_ET.xpath(subtractionXpath)[0]
            counts = subtract_spectra(specElement, specElement_b)
        if transform:
            counts = transform(counts)
        countslist.append(counts)

    sumcounts = numpy.array([0 if c < 0 else c for c in sum(countslist)])
    if all(sumcounts.astype(float) == sumcounts.astype(int)):
    #TODO: Make a switch to decide whether int or float
        countstxt = ' '.join(f'{round(count)}' for count in sumcounts)
    else:
        countstxt = ' '.join(f'{count:.4f}' for count in sumcounts)


    realtimes = ET.xpath(realtimeXPath)  # assumes realtime is a property of the radmeasurement
    livetimes = ET.xpath(livetimeXPath)
    livetime_sum_s = sum( [Rf.ConvertDurationToSeconds(livetime.text) for livetime in livetimes])
    realtime_sum_s = sum([Rf.ConvertDurationToSeconds(realtime.text) for realtime in realtimes])
    livetime_sum_txt = Rf.ConvertSecondsToIsoDuration(livetime_sum_s)
    realtime_sum_txt = Rf.ConvertSecondsToIsoDuration(realtime_sum_s)

    try:
        ecal = ET.xpath(calibration)[0].text
    except (TypeError, etree.XPathError):
        ecal = calibration
    except (IndexError):
        raise ValueError("Calibration XPath does not resolve to any element in input XML. "
                         "Please check base building config file and compare to the input XML.")

    RASE_sensitivity, FLUX_sensitivity = sensitivity_text(sumcounts,livetime_sum_s,uSievertsph,fluxValue)

    additional = ''
    if additionals:
        for addon in additionals:
            secondary_find = ET.xpath(addon)
            if secondary_find:
                secondary_el = ET.xpath(addon)[0]
                etree.indent(secondary_el)
                secondary_el.nsmap.clear()
                additional+=etree.tostring(secondary_el, encoding='unicode')
                additional+='\n'

    secondaries = {}
    if secondaries_dict:
        for key, value in secondaries_dict.items():
            sec = SecondarySpectrum(
                realtime = Rf.ConvertDurationToSeconds(ET.xpath(value['realtime'])[0].text),
                livetime = Rf.ConvertDurationToSeconds(ET.xpath(value['livetime'])[0].text),
                classcode = value['classcode']
            )
            spectrum_element = ET.xpath(value['spectrum'])[0]
            sec.counts = get_counts(spectrum_element)
            secondaries[key] = sec


    makotemplate = Template(text=base_template, input_encoding='utf-8')
    output = makotemplate.render(spectrum=countstxt, realtime=realtime_sum_txt, livetime=livetime_sum_txt,
                                 ecal=ecal, secondaries=secondaries,
                                 additional=additional, RASE_sens=RASE_sensitivity, FLUX_sens=FLUX_sensitivity)

    return output



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
    ET.write(outputpath, encoding="utf-8", method='xml', xml_declaration=True)


def write_base_text(text, outputfolder, outputfilename):
    outputpath = os.path.join(outputfolder, outputfilename)
    with open(outputpath, 'w', newline='') as f:
        f.write(text)




def do_all(inputfile, config:dict, outputfolder, manufacturer, model, source, subtraction,
           uSievertsph=None, fluxValue=None, description=None, transform=None):
    ET = get_ET_from_file(inputfile)
    try:
        subtraction_ET = get_ET_from_file(subtraction)
    except TypeError:
        subtraction_ET = subtraction


    output = build_base_ET(ET=ET, measureXPath=config['measurement_spectrum_xpath'], realtimeXPath=config['realtime_xpath'], livetimeXPath=config['livetime_xpath'],
                      subtraction_ET=subtraction_ET, subtractionXpath=config.get('subtraction_spectrum_xpath'),
                    calibration=config['calibration'], additionals=config.get('additionals'), secondaries_dict=config.get('secondaries'), uSievertsph=uSievertsph, fluxValue=fluxValue, transform=transform)
    outputfilename = base_output_filename(manufacturer, model, source, description)
    write_base_text(output, outputfolder, outputfilename)



def add_bases(ET:etree.ElementTree, ET2: Union[etree.ElementTree,None]):
    if ET2: #if ET2 is None, just return ET
        #add spectra, including livetimes
        spec1 = Rf.requiredElement('Spectrum',ET) #get first, which should be reliable since we have made these files in the right order
        spec2 = Rf.requiredElement('Spectrum',ET2) #get first, which should be reliable since we have made these files in the right order
        sum_counts = get_counts(spec1) + get_counts(spec2)
        sum_livetime = get_livetime(spec1) + get_livetime(spec2)
        insert_counts(spec1,sum_counts)
        Rf.requiredElement('LiveTimeDuration',spec1).text = f'PT{sum_livetime}S' #set livetime in units of seconds only.
        
        #add realtimes

        rt1 = Rf.requiredElement('RealTimeDuration',ET) #get first, which should be reliable since we have made these files in the right order
        rt2 = Rf.requiredElement('RealTimeDuration',ET2)
        sum_rt = Rf.ConvertDurationToSeconds(rt1.text)+Rf.ConvertDurationToSeconds(rt2.text)
        rt1.text = f'PT{sum_rt}S'
        indent(ET.getroot())

    return ET
    


def do_list(inputfiles, config:dict, outputfolder, manufacturer, model, source, subtraction,
           uSievertsph=None, fluxValue=None, description=None, transform=None):
    comboET=None
    try:
        subtraction_ET = get_ET_from_file(subtraction)
    except TypeError:
        subtraction_ET = subtraction
    for inputfile in inputfiles:
        ET_orig = get_ET_from_file(inputfile)
        ET = build_base_ET(ET=ET_orig, measureXPath=config['measurement_spectrum_xpath'], realtimeXPath=config['realtime_xpath'], livetimeXPath=config['livetime_xpath'],
                           subtraction_ET=subtraction_ET, subtractionXpath=config.get('subtraction_spectrum_xpath'), calibration=config['calibration'], additionals=config.get('additionals'), secondaries_dict=config.get('secondaries'), uSievertsph=uSievertsph, fluxValue=fluxValue, transform=transform)
        comboET = add_bases(etree.ElementTree(etree.fromstring(bytes(ET,encoding='utf-8'))), comboET)
    outputfilename = base_output_filename(manufacturer, model, source, description)
    write_base_ET(comboET, outputfolder, outputfilename)


def do_glob(inputfileglob, config:dict, outputfolder, manufacturer, model, source, subtraction,
           uSievertsph=None, fluxValue=None, description=None, transform=None):
    inputfiles = glob(inputfileglob)
    do_list(inputfiles, config, outputfolder, manufacturer, model, source, subtraction,
           uSievertsph, fluxValue, description, transform)


from .base_spectra_dialog import SharedObject
def validate_output(outputfolder, manufacturer, model, source, description=None):
    outputfilename = os.path.join(outputfolder,base_output_filename(manufacturer, model, source, description))
    sharedobj = SharedObject(True)
    tstatus=[]
    v = Rf.readSpectrumFile(filepath=outputfilename, sharedObject=sharedobj, tstatus=tstatus)
    if len(tstatus):
        raise Rf.BaseSpectraFormatException(tstatus)
    if not v:
        raise Rf.BaseSpectraFormatException("readSpectrumFile returned no output")