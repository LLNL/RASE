###############################################################################
# Copyright (c) 2018-2022 Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory
#
# Written by J. Brodsky, J. Chavez, S. Czyz, G. Kosinovsky, V. Mozin, S. Sangiorgio.
# RASE-support@llnl.gov.
#
# LLNL-CODE-841943, LLNL-CODE-829509
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
"""
This module defines key functions used in RASE
"""

import glob
import io
import logging
import ntpath
import os
import re
import shutil
import sys
from lxml import etree
from pathlib import Path
import isodate, datetime
import numpy as np
from mako import exceptions
from sqlalchemy.engine import create_engine, Engine
from sqlalchemy import event

from src.scenarios_io import ScenariosIO
from src.table_def import BaseSpectrum, BackgroundSpectrum, Detector, Scenario, SampleSpectraSeed, \
    Session, Base, DetectorInfluence, ScenarioMaterial, ScenarioBackgroundMaterial, Material
from src.utils import compress_counts, indent
# Key variables used in several places
secondary_type = {'internal': 2, 'base_spec': 0, 'scenario': 1, 'file': 3}



def initializeDatabase(databaseFilepath):
    """
    binds Session to database and creates new database if none exists

    :param databaseFilepath: path to src.sqlite file
    """
    Session.remove()
    engine = create_engine('sqlite:///' + databaseFilepath)
    Session.configure(bind=engine)
    if not os.path.exists(databaseFilepath):
        Base.metadata.create_all(engine)
        return False
    return True


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

def importDistortionFile(filepath):
    """
    Import Influences from distorsion (.dis) xml file formatted as in old RASE
    :param filepath: path of valid influence file
    :return: array of influence names and corresponding distorsion values
    """
    root = etree.parse(filepath).getroot()
    detInfluences = []
    for inflElement in root:
        inflName = inflElement.tag
        inflVals = [float(value) for value in inflElement.find('Nonlinearity').text.split()]
        detInfluences.append((inflName, inflVals))
    return detInfluences


def ConvertDurationToSeconds(inTime):
    """
    converts text string to seconds
    :param inTime: text string in ISO format ("PTxxx")
    :return: duration in seconds
    """
    outTime = isodate.parse_duration(inTime)
    return outTime.total_seconds()

def ConvertSecondsToIsoDuration(inseconds):
    """
    converts seconds to text string
    :param inseconds: seconds
    :return: ISO "PT" textstring
    """
    dt = datetime.timedelta(seconds=inseconds)
    return isodate.duration_isoformat(dt)

class ResultsFileFormatException(Exception):
    pass


def readTranslatedResultFile(filename, use_confs):
    """
    Reads translated results file from either of two formats:

    Format 1:
    //IdentificationResults
		/Isotopes (single)
			/text(): \n-separated list of identification labels
		/ConfidenceIndex (single)
			/text(): \n-separated list of confidence indices

	Format 2:
	//IdentificationResults
	    /Identification (multiple)
    	    /IDName
	            /text(): nuclide label
	        /IDConfidence
	            /text(): confidence level


    :param filename: path of valid results file
    :return: list of identification results
    """
    root = etree.parse(str(filename)).getroot()
    if root.tag != "IdentificationResults":
        raise ResultsFileFormatException(f'{filename}: bad file format')

    # Read format 1
    if len(root.findall('Isotopes')) > 0:
       isotopes = root.find('Isotopes').text
       if isotopes:
            results = list(filter(lambda x: x.strip() not in ['-', ''], isotopes.split('\n')))
            if root.find('ConfidenceIndex') is not None:
                confidences = root.find('ConfidenceIndex').text
            elif root.find('Confidences') is not None:
                confidences = root.find('Confidences').text
            else:
                confidences = None
            if use_confs and confidences is not None:
                confidences = list(filter(lambda x: x.strip() not in ['-', ''], confidences.split('\n')))
                # for some instruments (e.g.: RadEagle), the confidences are zeros while the isotopes are dashes
                if len(confidences) > len(results):
                    confidences = confidences[0:len(results)]
                if confidences:
                    try:
                        # 0 - 3 = low, 4 - 6 = medium, 7 - 10 = high
                        confidences = [(int(float(c)/3.4) + 1) / 3 for c in confidences]
                    except:
                        raw_confidences = confidences
                        confidences = []
                        for c in raw_confidences:
                            if c == 'low':
                                confidences.append(1/3)
                            elif c == 'medium':
                                confidences.append(2/3)
                            else:
                                confidences.append(1)  # default to full confidence in results
            else:
                confidences = [1] * len(results)
            return results, confidences
       else:
            return [], []
    # Read Format 2
    elif len(root.findall('Identification')) > 0:
        results = []
        confidences = []
        for identification in root.findall('Identification'):
            idname = identification.find('IDName')
            if idname.text:
                results.append(idname.text.strip())
                confidence = identification.find('IDConfidence')
            else:
                confidence = None
            if use_confs and confidence is not None:
                try:
                    # 0 - 3 = low, 4 - 6 = medium, 7 - 10 = high
                    confidences.append((int(float(confidence.text.strip()) / 3.4) + 1) / 3)
                except:
                    if confidence.text.strip() == 'low':
                        confidences.append(1 / 3)
                    elif confidence.text.strip() == 'medium':
                        confidences.append(2 / 3)
                    else:
                        confidences.append(1)  # default to full confidence in results
            else:
                confidences = [1] * len(results)

        return results, confidences
    else:
        raise ResultsFileFormatException(f'{filename}: bad file format')


class BaseSpectraFormatException(Exception):
    pass

def requiredElement(element, source, extratext=''):
    if isinstance(element, str):
        el = source.find(f".//{element}")
    else:
        for thiselement in element:
            el = source.find(f".//{thiselement}")
            if el is not None: return el
    if extratext: extratext = f'({extratext})'
    if el is None:
        raise BaseSpectraFormatException(f'No {element} in element {source.tag} {extratext}')
    return el

def requiredSensitivity(element, source):
    """
    Checks to see if RASE_Sensitvity and FLUX_Sensitivity terms are in a loaded spectrum.
    If not, return None for that specific sensitivity value. If it is None, that spectrum
    will not appear in the list of base spectra for that detector when creating a scenario,
    and it will show as red in the scenario list
    """
    if isinstance(element[0], str):
        el = [source.find(f".//{element[0]}")]
    else:
        el = [None]
    if isinstance(element[1], str):
        el.append(source.find(f".//{element[1]}"))
    else:
        el.append(None)
    if el == [None, None]:
        raise BaseSpectraFormatException(f'No {element[0]} or {element[1]} in element {source.tag}')
    return el

def parseRadMeasurement(root, filepath, sharedObject, tstatus, requireRASESens):
    try:
        radElement = requiredElement('RadMeasurement', root, )
        allRad = root.findall("RadMeasurement")
        if len(allRad) == 2:
            sharedObject.bkgndSpectrumInFile = True
            radElementBckg = allRad[1]
        elif len(allRad) > 2:
            raise BaseSpectraFormatException(f'Too many RadMeasurement elements, expected 1 or 2')
        specElement = requiredElement('Spectrum', radElement)
        chanData = requiredElement('ChannelData', specElement)
        countsChar = chanData.text.strip("'").strip().split()
        if len(countsChar) < 2:
            countsChar = chanData.text.strip("'").strip().split(',')
        counts = [float(count) for count in countsChar]
        if not counts: raise BaseSpectraFormatException('Could not parse ChannelData')
        if ("." in countsChar[0]):
            sharedObject.chanDataType = "float"
        else:
            sharedObject.chanDataType = "int"
        counts = ','.join(map(str, counts))
        chanDataBckg = None
        countsBckg = None
        if sharedObject.isBckgrndSave and sharedObject.bkgndSpectrumInFile:
            specElementBckg = requiredElement('Spectrum',radElementBckg,'secondary spectrum')
            chanDataBckg = requiredElement('ChannelData', specElementBckg, 'secondary spectrum')
            countsChar = chanDataBckg.text.strip("'").strip().split()
            countsBckg = [float(count) for count in countsChar]
            if not counts: raise BaseSpectraFormatException('Could not parse ChannelData in secondary spectrum')
            countsBckg = ','.join(map(str, countsBckg))
        realtimeBckg = None
        livetimeBckg = None
        ecalBckg = None
        rase_sensitivity = None
        flux_sensitivity = None
        calibration = requiredElement('EnergyCalibration',root)
        calElement = requiredElement('CoefficientValues',calibration)
        ecal = [float(value) for value in calElement.text.split()]
        realtimeElement = requiredElement(('RealTime','RealTimeDuration'),radElement)
        realtime = getSeconds(realtimeElement.text.strip())
        livetimeElement = requiredElement(('LiveTimeDuration','LiveTime'),specElement)
        livetime = getSeconds(livetimeElement.text.strip())
        if requireRASESens:
            RASEsensElement = requiredSensitivity(('RASE_Sensitivity', 'FLUX_Sensitivity'), specElement)
        else:
            RASEsensElement = specElement.find('Calibration')    # TODO: is this a problem for flux mode?
        if RASEsensElement is not None:
            if RASEsensElement[0] is None:
                rase_sensitivity = 'NaN'
            else:
                rase_sensitivity = float(RASEsensElement[0].text.strip())
            if RASEsensElement[1] is None:
                flux_sensitivity = 'NaN'
            else:
                flux_sensitivity = float(RASEsensElement[1].text.strip())
        if chanDataBckg is not None:
            ecalBckg = ecal
            realtimeElementBckg = requiredElement(('RealTime','RealTimeDuration'),radElementBckg,'secondary spectrum')
            realtimeBckg = getSeconds(realtimeElementBckg.text.strip())
            livetimeElementBckg = requiredElement(('LiveTimeDuration','LiveTime'), specElementBckg, 'secondary spectrum')
            livetimeBckg = getSeconds(livetimeElementBckg.text.strip())
        return counts, ecal, realtime, livetime, rase_sensitivity, flux_sensitivity, countsBckg, ecalBckg, \
               realtimeBckg, livetimeBckg
    except BaseSpectraFormatException as ex:
        message = f"{str(ex)} in file {ntpath.basename(filepath)}"
        tstatus.append(message)
        return None

def parseMeasurement(measurement, filepath, sharedObject, tstatus, requireRASESen=True):
    try:
        specElement = requiredElement('Spectrum', measurement)
        allSpectra = measurement.findall("Spectrum")
        if len(allSpectra) == 2:
            sharedObject.bkgndSpectrumInFile = True
            specElementBckg = allSpectra[1]
        elif len(allSpectra) > 2:
            raise BaseSpectraFormatException(f'Too many Spectrum elements, expected 1 or 2')

        chanData = requiredElement('ChannelData', specElement)
        countsChar = chanData.text.strip("'").strip().split()
        if len(countsChar) < 2:
            countsChar = chanData.text.strip("'").strip().split(',')
        if ("." in countsChar[0]):
            sharedObject.chanDataType = "float"
        else:
            sharedObject.chanDataType = "int"
        counts = [float(count) for count in countsChar]
        if not counts: raise BaseSpectraFormatException('Could not parse ChannelData')
        chanDataBckg = None
        countsBckg = None
        if sharedObject.isBckgrndSave and sharedObject.bkgndSpectrumInFile:
            chanDataBckg = requiredElement('ChannelData', specElementBckg, 'secondary spectrum')
            countsChar = chanDataBckg.text.strip("'").strip().split()
            countsBckg = [float(count) for count in countsChar]
            if not countsBckg: raise BaseSpectraFormatException('Could not parse ChannelData (secondary spectrum)')
        # uncompress if needed
        counts = uncompressCountedZeroes(chanData,counts)
        if chanDataBckg is not None:
            countsBckg = uncompressCountedZeroes(chanDataBckg,countsBckg)

        realtimeBckg = None
        livetimeBckg = None
        ecalBckg = None
        calibration = specElement.find('Calibration')
        if calibration is None:
            calibration = requiredElement('Calibration', root, 'or in Spectrum element')

        calElement = requiredElement('Coefficients',requiredElement('Equation',calibration))
        ecal = [float(value) for value in calElement.text.split()]
        realtimeElement = requiredElement(('RealTime','RealTimeDuration'),specElement)
        realtime = getSeconds(realtimeElement.text.strip())
        livetimeElement = requiredElement(('LiveTimeDuration','LiveTime'), specElement)
        livetime = getSeconds(livetimeElement.text.strip())
        if requireRASESen:
            RASEsensElement = requiredSensitivity(('RASE_Sensitivity', 'FLUX_Sensitivity'), specElement)
            if RASEsensElement[0] is None:
                rase_sensitivity = 'NaN'
            else:
                rase_sensitivity = float(RASEsensElement[0].text.strip())
            if RASEsensElement[1] is None:
                flux_sensitivity = 'NaN'
            else:
                flux_sensitivity = float(RASEsensElement[1].text.strip())
        else:
            rase_sensitivity = flux_sensitivity = 'NaN'

        if chanDataBckg is not None:
            ecalBckg = []
            calibrationBckg = specElementBckg.find('Calibration')
            if calibrationBckg is not None:
                calElement = requiredElement('Coefficients', requiredElement('Equation', calibrationBckg))
                ecalBckg = [float(value) for value in calElement.text.split()]
            else:
                message = "no Background Calibration in file " + ntpath.basename(filepath)
                tstatus.append(message)
            realtimeElementBckg = requiredElement(('RealTime','RealTimeDuration'), specElementBckg, 'secondary spectrum')
            realtimeBckg = getSeconds(realtimeElementBckg.text.strip())
            livetimeElementBckg = requiredElement(('LiveTimeDuration','LiveTime'), specElementBckg, 'secondary spectrum')
            livetimeBckg = getSeconds(livetimeElementBckg.text.strip())

        return counts, ecal, realtime, livetime, rase_sensitivity, flux_sensitivity, \
                    countsBckg, ecalBckg, realtimeBckg, livetimeBckg

    except BaseSpectraFormatException as ex:
        message = f"{str(ex)} in file {ntpath.basename(filepath)}"
        tstatus.append(message)
        return None


def uncompressCountedZeroes(chanData,counts):
    if (chanData.attrib.get('Compression') == 'CountedZeroes') or (
            chanData.attrib.get('compressionCode') == 'CountedZeroes'):
        uncompressedCounts = []
        countsIter = iter(counts)
        for count in countsIter:
            if count == float(0):
                uncompressedCounts.extend([0] * int(next(countsIter)))
            else:
                uncompressedCounts.append(count)
        counts = ','.join(map(str, uncompressedCounts))
    else:
        counts = ','.join(map(str, counts))
    return counts

def strip_namespaces(tree:etree.ElementTree):
    # xpath query for selecting all element nodes in namespace
    tree.getroot()
    query = "descendant-or-self::*[namespace-uri()!='']"
    # for each element returned by the above xpath query...
    for element in tree.xpath(query):
        # replace element name with its local name
        element.tag = etree.QName(element).localname
    tree.getroot().attrib.clear()
    etree.cleanup_namespaces(tree)
    return tree

def remove_control_characters(xml):
    def str_to_int(s, default, base=10):
        if int(s, base) < 0x10000:
            return chr(int(s, base))
        return default

    xml = re.sub(r"&#(\d+);?", lambda c: str_to_int(c.group(1), c.group(0)), xml)
    xml = re.sub(r"&#[xX]([0-9a-fA-F]+);?", lambda c: str_to_int(c.group(1), c.group(0), base=16), xml)
    xml = re.sub(r"[\x00-\x08\x0b\x0e-\x1f\x7f]", "", xml)
    return xml

def get_ET_from_file(inputfile):
    with open(inputfile, 'r') as inputf:
        inputstr = inputf.read()
        inputstr = remove_control_characters(inputstr)
        inputstr_io = io.BytesIO(bytes(inputstr,encoding='utf-8'))
        parser = etree.XMLParser(recover=True)
        et =  etree.parse(inputstr_io,parser)
        # et = copy.deepcopy((et_orig))
        strip_namespaces(et)
        return et

def readSpectrumFile(filepath, sharedObject, tstatus, requireRASESen=True):
    """
    Reads in the Spectrum File
    :param filepath: path to spectrum file
    :param sharedObject: contains fields that are set during parsing of the file
    :param tstatus: information string that is augmented during parcing of the file
    :return: counts, ecal, realtime, livetime, sensitivity, countsBckg, ecalBckg, realtimeBckg, livetimeBckg
    """
    try:
        specElement = None
        specElementBckg = None
        # First strip all namespaces if any
        # TODO: make this a general utility method as it can be useful elsewhere

        root = get_ET_from_file(filepath).getroot()
        # Now extract the relevant details from the file
        measurement = root.find('Measurement')
        rad_measurement = root.find('RadMeasurement')
        if measurement is not None:
            return parseMeasurement(measurement, filepath, sharedObject, tstatus, requireRASESen)
        elif rad_measurement is not None:
            return parseRadMeasurement(root, filepath, sharedObject, tstatus, requireRASESen)
    except BaseSpectraFormatException as ex:
        message = f"{str(ex)} in file {ntpath.basename(filepath)}"
        tstatus.append(message)
        return None
    except :
        print(sys.exc_info())
    #except : return None

def getSeconds(text):
    """
    translates file time format into seconds
    :param text: input time format
    :return: seconds as string
    """
    text = text.lower().strip('pts')
    seconds = 0
    if not text == "" and 'h' in text:
        hours, text = text.split('h')
        seconds += int(hours) * 3600
    if not text == "" and 'm' in text:
        minutes, text = text.split('m')
        seconds +=  int(minutes) * 60
    if not text == "":
        seconds += float(text)
    return seconds


def rebin(counts, oldEnergies, newEcal):
    """
    Rebins a list ouf counts to a new energy calibration.

    :param counts:      numpy array ouf counts indexed by channel
    :param oldEnergies: numpy array of energies indexed by channel
    :param newEcal:     list of new energy polynomial coefficents to rebin to: [E3 E2 E1 E0]
    :return:            numpy array of rebinned counts
    """
    newEnergies = np.polyval(newEcal, np.arange(len(counts)+1))
    newCounts   = np.zeros(len(counts))

    # move old energies index to first value greater than the first value in newEnergies
    oe = 0 # will always lead ne in energy boundary value
    while oe < len(oldEnergies) and oldEnergies[oe] <= newEnergies[0]: oe += 1
    ne0 = 0
    while newEnergies[ne0] <= oldEnergies[oe]:
        ne0 += 1

    # loop through and distribute old counts into new bins
    for ne in range(ne0, len(newCounts)):
        if oe == len(oldEnergies): break  # have already distributed all old counts

        # if no old energy boundaries within this new bin, new bin is fraction of old bin
        if oldEnergies[oe] > newEnergies[ne + 1]:
            newCounts[ne] = counts[oe - 1] * (newEnergies[ne + 1] - newEnergies[ne]) \
                            / (oldEnergies[oe] - oldEnergies[oe - 1])

        # else there are old energy boundaries in this new bin: add each portion of old bins
        else:
            # Step 1: add first partial(or full) old bin
            # TODO: This will crash if (oldEnergies[oe] - oldEnergies[oe-1]) < 0; might be necessary to handle this?
            newCounts[ne] = counts[oe-1] * (oldEnergies[oe] - newEnergies[ne]) \
                            / (oldEnergies[oe] - oldEnergies[oe-1])
            oe += 1

            # Step 2: add middle full old bins
            while oe < len(oldEnergies) and oldEnergies[oe] <= newEnergies[ne+1]:
                newCounts[ne] += counts[oe-1]
                oe += 1
            if oe == len(oldEnergies): break

            # Step 3: add last partial old bin
            newCounts[ne] += counts[oe-1] * (newEnergies[ne+1] - oldEnergies[oe-1]) \
                             / (oldEnergies[oe] - oldEnergies[oe-1])
    return newCounts


def _getCountsDoseAndSensitivity(scenario, detector, degradations=None):
    """

    :param scenario:
    :param detector:
    :return:
    """
    session = Session()

    # distortion:  distort ecal with influence factors
    ecal = [detector.ecal3, detector.ecal2, detector.ecal1, detector.ecal0]
    #get ecal: either the only ecal in the list of sources, or the preferred ecal of the detector if the sources differ
    scenMaterialnames =  [m.material_name for m in scenario.scen_materials + scenario.scen_bckg_materials]
    baseSpectra = session.query(BaseSpectrum).filter(BaseSpectrum.detector_name == detector.name,
                                                     BaseSpectrum.material_name.in_(scenMaterialnames)).all()

    ecals = [bs.ecal for bs in baseSpectra]
    all_same_ecal = all(np.array_equal(ecals[0], other) for other in ecals)

    if all_same_ecal:
        ecal = ecals[0]
    else:
        ecal = detector.ecal


    new_influences, bin_widths, energies = calculate_influence(scenario,detector,degradations,ecal)


    # get dose, counts and sensitivity for each material
    countsDoseAndSensitivity = []
    for scenMaterial in scenario.scen_materials + scenario.scen_bckg_materials:
        baseSpectrum = (session.query(BaseSpectrum)
                        .filter_by(detector_name=detector.name,
                                   material_name=scenMaterial.material_name)
                        ).first()
        counts = baseSpectrum.counts
        if not (np.array_equal(ecal, baseSpectrum.ecal)):
            oldenergies = np.polyval(baseSpectrum.ecal, np.arange(detector.chan_count))
            counts = rebin(counts, oldenergies, ecal)

        if scenario.influences:
            for index, infl in enumerate(new_influences):
                counts = apply_distortions(infl, counts, bin_widths[index], energies, ecal)

        if scenMaterial.fd_mode == 'FLUX':
            countsDoseAndSensitivity.append((counts, scenMaterial.dose, baseSpectrum.flux_sensitivity))
        else:
            countsDoseAndSensitivity.append((counts, scenMaterial.dose, baseSpectrum.rase_sensitivity))

    # if the detector has an internal calibration source, it needs to be added with special treatment
    if detector.includeSecondarySpectrum and detector.secondary_type == secondary_type['internal']:

        secondary_spectrum = (session.query(BackgroundSpectrum).filter_by(detector_name=detector.name)).first()
        counts = secondary_spectrum.get_counts_as_np()

        # apply distortion on counts
        if scenario.influences:
            for index, infl in enumerate(new_influences):
                counts = apply_distortions(infl, counts, bin_widths[index], energies, ecal)

        # extract counts per second
        cps = sum(counts)/secondary_spectrum.livetime

        # the internal calibration spectrum is scaled only by time
        # so the sensitivity parameter is set to the cps and the dose to 1
        countsDoseAndSensitivity.append((counts, 1.0, cps))

    return countsDoseAndSensitivity


def create_n42_file(filename, scenario, detector, sample_counts, secondary_spectrum=None):
    """
    Creates n42 file from input
    :param filename: path of resultant n42 file
    :param scenario: scenario info
    :param detector: detector info
    :param sample_counts: sample counts array
    :param secondary_spectrum: optional secondary spectrum array
    """
    # FIXME: should use ElementTree instead of manually creating the XML text
    f = open(filename, 'w')
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    f.write('<N42InstrumentData>\n')
    f.write('  <Measurement>\n')
    f.write('    <Spectrum>\n')
    f.write('      <SourceType>Item</SourceType>\n')
    f.write('      <RealTime Unit="sec">PT{}S</RealTime>\n'.format(scenario.acq_time))
    f.write('      <LiveTime Unit="sec">PT{}S</LiveTime>\n'.format(scenario.acq_time))
    f.write('      <Calibration Type="Energy" EnergyUnits="keV">\n')
    f.write('        <Equation Model="Polynomial">\n')
    f.write('          <Coefficients>{} {} {} {}</Coefficients>\n'.format(detector.ecal0, detector.ecal1, detector.ecal2, detector.ecal3))
    f.write('        </Equation>\n')
    f.write('      </Calibration>\n')
    f.write('      <ChannelData>')
    f.write('{}'.format(' '.join('{:f}'.format(x) for x in sample_counts)))
    f.write('</ChannelData>\n')
    f.write('    </Spectrum>\n')
    if secondary_spectrum:
        f.write('    <Spectrum>\n')
        type_str = 'Calibration' if detector.secondary_type == secondary_type['internal'] else 'Background'
        f.write(f'      <SourceType>{type_str}</SourceType>\n')
        f.write('      <RealTime Unit="sec">PT{}S</RealTime>\n'.format(secondary_spectrum.realtime))
        f.write('      <LiveTime Unit="sec">PT{}S</LiveTime>\n'.format(secondary_spectrum.livetime))
        f.write('      <Calibration Type="Energy" EnergyUnits="keV">\n')
        f.write('        <Equation Model="Polynomial">\n')
        f.write('          <Coefficients>{} {} {} {}</Coefficients>\n'.format(detector.ecal0, detector.ecal1,
                                                                              detector.ecal2, detector.ecal3))
        f.write('        </Equation>\n')
        f.write('      </Calibration>\n')
        f.write('      <ChannelData>')
        f.write(secondary_spectrum.get_counts_as_str())

        f.write('</ChannelData>\n')
        f.write('    </Spectrum>\n')
    f.write('  </Measurement>\n')
    f.write('</N42InstrumentData>\n')
    f.close()


def create_n42_file_from_template(n42_mako_template, filename, scenario, detector, sample_counts : np.ndarray, secondary_spectrum=None):
    """
    Creates n42 file from input using teplate
    :param n42_mako_template: template used to make file
    :param filename: path of resultant n42 file
    :param scenario: scenario info
    :param detector: detector info
    :param sample_counts: sample counts array
    :param secondary_spectrum: optional secondary spectrum array
    """
    template_data = dict(
        scenario=scenario,
        detector=detector,
        # TODO: we may want to create a 'sample_counts' class with methods to return it in different formatting

    )
    try:
        template_data['sample_counts'] = ' '.join('{:d}'.format(x) for x in sample_counts)
        template_data['compressed_sample_counts'] = ' '.join('{:d}'.format(x) for x in compress_counts(sample_counts))
    except TypeError:
        template_data['sample_periods'] = sample_counts

    if secondary_spectrum:
        secondary_spectrum.counts = secondary_spectrum.counts.astype(int)
        template_data.update(dict(secondary_spectrum=secondary_spectrum))

    try:
        templated_content = n42_mako_template.render(**template_data)
    except:
        logging.info("Mako Template exception:")
        err_msg = exceptions.text_error_template().render()
        logging.info(err_msg)
        print(err_msg)
        raise

    with open(filename, 'w', newline='') as f:
        f.write(templated_content)


def write_results(results_array, out_filepath):
    """
    Write a RASE-formatted results file from results data
    :param results_array: list of (isotope, confidence level) tuples
    :param out_filepath: full pathname of output file
    :return: None
    """
    root = etree.Element('IdentificationResults')

    if not results_array:
        results_array.append(('', 0))

    for iso, conf in results_array:
        identification = etree.SubElement(root, 'Identification')
        isotope = etree.SubElement(identification, 'IDName')
        isotope.text = iso
        confidence = etree.SubElement(identification, 'IDConfidence')
        confidence.text = conf

    indent(root)
    tree = etree.ElementTree(root)
    tree.write(out_filepath, encoding='utf-8', xml_declaration=True, method='xml')
    return


def strip_xml_tag(str):
    """
    Returns string stripped of XML tag
    """
    return re.sub('<[^<]+>', "", str)


def get_sample_dir(sample_root_dir, detector, scenario_id):
    """
    Returns the name of the folder where the generated sample spectra are saved
    """
    return os.path.join(sample_root_dir, '{}___{}'.format(detector.name, scenario_id))


def get_replay_input_dir(sample_root_dir, detector, scenario_id):
    """
    Returns the name of the folder where the sample spectra are saved in the format for the replay tool
    """
    replay_name = detector.replay_name
    if not (detector.replay and detector.replay.n42_template_path):
        replay_name = ""
    return os.path.join(get_sample_dir(sample_root_dir, detector, scenario_id), replay_name)


def get_replay_output_dir(sample_root_dir, detector, scenario_id):
    """
    Returns the name of the folder where the output of the replay tool is placed
    """
    return os.path.join(get_replay_input_dir(sample_root_dir, detector, scenario_id) + "_results", "")


def get_results_dir(sample_root_dir, detector, scenario_id):
    """
    Returns the name of the folder with the analyzed files (after replay) in RASE format
    """
    if not (detector.resultsTranslator and detector.resultsTranslator.exe_path):
        return get_replay_output_dir(sample_root_dir, detector, scenario_id)
    else:
        return os.path.join(get_replay_input_dir(sample_root_dir, detector, scenario_id) + "_translatedResults","")


def get_sample_spectra_filename(detector_name, scenario_id, filenum, suffix=".n42"):
    return f"{detector_name}___{scenario_id}___{filenum}{suffix}"


def files_endswith_exists(dir, endswith_filters):
    """
    Search if at least one file exists in 'dir' that ends with one of the specified filters
    :param dir: search path (folder)
    :param endswith_filters: tuple of file endings to filter e.g. (".n42",".res")
    :return: True if at least one file exists in path that match filter
    """
    if not os.path.exists(dir):
        return False
    for f in os.listdir(dir):
        if f.endswith(endswith_filters):
            return True
    return False


def count_files_endwith(dir, endswith_filters):
    """
    Search if any files exists in 'dir' that ends with one of the specified filters
    :param dir: search path (folder)
    :param endswith_filters: tuple of file endings to filter e.g. (".n42",".res")
    :return: Number of files that match the filter that exist in path
    """
    num_files = 0
    if not os.path.exists(dir):
        return 0
    for f in os.listdir(dir):
        if f.endswith(endswith_filters):
            num_files += 1
    return num_files


def delete_scenario(scenario_ids, sample_root_dir):
    """
    Delete scenarios from database and cleanup sample folders
    """
    session = Session()
    for id in scenario_ids:
        scenDelete = session.query(Scenario).filter(Scenario.id == id)
        matDelete = session.query(ScenarioMaterial).filter(ScenarioMaterial.scenario_id == id)
        backgMatDelete = session.query(ScenarioBackgroundMaterial).filter(ScenarioBackgroundMaterial.scenario_id == id)

        # folders
        folders = [name for name in glob.glob(os.path.join(sample_root_dir, "*" + id + "*"))]
        for folder in folders:
            shutil.rmtree(folder)

        # database
        scenObj = scenDelete.first()
        scenObj.scenario_groups.clear()
        matDelete.delete()
        backgMatDelete.delete()
        scenDelete.delete()
        session.commit()

    session.close()


def delete_instrument(session, name):
    sssDelete = session.query(SampleSpectraSeed).filter(SampleSpectraSeed.det_name == name)
    sssDelete.delete()
    detReplayDelete = session.query(Detector).filter(Detector.name == name)
    detReplayDelete.first().influences.clear()
    detReplayDelete.delete()
    detBaseRelationDelete = session.query(BaseSpectrum).filter(BaseSpectrum.detector_name == name)
    detBaseRelationDelete.delete()
    detBackRelationDelete = session.query(BackgroundSpectrum).filter(BackgroundSpectrum.detector_name == name)
    detBackRelationDelete.delete()
    session.commit()


def get_or_create_material(session, matname, include_intrinsic=False):
    material_name = Material.get_name(matname, include_intrinsic)
    material = session.query(Material).filter_by(name=material_name).first()
    if not material:
        material = Material(name=matname, include_intrinsic=include_intrinsic)
        session.commit()
    return material


def export_scenarios(scenarios_ids, file_path):
    """
    Export scenarios from database to xml file
    """
    session = Session()
    scenarios = [session.query(Scenario).filter_by(id=scenid).first() for scenid in scenarios_ids]

    scen_io = ScenariosIO()
    xml_str = scen_io.scenario_export(scenarios)
    Path(file_path).write_text(xml_str)


def import_scenarios(file_path, file_format='xml', group_name=None, group_desc=None):
    """
    Import scenarios from an xml file into a list of scenarios. Objects are not committed to db here.
    """
    scen_io = ScenariosIO(group_name=group_name, group_desc=group_desc)
    if file_format == 'csv':
        # import is taken from a tree directly
        xml_str = scen_io.xmlstr_from_csv(file_path)
        return scen_io.scenario_import(xml_str)
    elif file_format == 'xml':
        # xml is taken from a file
        return scen_io.scenario_import(Path(file_path).read_text())
    else:
        return []


def calc_result_uncertainty(p, n, alpha=0.05):
    """
    http://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval
    Alpha confidence intervals for a binomial distribution of p expected successes on n trials using the Wilson Score
    approach. Wilson Score intervals are biased towards 0.5, and are asymmetric, but have been shown to have a more
    accurate performance than "exact" methods such as Clopper-Pearson, which tend to be overly conservative (see
    Newcombe, 1998). z-values are hard-coded for alpha = 0.01 (99%), 0.05 (95%), 0.1 (90%), and 0.32 (68%).
    """
    alpha_dict = {
        0.01: 2.576,
        0.05: 1.96,
        0.1: 1.645,
        0.32: 0.994,
    }

    # z = norm.ppf(1 - alpha / 2)
    # TODO: add alpha drop-down selection in some window (correspondence table?) to prevent alphas not in dictionary
    # from being entered
    z = alpha_dict[alpha]
    p_prime = (p + z ** 2 / (2 * n)) / (1 + z ** 2 / n)
    s_prime = z * np.sqrt(p * (1 - p) / n + z ** 2 / (4 * n ** 2)) / (1 + z ** 2 / n)
    CI_pos = p_prime + s_prime
    CI_neg = p_prime - s_prime

    return CI_pos, CI_neg


def files_exist(directory, globadd='/*'):
    if os.path.exists(directory) and glob.glob(directory + globadd):
        return True
    return False


def apply_distortions(new_influences, counts, bin_widths, energies, ecal):
    count_bs = BaseSpectrum()
    if (not new_influences[0] == 0) or (not new_influences[2] == 0) or (not new_influences[1] == 1):
        counts = rebin(np.array(counts), energies, ecal)

    count_bs.counts = counts

    counts = gaussian_smearing(counts, bin_widths, new_influences[4], count_bs.is_spectrum_float())

    return counts

def calculate_influence(scenario, detector, degradations, ecal):
    session = Session()

    energies = np.polyval(ecal, np.arange(detector.chan_count))
    new_influences = []
    bin_widths = np.zeros([len(scenario.influences), len(energies)])
    for index, influence in enumerate(scenario.influences):
        detInfl = influence.detector_influence
        new_infl = [detInfl.infl_0, detInfl.infl_1, detInfl.infl_2, detInfl.fixed_smear, detInfl.linear_smear]
        if degradations:
            new_infl = [infl + deg for infl, deg in zip(new_infl, degradations[index])]
            # deal with potential negative values
            for position, n_inf in enumerate(new_infl):
                if n_inf < 0:
                    if not position == 1:
                        new_infl[position] = 0
                    else:
                        new_infl[position] = 0.0001

        new_influences.append(new_infl)

        if new_infl[0] != 0 or new_infl[2] != 0 or new_infl[1] != 1:
            energies = np.polyval([new_infl[2], (new_infl[1]), new_infl[0]], energies)
        # convert fixed energy smear distortion from energy to bins
        if new_infl[3] != 0:
            e_width = new_infl[3] / 2
            for sub_index, energy in enumerate(energies):
                b0 = np.roots([new_infl[2], new_infl[1], new_infl[0] - (energy - e_width)])
                b1 = np.roots([new_infl[2], new_infl[1], new_infl[0] - (energy + e_width)])
                bin_widths[index][sub_index] = max(b1) - max(b0)
    return new_influences, bin_widths, energies

def gaussian_smearing(orig_hist, bin_widths, res_percent, is_float=False):
    if is_float:
        order_of_mag_list = [round(np.log10(v)) for v in orig_hist if v > 0]  # to prevent scaling values to large
                                                                              # values that make sampling take forever
        if min(order_of_mag_list) < 0:
            oom_scale = int(np.power(10, (min(order_of_mag_list) + 1) * -1))
        else:
            oom_scale = int(np.power(10, max((4 - max(order_of_mag_list)), 0)))
        hist = np.array(orig_hist * oom_scale).astype(int)
    else:
        hist = orig_hist  # expect counts, so casting into int
    sigma = (res_percent / 100) / 2.355

    # gaussian smearing
    a = [np.random.normal(i, b + sigma * i, k) for i, (b, k) in enumerate(zip(bin_widths, hist))]
    a = np.concatenate(a)

    # reformat into an histogram
    smeared_hist, __ = np.histogram(a, bins=np.arange(0, len(orig_hist) + 1))

    if is_float:
        smeared_hist = smeared_hist / oom_scale

    return smeared_hist


def get_ids_from_webid(inputdir, outputdir, drf, url='http://127.0.0.1:8082', bkg_file=None):
    api_url = url + "/api/v1/analysis"
    for ff in [f for f in os.listdir(inputdir) if f.endswith(".n42")]:
        files = {"ipc": open(os.path.join(inputdir, ff), 'rb')}
        if bkg_file:
            files["back"] = open(bkg_file, 'rb')

        try:
            import requests
            r = requests.post(f'{api_url}?drf={drf}', files=files)
        except Exception as e:
            print(e)
            raise

        try:
            ids = [(i['name'], str(i['confidence'])) for i in r.json()['isotopes']]
        except:
            # if zero counts in primary spectrum, r.json() has no 'isotopes' key
            ids = None
        if not ids:  # no identifications
            ids = [('', '0')]

        id_report = etree.Element('IdentificationResults')
        for id_iso, id_conf in ids:
            id_result = etree.SubElement(id_report, 'Identification')
            id_name = etree.SubElement(id_result, 'IDName')
            id_name.text = id_iso
            id_confidence = etree.SubElement(id_result, 'IDConfidence')
            id_confidence.text = id_conf
        indent(id_report)

        etree.ElementTree(id_report).write(os.path.join(outputdir, ff.replace(".n42", ".res")), encoding='utf-8',
                                        xml_declaration=True, method='xml')
