#!/usr/bin/env python3
#
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
Connect to GADRAS Full Spectrum ID web server using the REST API and save the results to file
"""

# To generate a windows executable version:
# python -m PyInstaller -a -y -F --clean --noupx --distpath ..\dist --workpath ..\build GADRAS_Full_Spectrum_ID.py

import sys

__author__ = 'sangiorgio1'

import os
import xml.etree.ElementTree as ET
import requests

# settings
api_url = "http://127.0.0.1:8082/api/v1/analysis"
drfs = ['1x1/BGO Side', '1x1/CsI Side', '1x1/LaCl3', '1x1/NaI Front', '1x1/NaI Side', '3x3/NaI AboveSource',
        '3x3/NaI InCorner', '3x3/NaI LowScat', '3x3/NaI MidScat', '3x3/NaI OnGround', 'ASP-Thermo', 'Apollo/Bottom',
        'Apollo/Front', 'Atomex-AT6102', 'D3S', 'Detective', 'Detective-EX', 'Detective-EX100', 'Detective-EX200',
        'Detective-Micro', 'Detective-Micro/Variant-LowEfficiency', 'Detective-X', 'Falcon 5000', 'FieldSpec', 'GR130',
        'GR135', 'GR135Plus', 'IdentiFINDER-LaBr3', 'IdentiFINDER-N', 'IdentiFINDER-NG', 'IdentiFINDER-NGH',
        'IdentiFINDER-R300', 'IdentiFINDER-R500-NaI', 'InSpector 1000 LaBr3', 'InSpector 1000 NaI', 'Interceptor',
        'LaBr3Marlow', 'LaBr3PNNL', 'MKC-A03', 'Mirion PDS-100', 'Polimaster PM1704-GN', 'RIIDEyeX-GN1', 'RadEagle',
        'RadEye', 'RadPack', 'RadSeeker-NaI', 'Radseeker-LaBr3', 'Raider', 'Ranger', 'SAM-935', 'SAM-945',
        'SAM-950GN-N30', 'SAM-Eagle-LaBr3', 'SAM-Eagle-NaI-3x3', 'SpiR-ID/LaBr3', 'SpiR-ID/NaI', 'Thermo ARIS Portal',
        'Transpec', 'Verifinder']


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


def generate_id_report(identifications):
    id_report = ET.Element('IdentificationResults')

    for id_iso, id_conf in identifications:
        id_result = ET.SubElement(id_report, 'Identification')
        id_name = ET.SubElement(id_result, 'IDName')
        id_name.text = id_iso
        id_confidence = ET.SubElement(id_result, 'IDConfidence')
        id_confidence.text = id_conf
    indent(id_report)
    return id_report


def get_file_list(in_folder):
    return [f for f in os.listdir(in_folder) if f.endswith(".n42")]


if __name__ == '__main__':

    if len(sys.argv) < 4:
        print("USAGE: GADRAS_Full_Spectrum_ID INPUTDIR OUTPUTDIR DRF-NAME [background_file]")
        print("Available DRFs: ")
        print(*drfs, sep=', ')
        sys.exit(1)

    inputFolder = sys.argv[1]
    outputFolder = sys.argv[2]
    drf = sys.argv[3]
    bkg_file = sys.argv[4] if (len(sys.argv) == 5) else None

    if drf not in drfs:
        print("ERROR: an unknown DRF name was provided")
        print("Available DRFs: ")
        print(*drfs, sep=', ')
        sys.exit(1)

    for ff in get_file_list(inputFolder):
        files = {"ipc": open(os.path.join(inputFolder, ff), 'rb')}
        if bkg_file:
            files["back"] = open(bkg_file, 'rb')

        try:
            r = requests.post(f'{api_url}?drf={drf}', files=files)
        except Exception as e:
            print(e)
            sys.exit(-1)

        ids = [(i['name'], str(i['confidence'])) for i in r.json()['isotopes']]
        if not ids:  # no identifications
            ids = [('', '0')]
        id_report = generate_id_report(ids)
        ET.ElementTree(id_report).write(os.path.join(outputFolder, ff.replace(".n42", ".res")), encoding='utf-8',
                                        xml_declaration=True, method='xml')
