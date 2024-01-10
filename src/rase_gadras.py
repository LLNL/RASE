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

from gadpy import gadfunc
import os
from pathlib import Path
from src.rase_settings import RaseSettings
import src.pcf_tools as pcftools
from src.rase_functions import *
from src.spectrum_file_reading import yield_spectra, all_spec

def init_gadras(gadras_root):
    os.add_dll_directory(os.path.join(gadras_root, "Program"))
    gadfunc.initialize(gadras_root)

class SourceNotFoundException(BaseException):
    pass

class rdrf(object):
    def __init__(self,drf_path):
        self.drf_path = drf_path
    def __enter__(self):
        gadfunc.detector_set_current(self.drf_path)
        gadfunc.initialize_inject()
        return self

    def __exit__(self, *args):
        gadfunc.uninitialize_inject()

    def inject_source(self,sourcename):
        injectSetup = gadfunc.InjectSetup(Source=f"{sourcename},100uC", TimeStamp="11-Mar-2014 11:50:21",
                                          BackgroundSuppressionScalar=0, ComputeDoseRateFlag=True)
        outpcf = self.pcf_path(sourcename)
        outpcf.parent.mkdir(parents=True, exist_ok=True)
        try:
            result = gadfunc.run_inject(injectSetup, str(outpcf), 1)
        except Exception as e:
            if "ParseSources failed to load source" in str(e):
                raise SourceNotFoundException(str(e))
            else:
                raise e
        return result

    def pcf_path(self,sourcename):
        settings = RaseSettings()
        outdir = Path(settings.getDataDirectory()) / "gadras_injections" / self.drf_path
        return outdir / f"{sourcename}.pcf"

    def n42_path(self,):
        settings = RaseSettings()
        outdir = Path(settings.getDataDirectory()) / "converted_gadras" / self.drf_path
        return outdir

    def n42s(self):
        return self.n42_path().glob('*.n42')

    def convert(self, sourcename):
        pcftools.PCFtoN42Writer(self.pcf_path(sourcename)).generate_n42(self.n42_path())

    def inject_convert(self,sourcename):
        self.inject_source(sourcename)
        self.convert(sourcename)

    def get_spectrum(self,sourcename):
        n42 = self.n42_path()/f'{sourcename}_0.n42'
        firstroot = get_ET_from_file(n42).getroot()
        return next(yield_spectra(firstroot, all_spec))

    def make_spectrum(self,sourcename):
        self.inject_convert(sourcename)
        return self.get_spectrum(sourcename)