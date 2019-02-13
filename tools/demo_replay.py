#!/usr/bin/env python3
#
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
A dummy isotope identification algorithm that output identification results based
on a random selection within a list of possible results
"""

# To generate a windows executable version:
# python -m PyInstaller -a -y -F --clean --noupx --distpath ..\dist --workpath ..\build demo_replay.py

import sys

__author__ = 'sangiorgio1'

import os
import xml.etree.ElementTree as ET
from random import randint


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


def random_ids():
    isotopes = ['HEU', 'Ga-67', 'Cs-137', 'WGPu', 'K-40', 'U-235', 'U-238', 'Tc-99m', 'Tl-201']
    identifications = [(isotopes[randint(0, len(isotopes) - 1)], str(randint(0, 10))) for i in range(0, randint(1, 3))]
    return identifications


def generate_id_report(scenario):
    id_report = ET.Element('IdentificationResults')

    for id_iso, id_conf in random_ids():
        id_result = ET.SubElement(id_report, 'Identification')
        id_name = ET.SubElement(id_result, 'IDName')
        id_name.text = id_iso
        id_confidence = ET.SubElement(id_result, 'IDConfidence')
        id_confidence.text = id_conf
        # id_reported = SubElement(id_result, 'Reported')
        # id_reported.text = 'true'
    indent(id_report)
    return id_report


def get_file_list(in_folder):
    return [f for f in os.listdir(in_folder) if f.endswith(".n42")]


if __name__ == '__main__':

    if len(sys.argv) < 3:
        print("ERROR: Need input and output folders!")
        sys.exit(1)

    inputFolder = sys.argv[1]
    outputFolder = sys.argv[2]

    for ff in get_file_list(inputFolder):
        # Passing the filename as scenario
        id_report = generate_id_report(ff)
        # print (prettify(id_report))

        ET.ElementTree(id_report).write(os.path.join(outputFolder, ff.replace(".n42", ".res")), encoding='utf-8',
                                        xml_declaration=True, method='xml')
