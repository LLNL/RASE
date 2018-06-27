###############################################################################
# Copyright (c) 2018 Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory
#
# Written by J. Chavez, G. Kosinovsky, V. Mozin, S. Sangiorgio.
# RASE-support@llnl.gov.
#
# LLNL-CODE-750919
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
import ntpath
import os
import re
import shutil
import sys
import xml.etree.ElementTree as ET

import numpy as np
from sqlalchemy.engine import create_engine

from .table_def import BaseSpectrum, BackgroundSpectrum, Detector, Scenario, IdentificationSet, IdentificationReport, \
    IdentificationResult, Session, Base, DetectorInfluence, SampleSpectraSeed, ScenarioMaterial

from .utils import compress_counts

def initializeDatabase(databaseFilepath):
    """
    binds Session to database and creates new database if none exists

    :param databaseFilepath: path to src.sqlite file
    """
    engine  = create_engine('sqlite:///' + databaseFilepath)
    Session.configure(bind=engine)
    if not os.path.exists(databaseFilepath):
        Base.metadata.create_all(engine)


def importDistortionFile(filepath):
    """
    Import Influences from distorsion (.dis) xml file formatted as in old RASE
    :param filepath: path of valid influence file
    :return: array of influence names and corresponding distorsion values
    """
    root = ET.parse(filepath).getroot()
    detInfluences = []
    for inflElement in root:
        inflName = inflElement.tag
        inflVals = [float(value) for value in inflElement.find('Nonlinearity').text.split()]
        detInfluences.append((inflName, inflVals))
    return detInfluences


def importResultsDirectory(directory, scenarioId, detectorName):
    """

    :param directory:
    :param scenarioId:
    :param detectorName:
    :return:
    """
    if not os.path.exists(directory): return

    session  = Session()
    detector = session.query(Detector).filter_by(name = detectorName).first()
    scenario = session.query(Scenario).filter_by(id = scenarioId).first()
    idSet    = session.query(IdentificationSet).filter_by(det_name = detectorName, scen_id = scenarioId).first()
    if not idSet: idSet = IdentificationSet(det_name=detectorName, scen_id=scenarioId, replay=detector.replay)
    session.add(idSet)
    idSet.id_reports = []

    for filename in os.listdir(directory):
        if filename.endswith('.res'):
            filenum = int(filename.split('___')[2].replace('.res',''))
            idReport = IdentificationReport(filenum=filenum)
            idSet.id_reports.append(idReport)

            # parse each .res file and extract id_name, confidence and reported
            resultElements = ET.parse(os.path.join(directory, filename)).findall('IdentificationResult')
            for resultElement in resultElements:
                name = resultElement.find('IDName').text
                confidence = int(resultElement.find('IDConfidence').text)
                reported   = True if resultElement.find('Reported').text == 'true' else False

                idResult = IdentificationResult(name=name, confidence=confidence, reported=reported)
                idReport.results.append(idResult)
    idSet.scen_id=scenarioId
    session.commit()


def readTranslatedResultFile(filename):
    """
    Reads translated results file
    :param filename: path of valid influence file
    :return: array of results
    """
    root = ET.parse(filename).getroot()
    results = []
    for identification in root.findall('Identification'):
        idname = identification.find('IDName')
        # TODO: confidence level of the identification is neglected for now
        confidence = identification.find('IDConfidence')
        if idname.text:
            results.append(idname.text.strip())
    return results


def readSpectrumFile(filepath, sharedObject, tstatus):
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
        it = ET.iterparse(filepath)
        for _, el in it:
            el.tag = el.tag.split('}', 1)[-1]

        root = it.root
        # Now extract the relevant details from the file
        measurement = root.find('Measurement')
        rad_measurement = root.find('RadMeasurement')
        if measurement is not None:
            allSpectra = measurement.findall("Spectrum")
            if len(allSpectra) == 2:
                sharedObject.bcgndSpectrumInFile = True
                specElement = allSpectra[0]
                specElementBckg = allSpectra[1]
            else:
                specElement = allSpectra[0]
            if not specElement:
                message = "no Spectrum in file " + ntpath.basename(filepath)
                tstatus.append(message)
                return None
            chanData = specElement.find('ChannelData')
            if chanData is None:
                message = "no ChannelData in file " + ntpath.basename(filepath)
                tstatus.append(message)
                return None
            countsChar = chanData.text.strip("'").strip().split()
            if( "." in countsChar[0]):
                sharedObject.chanDataType = "float"
            else:
                sharedObject.chanDataType = "int"
            counts = [float(count) for count in countsChar]
            chanDataBckg = None
            countsBckg = None
            if sharedObject.isBckgrndSave and sharedObject.bcgndSpectrumInFile:
                chanDataBckg = specElementBckg.find('ChannelData')
                countsChar = chanDataBckg.text.strip("'").strip().split()
                countsBckg = [float(count) for count in countsChar]
            # uncompress if needed
            if chanData.attrib.get('Compression') == 'CountedZeroes':
                uncompressedCounts = []
                countsIter = iter(counts)
                for count in countsIter:
                    if count == float(0):
                        uncompressedCounts.extend([0] * int(next(countsIter)))
                    else: uncompressedCounts.append(count)
                counts =  ','.join(map(str, uncompressedCounts))
            else:
                counts = ','.join(map(str, counts))
            if chanDataBckg is not None:
                if chanDataBckg.attrib.get('Compression') == 'CountedZeroes':
                    uncompressedCounts = []
                    countsIter = iter(countsBckg)

                    for count in countsIter:
                        if count == float(0):
                            uncompressedCounts.extend([0] * int(next(countsIter)))
                        else:
                            uncompressedCounts.append(count)
                    countsBckg =  ','.join(map(str, uncompressedCounts))
                else:
                    countsBckg = ','.join(map(str, countsBckg))

            realtimeBckg    = None
            livetimeBckg    = None
            ecalBckg = None
            calibration = specElement.find('Calibration')
            if calibration is None:
                calibration = root.find('Calibration')
            ecal = []
            if calibration is not None:
                calElement = calibration.find('Equation').find('Coefficients')
                ecal        = [float(value) for value in calElement.text.split()]
            else:
                message = "no Calibration in file " + ntpath.basename(filepath)
                tstatus.append(message)
                return None
            if specElement.find('RealTime') is None:
                message = "no RealTime in file " + ntpath.basename(filepath)
                tstatus.append(message)
                return None
            else:
                realtime = getSeconds(specElement.find('RealTime').text.strip())
            if specElement.find('LiveTime') is None:
                message = "no LiveTime in file " + ntpath.basename(filepath)
                tstatus.append(message)
                return None
            else:
                livetime = getSeconds(specElement.find('LiveTime').text.strip())
            if specElement.find('RASE_Sensitivity') is None:
                message = "no RASE_Sensitivity in file " + ntpath.basename(filepath)
                tstatus.append(message)
                return None
            else:
                sensitivity = float(specElement.find('RASE_Sensitivity').text.strip())

            if chanDataBckg is not None:
                ecalBckg = []
                calibrationBckg = specElementBckg.find('Calibration')
                if calibrationBckg is not None:
                    calElement = calibrationBckg.find('Equation').find('Coefficients')
                    ecalBckg        = [float(value) for value in calElement.text.split()]
                else:
                    message = "no Background Calibration in file " + ntpath.basename(filepath)
                    tstatus.append(message)
                if specElementBckg.find('RealTime') is None:
                    message = "no Background RealTime in file " + ntpath.basename(filepath)
                    tstatus.append(message)
                else:
                    realtimeBckg = getSeconds(specElementBckg.find('RealTime').text.strip())
                if specElementBckg.find('LiveTime') is None:
                    message = "no Background LiveTime in file " + ntpath.basename(filepath)
                    tstatus.append(message)
                else:
                    livetimeBckg = getSeconds(specElementBckg.find('LiveTime').text.strip())

            return counts, ecal, realtime, livetime, sensitivity, countsBckg, ecalBckg, realtimeBckg, livetimeBckg
        elif rad_measurement is not None:
            allRad = root.findall("RadMeasurement")
            if len(allRad) == 2:
                sharedObject.bcgndSpectrumInFile = True
                radElement = allRad[0]
                radElementBckg = allRad[1]
            else:
                radElement = allRad[0]
            if radElement is None:
                message = "no RadMeasurement in file " + ntpath.basename(filepath)
                tstatus.append(message)
                return None
            specElement = radElement.find('Spectrum')
            if specElement is None:
                message = "no Spectrum in file " + ntpath.basename(filepath)
                tstatus.append(message)
                return None
            chanData = specElement.find('ChannelData')
            if chanData is None:
                message = "no ChannelData in file " + ntpath.basename(filepath)
                tstatus.append(message)
                return None
            countsChar = chanData.text.strip("'").strip().split()
            counts = [float(count) for count in countsChar]
            if( "." in countsChar[0]):
                sharedObject.chanDataType = "float"
            else:
                sharedObject.chanDataType = "int"
            counts = ','.join(map(str, counts))
            chanDataBckg = None
            countsBckg = None
            if sharedObject.isBckgrndSave and sharedObject.bcgndSpectrumInFile:
                specElementBckg = radElementBckg.find('Spectrum')
                chanDataBckg = specElementBckg.find('ChannelData')
                countsChar = chanDataBckg.text.strip("'").strip().split()
                countsBckg = [float(count) for count in countsChar]
                countsBckg = ','.join(map(str, countsBckg))
            realtimeBckg    = None
            livetimeBckg    = None
            ecalBckg = None
            calibration = root.find('EnergyCalibration')
            ecal = []
            if calibration is not None:
                calElement = root.find('EnergyCalibration').find('CoefficientValues')
                ecal = [float(value) for value in calElement.text.split()]
            else:
                message = "no Calibration in file " + ntpath.basename(filepath)
                tstatus.append(message)
                return None
            if radElement.find('RealTimeDuration') is None:
                message = "no RealTime in file " + ntpath.basename(filepath)
                tstatus.append(message)
                return None
            else:
                realtime = getSeconds(radElement.find('RealTimeDuration').text.strip())
            if specElement.find('LiveTimeDuration') is None:
                message = "no LiveTime in file " + ntpath.basename(filepath)
                tstatus.append(message)
                return None
            else:
                livetime = getSeconds(specElement.find('LiveTimeDuration').text.strip())
            if specElement.find('RASE_Sensitivity') is None:
                message = "no RASE_Sensitivity in file " + ntpath.basename(filepath)
                tstatus.append(message)
                raise ValueError('sensitivity is missing')
                return None
            else:
                sensitivity = float(specElement.find('RASE_Sensitivity').text.strip())

            if chanDataBckg is not None:
                ecalBckg = ecal
                if radElementBckg.find('RealTimeDuration') is None:
                    message = "no Background RealTime in file " + ntpath.basename(filepath)
                    tstatus.append(message)
                else:
                    realtimeBckg = getSeconds(radElementBckg.find('RealTimeDuration').text.strip())
                if specElementBckg.find('LiveTimeDuration') is None:
                    message = "no Background LiveTime in file " + ntpath.basename(filepath)
                    tstatus.append(message)
                else:
                    livetimeBckg = getSeconds(specElementBckg.find('LiveTimeDuration').text.strip())

            return counts, ecal, realtime, livetime, sensitivity, countsBckg, ecalBckg, realtimeBckg, livetimeBckg

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
        if oe == len(oldEnergies): break # have already distributed all old counts

        # if no old energy boundaries within this new bin, new bin is fraction of old bin
        if oldEnergies[oe] > newEnergies[ne+1]:
            newCounts[ne] = counts[oe-1] * (newEnergies[ne+1] - newEnergies[ne]) \
                            / (oldEnergies[oe]   - oldEnergies[oe-1])

        # else there are old energy boundaries in this new bin: add each portion of old bins
        else:
            # Step 1: add first partial(or full) old bin
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


def _getCountsDoseAndSensitivity(scenario, detector):
    """

    :param scenario:
    :param detector:
    :return:
    """
    session = Session()

    # distortion:  distort ecal with influence factors
    ecal = [detector.ecal3, detector.ecal2, detector.ecal1, detector.ecal0]
    energies = np.polyval(ecal, np.arange(detector.chan_count))
    if scenario.influences:
        for infl in scenario.influences:
            detInfl = (session.query(DetectorInfluence)
                       .filter_by(detector_name = detector.name,
                                  influence = infl)
                       ).first()
            energies = np.polyval([detInfl.infl_2, detInfl.infl_1, detInfl.infl_0], energies)

    # get dose, counts and sensitivity for each material
    countsDoseAndSensitivity = []
    for scenMaterial in scenario.scen_materials:

        baseSpectrum = (session.query(BaseSpectrum)
                        .filter_by(detector_name = detector.name,
                                   material_name = scenMaterial.material_name)
                        ).first()
        counts = np.array([int(float(c)) for c in baseSpectrum.baseCounts.split(",")])

#        counts = np.array([baseCount.count for baseCount in baseSpectrum.baseCounts])

        # apply distortion on counts
        if scenario.influences:
            counts = rebin(np.array(counts), energies, ecal)

        countsDoseAndSensitivity.append((counts, scenMaterial.dose, baseSpectrum.sensitivity))

    # if the detector has an internal calibration source, it needs to be added with special treatment
    if detector.includeSecondarySpectrum and detector.secondary_type == 2:

        secondary_spectrum = (session.query(BackgroundSpectrum).filter_by(detector_name = detector.name)).first()
        counts = np.array([int(float(c)) for c in secondary_spectrum.baseCounts.split(",")])

        # apply distortion on counts
        if scenario.influences:
            counts = rebin(np.array(counts), energies, ecal)

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
    f.write('      <RealTime Unit="sec">PT{}S</RealTime>\n'.format(scenario.acq_time))
    f.write('      <LiveTime Unit="sec">PT{}S</LiveTime>\n'.format(scenario.acq_time))
    f.write('      <Calibration Type="Energy" EnergyUnits="keV">\n')
    f.write('        <Equation Model="Polynomial">\n')
    f.write('          <Coefficients>{} {} {} {}</Coefficients>\n'.format(detector.ecal0, detector.ecal1, detector.ecal2, detector.ecal3))
    f.write('        </Equation>\n')
    f.write('      </Calibration>\n')
    f.write('      <ChannelData>')
    f.write('{}'.format(' '.join('{:d}'.format(x) for x in sample_counts)))
    f.write('</ChannelData>\n')
    f.write('    </Spectrum>\n')
    if secondary_spectrum:
        sec_counts = [int(float(c_str)) for c_str in secondary_spectrum.baseCounts.split(",")]
        f.write('    <Spectrum>\n')
        f.write('      <RealTime Unit="sec">PT{}S</RealTime>\n'.format(secondary_spectrum.realtime))
        f.write('      <LiveTime Unit="sec">PT{}S</LiveTime>\n'.format(secondary_spectrum.livetime))
        f.write('      <Calibration Type="Energy" EnergyUnits="keV">\n')
        f.write('        <Equation Model="Polynomial">\n')
        f.write('          <Coefficients>{} {} {} {}</Coefficients>\n'.format(detector.ecal0, detector.ecal1,
                                                                              detector.ecal2, detector.ecal3))
        f.write('        </Equation>\n')
        f.write('      </Calibration>\n')
        f.write('      <ChannelData>')
        f.write('{}'.format(' '.join('{:d}'.format(x) for x in sec_counts)))
        f.write('</ChannelData>\n')
        f.write('    </Spectrum>\n')
    f.write('  </Measurement>\n')
    f.write('</N42InstrumentData>\n')
    f.close()


def create_n42_file_from_template(n42_mako_template, filename, scenario, detector, sample_counts, secondary_spectrum=None):
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
        sample_counts=' '.join('{:d}'.format(x) for x in sample_counts),    # FIXME: this is forced to integers
        compressed_sample_counts=' '.join('{:d}'.format(x) for x in compress_counts(sample_counts)),
    )

    if secondary_spectrum:
        template_data.update(dict(secondary_spectrum=secondary_spectrum))

    f = open(filename, 'w', newline='')
    f.write(n42_mako_template.render(**template_data))
    f.close()


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
    return os.path.join(get_replay_input_dir(sample_root_dir, detector, scenario_id) + "_results")


def get_results_dir(sample_root_dir, detector, scenario_id):
    """
    Returns the name of the folder with the analyzed files (after replay) in RASE format
    """
    if not (detector.resultsTranslator and detector.resultsTranslator.exe_path):
        return get_replay_output_dir(sample_root_dir, detector, scenario_id)
    else:
        return os.path.join(get_replay_input_dir(sample_root_dir, detector, scenario_id) + "_translatedResults")


def delete_scenario(scenario_ids, sample_root_dir):
    """
    Delete scenarios from database and cleanup sample folders
    """
    session = Session()
    for id in scenario_ids:
        scenDelete = session.query(Scenario).filter(Scenario.id == id)
        matDelete = session.query(ScenarioMaterial).filter(ScenarioMaterial.scenario_id == id)

        # folders
        folders = [name for name in glob.glob(os.path.join(sample_root_dir, "*" + id + "*"))]
        for folder in folders:
            shutil.rmtree(folder)

        # database
        matDelete.delete()
        scenDelete.delete()
        session.commit()

    session.close()

