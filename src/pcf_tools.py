###############################################################################
# Copyright (c) 2018-2022 Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory
#
# Written by J. Chavez, S. Czyz, G. Kosinovsky, V. Mozin, S. Sangiorgio.
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
Class to read PCF files

PCF File format definition from:
Thoreson, Gregory G. 2019. "PCF File Format". United States. https://doi.org/10.2172/1762353

Adapted from original work by Lance Bentley-Tammero
"""
import struct
import os
from time import localtime, strftime
import numpy as np
import xml.etree.ElementTree as ET
from xml.dom import minidom
from pathlib import Path


class Spectrum(object):
    """this class contain a spectrum objects
    """

    def __init__(self):
        self.title = ''
        self.info = ''
        self.source_list = ''
        self.date = strftime("%d-%b-%Y %H:%M:%S.00", localtime())
        self.tag = 'T'

        self.live_time = 0.
        self.real_time = 0.

        self.resv1 = 0.  # offset
        self.resv2 = 0.  # gain (full-range fraction)
        self.resv3 = 0.  # quadratic term (full-range fraction)
        self.resv4 = 0.  # cubic term (full-range fraction)

        self.neutron_counts = 0.

        self.gamma_channels = 0
        self.gamma_counts = []

    def get_calibration_polynomial_coefficients(self):
        """Return polynomial calibration coefficients """
        ecal0 = self.resv1
        ecal1 = self.resv2 / self.gamma_channels
        ecal2 = self.resv3 / (self.gamma_channels ** 2)
        ecal3 = self.resv4 / (self.gamma_channels ** 3)
        return ecal0, ecal1, ecal2, ecal3


def readpcf(file_name):
    """read a pcf file and return a list of spectrum objects, 1 for each
    spectrum in the file"""
    out = []  # list containing output spectrum objects

    # open the input file to read binary using the "with" so the file is
    # properly closed in the event of an exception
    with open(file_name, "rb") as fid:

        # read two bytes, since this is a short, and it's two bytes long
        chunk = fid.read(2)
        # little endian,signed char (int)... since unpack returns a tuple
        # want first element
        nrps = struct.unpack("<h", chunk)[0]
        # print(nrps)
        chunk = fid.read(254)  # read the header
        # header = struct.unpack("<254s", chunk)[0]  # little endian string

        channels = 0
        total = 1

        while not file_eof(fid):
            spect = Spectrum()
            spect.title = nullstrip(struct.unpack("<60s", fid.read(60))[0])
            if spect.title.find('DeviationPairs') > -1:
                fid.seek(256 - 60, 1)
                fid.seek(256 * 80, 1)
                spect.title = nullstrip(struct.unpack("<60s", fid.read(60))[0])

            spect.info = nullstrip(struct.unpack("<60s", fid.read(60))[0])
            spect.source_list = nullstrip(
                struct.unpack("<60s", fid.read(60))[0]
            )
            spect.date = nullstrip(
                struct.unpack("<23s", fid.read(23))[0]
            )
            spect.tag = nullstrip(struct.unpack("<c", fid.read(1))[0])

            spect.live_time = struct.unpack("<f", fid.read(4))[0]
            spect.real_time = struct.unpack("<f", fid.read(4))[0]

            fid.read(4 * 3)  # skip 3 unused 4-byte floating points

            spect.resv1 = struct.unpack("<f", fid.read(4))[0]
            spect.resv2 = struct.unpack("<f", fid.read(4))[0]
            spect.resv3 = struct.unpack("<f", fid.read(4))[0]
            spect.resv4 = struct.unpack("<f", fid.read(4))[0]

            fid.read(4)  # skip energy calibration low-energy term
            fid.read(4)  # skip 1 unused 4-byte floating point

            spect.neutron_counts = struct.unpack("<f", fid.read(4))[0]

            spect.gamma_channels = struct.unpack("<i", fid.read(4))[0]
            if spect.gamma_channels > 0:
                channels = spect.gamma_channels

            # need to read in [channels] number of floats now
            gamma_counts = []
            for ctr in range(channels):
                gamma_counts.append(struct.unpack("<f", fid.read(4))[0])

            spect.gamma_counts = np.array(gamma_counts)
            extra = 256 * nrps - 254 - 4 * channels - 2
            if extra > 0:
                # move the file pointer along?
                fid.seek(extra, 1)

            if spect.live_time > 0:
                out.append(spect)
                total = total + 1

    fid.close()
    return out


def nullstrip(string_in):
    """strip a string of all '\x00' characters
    """
    # fix for python3
    string_in = string_in.decode("utf-8")
    # nonNullLocations = []
    str_ret = ''
    for str_val in string_in:
        # print(s[idx])
        if str_val != '\x00':
            # nonNullLocations.append(idx)
            str_ret = str_ret + str_val
    return str_ret


def file_eof(filehandle):
    """since python has no way to tell if you're at end of file
    and if I were to do the simple (read(1) == '') test,
    it advances the file pointer, I need to create something where I do the
    read, then I move the pointer back"""

    # use this for python 2.x
    # if filehandle.read(1) == '':

    # use this for python 3.x
    if filehandle.read(1).decode("utf-8") == '':
        return True
    else:
        # move the pointer back one from the current position
        # print(filehandle.tell())
        filehandle.seek(-1, 1)
        # print(filehandle.tell())
        return False


def batch_load_spectra(directory_in):
    """load a series of pcf files from the input directory and write them
    to a list of spectrum objects
    """
    file_list = os.listdir(directory_in)
    spectrum_list = []
    for pcf_file in sorted(file_list):
        if pcf_file[-3:] == 'pcf' and pcf_file[0:2] != 'DB':
            curr_specs = readpcf(os.path.join(directory_in, pcf_file))
            spectrum_list.append(curr_specs[0])
    return spectrum_list


def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


def get_channel_data_string(array_in):
    """ convert the channel data array to string for the xml
    """
    return " ".join([f"{val:.4F}" if val > .1 else f"{val:.4G}"
                     for val in array_in])


class PCFtoN42Writer:
    """
    Class to write RASE-compliant n42 output from PCF files
    """

    def __init__(self, pcf_file_in):
        self.pcf_file_in = Path(pcf_file_in)
        self.pcf = readpcf(pcf_file_in)
        print(f"Successfully read {len(self.pcf)} spectra")

    def _add_data_to_n42(self, spec_in):
        """returns n42 XML
        """
        top = ET.Element('RadInstrumentData')

        calibration = ET.SubElement(top, 'EnergyCalibration')
        coefficients = ET.SubElement(calibration, 'CoefficientValues')
        coefficients.text = "  ".join([str(val) for val in spec_in.get_calibration_polynomial_coefficients()])

        measurement = ET.SubElement(top, 'RadMeasurement')
        self._add_spec_to_measurement(spec_in, measurement)
        return prettify(top)

    def _add_spec_to_measurement(self, spec_in, measurement):
        spectrum = ET.SubElement(measurement, 'Spectrum')

        real_time = ET.SubElement(spectrum, 'RealTimeDuration')
        live_time = ET.SubElement(spectrum, 'LiveTimeDuration')
        real_time.text = f"PT{spec_in.real_time}S"
        live_time.text = f"PT{spec_in.live_time}S"

        channel_data = ET.SubElement(spectrum, 'ChannelData')
        channel_data.text = get_channel_data_string(spec_in.gamma_counts)

    def generate_n42(self, dir_out, file_list=None):
        """
        generate the RASE n42 files from the spectra
        """
        if not file_list:
            file_list = [Path(self.pcf_file_in.with_suffix('').name + f'_{i}.n42') for i in range(0, len(self.pcf))]
        dir_out = Path(dir_out)
        if not dir_out.exists():
            os.makedirs(dir_out)

        filenames_map = {}
        for i, (spec, f_out) in enumerate(zip(self.pcf, file_list)):
            xml_str = self._add_data_to_n42(spec)
            with open(dir_out / f_out, 'w') as fod:
                fod.write(xml_str)
                filenames_map[i] = str(f_out)
        return filenames_map
