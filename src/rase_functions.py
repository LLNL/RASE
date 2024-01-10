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
from src.table_def import BaseSpectrum, BackgroundSpectrum, SecondarySpectrum, Detector, Scenario, \
    SampleSpectraSeed, Session, Base, ScenarioMaterial, ScenarioBackgroundMaterial, Material, \
    DetectorInfluence
from src.utils import compress_counts, indent

# Key variables used in several places
secondary_type = {'base_spec': 0, 'scenario': 1, 'file': 2}


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
    try:
        outTime = isodate.parse_duration(inTime)
    except:
        outTime = isodate.parse_duration('PT'+inTime+'S')
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


def process_confidences(confidences: list, results: list, use_confs: bool) -> list:
    """
    Process the confidence values from the results files.
    If `use_confs == True` then confidences are mapped to 'low', 'medium', 'high' values
    of 0.33, 0.66 and 1 respectively, otherwise confidences are converted to 1 for each result.
    Returns the updated list of confidences
    """
    if use_confs and confidences:
        # for some instruments (e.g.: RadEagle), the confidences are zeros while the isotopes are dashes
        if len(confidences) > len(results):
            confidences = confidences[0:len(results)]
        if confidences:
            try:
                # 0 - 3 = low, 4 - 6 = medium, 7 - 10 = high
                confidences = [(int(float(c) / 3.4) + 1) / 3 for c in confidences]
            except Exception as e:
                raw_confidences = confidences
                confidences = []
                for c in raw_confidences:
                    if c == 'low':
                        confidences.append(1 / 3)
                    elif c == 'medium':
                        confidences.append(2 / 3)
                    else:
                        confidences.append(1)  # default to full confidence in results
    else:
        confidences = [1] * len(results)
    return confidences


def readTranslatedResultFile(filename, use_confs):
    """
    Reads translated results file from defaults formats

    Format 1 (RASE defined):
    //IdentificationResults
		/Isotopes (single)
			/text(): \n-separated list of identification labels
		/ConfidenceIndex (single)
			/text(): \n-separated list of confidence indices

	Format 2 (RASE defined):
	//IdentificationResults
	    /Identification (multiple)
    	    /IDName
	            /text(): nuclide label
	        /IDConfidence
	            /text(): confidence level

    Format 3 (BARNI):
    // NuclideResult
        /Nuclide
        /Score

    Format 4 (n42-2011)
    Used by:
     - most FLIR except R440
     - CAEN DiscoveRAD
     - Symetrica SN33

    Format 5 (ICD2/HPRDS)
    Used by:
     - Smiths RadSeeker
     - ORTEC HPGe replay tool (standalone version)

     Format 6 (CSV)
     Used by: Kromek D5 - PCS Offline v170.1.5.7
     it processes only the first line since we expect 1 spectrum per file

    :param filename: path of valid results file
    :param use_confs: when set confidences are mapped to 'low', 'medium', 'high' values
    :return: list of identification results
    """
    if os.path.getsize(os.path.join(str(filename))) == 0:
        return [], []

    # Parse CSV format (Kromek D5 PCS Offline)
    # Label1, Label2, Integration time, Messages(i.e.errors), Result1 confidence, Result1 isotope, Result2 confidence, Result2 isotope, ...
    if str(filename).endswith(".csv"):
        with open(filename) as f:
            f.readline()  # skip header line
            line = f.readline()
            raw_results = [s.strip() for s in line.split(',')[4:]]
        results = raw_results[1::2]
        confidences = process_confidences(raw_results[0::2], results, use_confs)
        return results, confidences

    root = etree.parse(str(filename)).getroot()
    if ((root.tag != "IdentificationResults")   # RASE Format 1, 2
            and (root.tag != "NuclideResultList")  # BARNI
            and not (root.tag.endswith("RadInstrumentData"))  # n42-2011
            and (root.tag != 'Event')):  # ICD2/HPRDS
        raise ResultsFileFormatException(f'{filename}: bad file format')

    # Parse RASE format 1
    confidences = []
    results = []
    if len(root.findall('Isotopes')) > 0:
        isotopes = root.find('Isotopes').text
        if isotopes:
            results = list(filter(lambda x: x.strip() not in ['-', ''], isotopes.split('\n')))
            confidences_str = ''
            if root.find('ConfidenceIndex') is not None:
                confidences_str = root.find('ConfidenceIndex').text
            elif root.find('Confidences') is not None:
                confidences_str = root.find('Confidences').text
            if confidences_str:
                confidences = list(filter(lambda x: x.strip() not in ['-', ''], confidences_str.split('\n')))
    # Parse RASE Format 2
    elif len(root.findall('Identification')) > 0:
        for identification in root.findall('Identification'):
            idname = identification.find('IDName')
            if idname.text:
                results.append(idname.text.strip())
                confidences.append(identification.find('IDConfidence').text.strip())
            else:
                confidences.append('')
    # Parse BARNI output format
    elif len(root.findall('NuclideResult')) > 0:
        for identification in root.findall('NuclideResult'):
            idname = identification.find('nuclide')
            if idname.text:
                results.append(idname.text.strip())
                confidences.append(identification.find('score').text.strip())
            else:
                confidences.append('')
    # Parse n42-2011 format
    # For simplicity '{*}' is used to accept all namespaces
    elif root.tag.endswith("RadInstrumentData"):
        if root.find('.//{*}NuclideAnalysisResults') is not None:
            for element in root.findall('.//{*}Nuclide'):
                results.append(element.find('{*}NuclideName').text)
                confidences.append(element.find('{*}NuclideIDConfidenceValue').text)
    # Parse ICD2/HPRDS
    elif len(root.findall('AnalysisResults')):
        for nuclide in root.iter('Nuclide'):
            results.append(nuclide.find('NuclideName').text)
            confidences.append(nuclide.find('NuclideIDConfidence').text)
    else:
        raise ResultsFileFormatException(f'{filename}: bad file format')

    confidences = process_confidences(confidences, results, use_confs)
    return results, confidences







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
    newEnergies = np.polyval(np.flip(newEcal), np.arange(len(counts)+1))
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
            oldenergies = np.polyval(np.flip(baseSpectrum.ecal), np.arange(detector.chan_count))
            counts = rebin(counts, oldenergies, ecal)

        if scenario.influences:
            for index, infl in enumerate(new_influences):
                counts = apply_distortions(infl, counts, bin_widths[index], energies, ecal)

        if scenMaterial.fd_mode == 'FLUX':
            countsDoseAndSensitivity.append((counts, scenMaterial.dose, baseSpectrum.flux_sensitivity))
        else:
            countsDoseAndSensitivity.append((counts, scenMaterial.dose, baseSpectrum.rase_sensitivity))

    # if the detector has an internal calibration source, it needs to be added with special treatment
    if detector.includeSecondarySpectrum and detector.sample_intrinsic:

        secondary_spectra = session.query(SecondarySpectrum).filter_by(detector_name=detector.name).all()
        secondary_spectrum = [k for k in secondary_spectra if k.classcode == detector.intrinsic_classcode][0]
        # secondary_spectrum = (session.query(BackgroundSpectrum).filter_by(detector_name=detector.name)).first()
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
    f.write('      <MeasurementClassCode>Foreground</MeasurementClassCode>\n')
    f.write('      <RealTime Unit="sec">PT{}S</RealTime>\n'.format(scenario.acq_time))
    f.write('      <LiveTime Unit="sec">PT{}S</LiveTime>\n'.format(scenario.acq_time))
    f.write('      <Calibration Type="Energy" EnergyUnits="keV">\n')
    f.write('        <Equation Model="Polynomial">\n')
    f.write('          <Coefficients>{} {} {} {}</Coefficients>\n'.format(detector.ecal0, detector.ecal1, detector.ecal2, detector.ecal3))
    f.write('        </Equation>\n')
    f.write('      </Calibration>\n')
    f.write('      <ChannelData>')
    if all([float(k) == int(k) for k in sample_counts]):
        f.write('{}'.format(' '.join('{:d}'.format(x) for x in sample_counts)))
    else:
        f.write('{}'.format(' '.join('{:f}'.format(x) for x in sample_counts)))
    f.write('</ChannelData>\n')
    f.write('    </Spectrum>\n')
    if secondary_spectrum:
        if (detector.secondary_type == secondary_type['scenario']):
            type_str = 'Background'
        elif (detector.sample_intrinsic and len(detector.secondary_spectra) == 1) or \
                detector.secondary_classcode == 'Calibration':
            type_str = 'Calibration'
        else:
            type_str = detector.secondary_classcode #'Background'
        f.write('    <Spectrum>\n')
        f.write(f'      <MeasurementClassCode>{type_str}</MeasurementClassCode>\n')
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
        template_data['sample_counts_array'] = sample_counts
        template_data['bin_edges'] = ' '.join(str(v) for v in np.polyval([detector.ecal3, detector.ecal2, detector.ecal1, detector.ecal0], np.arange(detector.chan_count+1)))
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
    return os.path.join(sample_root_dir, '{}___{}'.format(detector.id, scenario_id))


def get_replay_input_dir(sample_root_dir, detector, scenario_id):
    """
    Returns the name of the folder where the sample spectra are saved in the format for the replay tool
    """
    if not (detector.replay and detector.replay.n42_template_path):
        replay_id = ""
    else:
        replay_id = detector.replay.id
    return os.path.join(get_sample_dir(sample_root_dir, detector, scenario_id), replay_id)


def get_replay_output_dir(sample_root_dir, detector, scenario_id):
    """
    Returns the name of the folder where the output of the replay tool is placed
    """
    return os.path.join(get_replay_input_dir(sample_root_dir, detector, scenario_id) + "_results", "")


def get_results_dir(sample_root_dir, detector, scenario_id):
    """
    Returns the name of the folder with the analyzed files (after replay) in RASE format
    """
    if not (detector.replay and detector.replay.translator_exe_path):
        return get_replay_output_dir(sample_root_dir, detector, scenario_id)
    else:
        return os.path.join(get_replay_input_dir(sample_root_dir, detector, scenario_id) + "_translatedResults","")


def get_sample_spectra_filename(detector_id: str, scenario_id: str, filenum: int, suffix=".n42"):
    return f"{detector_id}___{scenario_id}___{filenum}{suffix}"


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
        scenObj.influences.clear()
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
    # detBaseRelationDelete = session.query(BaseSpectrum).filter(BaseSpectrum.detector_name == name)
    # detBaseRelationDelete.delete()
    # detBackRelationDelete = session.query(BackgroundSpectrum).filter(BackgroundSpectrum.detector_name == name)
    # detBackRelationDelete.delete()
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

    energies = np.polyval(np.flip(ecal), np.arange(detector.chan_count))
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
    #TODO: Temp fix to make gaussian smearing fast by forcing integers in influence scenarios
    is_float = False
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
    a = [np.random.normal(i, b + sigma * i, int(k)) for i, (b, k) in enumerate(zip(bin_widths, hist))]
    a = np.concatenate(a)

    # reformat into an histogram
    smeared_hist, __ = np.histogram(a, bins=np.arange(0, len(orig_hist) + 1))

    if is_float:
        smeared_hist = smeared_hist / oom_scale

    return smeared_hist


def get_ids_from_webid(inputdir, outputdir, drf, url='https://full-spectrum.sandia.gov/', bkg_file=None, synthesize_bkg=False):
    api_url = url.strip('/') + "/api/v1/analysis"
    for ff in [f for f in os.listdir(inputdir) if f.endswith(".n42")]:
        files = {"ipc": open(os.path.join(inputdir, ff), 'rb')}
        if bkg_file:
            files["back"] = open(bkg_file, 'rb')

        import json
        payload = {"options": json.dumps({'synthesizeBackground': synthesize_bkg, 'drf': drf})}

        try:
            import requests
            r = requests.post(f'{api_url}', files=files, data=payload)
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


def get_DRFList_from_webid(url='https://full-spectrum.sandia.gov/'):
    """
    Get List of DRFs available in WebID from querying the API
    """
    try:
        import requests
        r = requests.post(f'{url}/api/v1/info')
    except Exception as e:
        print(e)
        return None

    return r.json()['Options'][0]['possibleValues'] if r else None
