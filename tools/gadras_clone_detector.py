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

import yaml
from src.table_def import DetectorSchema, Detector
from src import rase_gadras

def clone_detector_yaml(yaml_path, drf_path, gadras_path=r"C:\GADRAS",  force=False):
    '''
    Function that will extract source names from an exported detector yaml, inject those sources using GADRAS, and
    convert the GADRAS results to N42 base spectra containing RASE_senstivity tags. Output N42s will be placed in the
    RASE data directory / converted_gadras / drf_path and can be loaded into RASE as base spectra for a new detector.
    @param yaml_path: path to exported detector yaml. Generate this using the RASE gui -> detector window -> Export
    @param drf_path: path within the GADRAS root to the DRF file appropriate for the detector you wish to simulated
    @param gadras_path: path to the GADRAS root.
    @param force: if True, every source name in the detector yaml must be recognizable by GADRAS.
    If False, source names that GADRAS does not recognize will be skipped without error.
    @return:
    '''
    rase_gadras.init_gadras(gadras_path)
    with open(yaml_path, 'r') as file:
        importdict = yaml.safe_load(file)
    dschema = DetectorSchema()
    detector : Detector = dschema.load(importdict,transient=True)
    with rase_gadras.rdrf(drf_path) as rg:
        for basespec in detector.base_spectra:
            try:
                rg.make_spectrum(basespec.material.name)
            except rase_gadras.SourceNotFoundException as e:
                if force:
                    raise e
                else: pass
