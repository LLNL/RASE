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

import os
from pathlib import Path
import tempfile
import pytest
from src.rase_settings import RaseSettings
from sqlalchemy.orm import close_all_sessions
from src.rase_functions import *
from src.rase_gadras import *
from tools import gadras_clone_detector
from src.table_def import DetectorSchema
import yaml


gadras_root = r"C:\GADRAS"
drf_to_use = r"Handheld\Detective-EX100"



tempdir = Path(tempfile.gettempdir())
outpcf = tempdir/'test.pcf'


@pytest.fixture(scope='session', autouse=True)
def temp_data_dir():
    """Make sure no sample spectra are left after the final test is run"""
    settings = RaseSettings()
    original_data_dir = settings.getDataDirectory()
    settings.setDataDirectory(os.path.join(os.getcwd(),'__temp_test_rase'))
    if os.path.isdir(settings.getSampleDirectory()):
        shutil.rmtree(settings.getSampleDirectory())
        print(f'Deleting sample dir at {settings.getSampleDirectory()}')
    if os.path.isfile(settings.getDatabaseFilepath()):
        os.remove(settings.getDatabaseFilepath())
        print(f'Deleting DB at {settings.getDatabaseFilepath()}')
    if os.path.isdir(Path(settings.getDataDirectory())/'gadras_injections'):
        shutil.rmtree(Path(settings.getDataDirectory())/'gadras_injections')
        print(f'Deleting gadras pcfs at {Path(settings.getDataDirectory())/"gadras_injections"}')
    if os.path.isdir(Path(settings.getDataDirectory())/'converted_gadras'):
        shutil.rmtree(Path(settings.getDataDirectory())/'converted_gadras')
        print(f'Deleting gadras N42s at {Path(settings.getDataDirectory())/"converted_gadras"}')
    yield settings.getDataDirectory()  # anything before this line will be run prior to the tests
    settings = RaseSettings()
    settings.setDataDirectory(original_data_dir)




@pytest.fixture(scope="class", autouse=True)
def db_and_output_folder():
    """Delete and recreate the database between test classes"""
    settings = RaseSettings()
    close_all_sessions()
    dataDir = settings.getDataDirectory()

    os.makedirs(dataDir, exist_ok=True)
    initializeDatabase(settings.getDatabaseFilepath())

    from .test_main import HelpObjectCreation
    hoc = HelpObjectCreation()
    hoc.create_default_workflow()
    hoc.get_default_workflow()
    yield hoc
    close_all_sessions()


@pytest.fixture(scope="function")
def setup_gadras():
    init_gadras(gadras_root)
    with rdrf(drf_to_use) as drf:
        yield drf

class Test_gadras:
    def test_inject(self,qtbot,setup_gadras ):
        result = setup_gadras.inject_source('Cs137')
        print(result)

    def test_inject_from_scenario(self, setup_gadras):
        session = Session()
        scen1 = session.query(Scenario).filter_by(acq_time=60).one()
        for mat in scen1.scen_materials:
            setup_gadras.inject_source(mat.material_name)

    def test_convert_inject_result(self,setup_gadras):
        setup_gadras.convert('Cs137')

#copy detector's spectra list
    def test_create_detector_from_converted(self,setup_gadras):
        spectrum = setup_gadras.get_spectrum('Cs137')
        detector = Detector()
        detector.base_spectra.append(spectrum)

    def test_create_detector_from_converted(self,setup_gadras):
        spectrum = setup_gadras.get_spectrum('Cs137')
        detector = Detector()
        detector.base_spectra.append(spectrum)

    def test_export(self, temp_data_dir, db_and_output_folder):
        dschema = DetectorSchema()
        detector = Session().query(Detector).filter_by(name=db_and_output_folder.get_default_detector_name()).first()
        exportstring = dschema.dump(detector)
        savefilepath = Path(temp_data_dir)/'test_export.yaml'

        with open(savefilepath, 'w') as file:
            yaml.dump(exportstring, file)

    def test_convert_yaml(self,temp_data_dir):
        savefilepath = Path(temp_data_dir) / 'test_export.yaml'
        gadras_clone_detector.clone_detector_yaml(savefilepath, drf_to_use)

    def test_convert_yaml_force(self,temp_data_dir):
        savefilepath = Path(temp_data_dir) / 'test_export.yaml'
        with pytest.raises(SourceNotFoundException):
            gadras_clone_detector.clone_detector_yaml(savefilepath, drf_to_use,force=True)