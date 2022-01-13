###############################################################################
# Copyright (c) 2018-2022 Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory
#
# Written by J. Brodsky, S. Czyz
# RASE-support@llnl.gov.
#
# LLNL-CODE-829509
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

from src import rase_functions as rf
from src.table_def import *
import re
import src.base_building_algos as bba
import os
from pathlib import Path
from typing import Tuple
from itertools import tee

class Bunch:
    def __init__(self, **kwds):
        self.__dict__.update(kwds)

def get_xyz(position_ET):
    xyz=[]
    for q in ['x','y','z']:
        element = rf.requiredElement(q,position_ET)
        if element.text:
            xyz.append(float(element.text.strip()))
        else:
            xyz.append(0)
    return xyz


class DynamicData:
    _instance = None
    '''This is a data access class that groups together the base spectra (stored in the DB) along with the GPs, etc.'''
    #todo: extend to multiple detectors in yaml?
    def __init__(self, config:dict):
        self.config = config
        found_db = self.connect_to_db()
        DynamicData._instance = self
        self.create_scenario()
        # self.create_spectra()


    @staticmethod
    def get(config=None) -> 'DynamicData':
        if not DynamicData._instance:
            raise RuntimeError('DynamicData uninitialized. Initialize DynamicData(config) before reaching this part of the code')
        return DynamicData._instance

    def connect_to_db(self,): #returns true if DB already existed, false otherwise
        self.db_file_location = self.config.get('db_file_location')
        if self.db_file_location and not os.path.isdir(os.path.dirname(os.path.abspath(self.db_file_location))):
            os.makedirs(os.path.dirname(os.path.abspath(self.db_file_location)))
        if not self.db_file_location:
            import tempfile
            self.db_file_location = f'{tempfile._get_default_tempdir()}/{next(tempfile._get_candidate_names())}'
        try:
            return rf.initializeDatabase(self.db_file_location) # sets up global Session variable to access DB. Creates DB if it doesn't already exist, and then returns false. If DB exists, returns true
        except:
            raise FileNotFoundError(f"Cannot initialize database at {self.db_file_location}! Exiting.")

    def create_detector(self, detector_name, clear:Boolean = True):
        '''
        Read an textfile that fills in the various qualities of a detector in the database
        FIXME: In the future make it so these are read from the .n42 files directly
        '''
        session=Session()
        if clear: session.query(Detector).filter_by(name=detector_name).delete()
        detconf = self.config['detectors'][detector_name]
        det = Detector()
        det.name = detector_name
        det.description = detconf['description']
        det.manufacturer = detconf['manufacturer']
        det.class_code = detconf['class_code']
        det.hardware_version = detconf['hardware_version']
        det.instr_id = detconf['instr_id']
        det.chan_count = detconf['chan_count']
        det.includeSecondarySpectrum = detconf['include_secondary_spectrum']
        if det.includeSecondarySpectrum:
            det.secondary_type = rf.secondary_type[detconf['secondary_type']]

        session.add(det)
        session.commit()


    def create_spectra(self, detector_name=None, clear=True):
        session = Session()
        # session.query(Material).delete()
        if not detector_name:
            detector_name = next(iter(self.config['detectors']))
        if clear:
            session.query(BaseSpectrumXYZ).filter_by(detector_name=detector_name).delete()
            session.query(BackgroundSpectrum).filter_by(detector_name=detector_name).delete()
        detector = self.get_detector(detector_name)
        spectra_config = self.config['detectors'][detector_name]['spectra']
        sharedobject = Bunch(isBckgrndSave=False, bkgndSpectrumInFile=False)
        subtraction_ETs={}

        for name,bg in spectra_config['backgrounds'].items():
            BG_ET = bba.get_ET_from_file(bg['path'])
            bkgmat = self.get_material(name=name)
            try:
                v = rf.parseRadMeasurement(BG_ET, bg['path'], sharedobject, '', False)
            except:
                v = rf.parseMeasurement(BG_ET, bg['path'], sharedobject, '',requireRASESen=False)
            quantity = float(rf.requiredElement('Quantity', BG_ET).text.strip())
            BgSpec = BackgroundSpectrum(material=bkgmat, filename=bg['path'],
                                        realtime=v[2],
                                        livetime=v[3],
                                        sensitivity=1 / quantity,
                                        _counts=v[0],
                                        )
            detector.bckg_spectra.append(BgSpec)

        for name,source in spectra_config['sources'].items():
            mat = self.get_material(name=name)

            sourcedir = Path(source['directory'])
            if '*' not in sourcedir.name: fileiter = sourcedir.iterdir()
            else: fileiter = sourcedir.parent.glob(sourcedir.name)

            fileiter, check = tee(fileiter)
            try: next(check)
            except StopIteration:
                raise RuntimeError(f'Source {name} has no files in the specified directory {sourcedir}')

            for filename in fileiter:
                filepath = os.path.join(source['directory'],filename)
                sharedobject = Bunch(isBckgrndSave=False, bkgndSpectrumInFile=False)
                ET = bba.get_ET_from_file(filepath)
                try:
                    v = rf.parseRadMeasurement(ET, filepath, sharedobject, '', requireRASESens=False)
                except:
                    v = rf.parseMeasurement(ET, filepath, sharedobject, '',requireRASESen=False)

                try:
                    detector.ecal0 = v[1][0]
                    detector.ecal1 = v[1][1]
                    detector.ecal2 = v[1][2]
                    detector.ecal3 = v[1][3]
                except IndexError:
                    pass

                position = rf.requiredElement('Position',ET)
                x,y,z = get_xyz(position)
                quantity = float(rf.requiredElement('Quantity',ET).text.strip())
                baseSpectrum = BaseSpectrumXYZ(material=mat,
                                               filename=filepath,
                                               realtime=v[2],
                                               livetime=v[3],
                                               sensitivity=1/quantity,
                                               _counts=v[0],
                                               x=x, y=y, z=z)
                detector.base_spectra_xyz.append(baseSpectrum)

        session.commit()

    def create_scenario(self,clear:Boolean = True):
        session = Session()
        if clear:
            session.query(Scenario).delete()
            session.query(ScenarioMaterial).delete()
            session.query(ScenarioBackgroundMaterial).delete()
            session.query(ScenarioGroup).delete()
            session.commit()
            # matDelete.delete()
            # bckgMatDelete.delete()
            # scenDelete.delete()
        # for scen in list(self.config['scenarios']):
        #     scengroup = session.query(ScenarioGroup).filter_by(name=scen).one_or_none()
        #     if not scengroup:
        #         scengroup = ScenarioGroup(name=scen, description='')
        #         session.add(scengroup)
        for name, scenario_config in self.config['scenarios'].items():
            mats = [self.get_material(p) for p in scenario_config['sources'].keys()]
            doses = [c['quantity'] for c in scenario_config['sources'].values()]
            if scenario_config.get('backgrounds'):
                bg_mats = [self.get_material(p) for p in scenario_config['backgrounds'].keys()]
                bg_doses = [p['quantity'] for p in scenario_config['backgrounds'].values()]
            else:
                raise ValueError(
                    'DRASE currently requires all scenarios to have a background specified.')  # TODO: get DRASE to work with no backgrounds specified

            ScenarioMaterials = [ScenarioMaterial(dose=d, material=m) for m, d in zip(mats, doses)]
            BgScenarioMaterials = [ScenarioBackgroundMaterial(dose=d, material=m) for m, d in zip(bg_mats, bg_doses)]

            scen = Scenario(scenario_config['acquisition_time'], scenario_config['replications'], ScenarioMaterials,
                            BgScenarioMaterials, [])  # acq time, replications
            existingscen = session.query(Scenario).filter_by(id=scen.id).one_or_none()
            if existingscen:
                scen = existingscen
            scengroup = ScenarioGroup(name=name, description='', scenarios=[scen, ])
            session.add(scengroup)
        session.commit()

    def get_material(self, name, create=True) -> Material :
        session=Session()
        mat = session.query(Material).filter_by(name=name).one_or_none()
        if not mat:
            if create:
                mat = Material(name=name)
            else:
                raise ValueError('Materials not found in DB and couldn\'t be created')
        return mat

    def get_scenariomaterial(self, name, create=True):
        session=Session()
        mat = session.query(Material).filter_by(name=name).one_or_none()
        if not mat:
            if create:
                self.create_spectra()
                return self.get_material(name,create=False)
            else:
                raise ValueError('Materials not found in DB and couldn\'t be created')
        return mat


    def get_scenario(self,name):
        session=Session()
        scengrp:ScenarioGroup = session.query(ScenarioGroup).filter_by(name=name).one_or_none()
        if not scengrp:
            self.create_scenario()
            scengrp = session.query(ScenarioGroup).filter_by(name=name).one()
        scen = scengrp.scenarios[0]
        return scen

    def get_detector(self,name):
        session=Session()
        det = session.query(Detector).filter_by(name=name).one_or_none()
        if not det:
            self.create_detector(name)
            det = session.query(Detector).filter_by(name=name).one()
        return det

    def get_spectra_xyz(self, detector_name, material_name, create:Boolean=True):
        session = Session()
        detector = self.get_detector(detector_name)
        spectra = session.query(BaseSpectrumXYZ).filter_by(detector_name=detector.name,
                                                               material_name=material_name).all()
        if not spectra:
            if create:
                self.create_spectra(detector_name)
                spectra = self.get_spectra_xyz(detector_name, material_name, create=False)
            else:
                raise ValueError('Spectra not found in DB and couldn\'t be created')

        return spectra

    def store_model(self,model):
        session=Session()
        storedmodel = DynamicModelStorage()
        storedmodel.material_name = model.material.name
        storedmodel.detector_name = model.detector.name
        storedmodel.model_name = model.__class__.__name__
        storedmodel.model_def = model.model_def
        storedmodel.model = model
        session.add(storedmodel)
        session.commit()

    def get_model(self,detector_name, material_name, model_name, model_def):
        session=Session()
        result = session.query(DynamicModelStorage).filter_by(detector_name=detector_name,
                                                              material_name=material_name,model_name=model_name,
                                                              model_def=model_def).one_or_none()
        return result

    def delete_model(self,detector_name, material_name, model_name, model_def):
        session = Session()
        session.query(DynamicModelStorage).filter_by(detector_name=detector_name,
                                                              material_name=material_name, model_name=model_name,
                                                              model_def=model_def).delete()

    def get_bg_spectra(self,detector_name, scenario_name,create=True) -> Sequence[Tuple[BackgroundSpectrum,float]]:
        session = Session()
        detector = self.get_detector(detector_name)
        scenario = self.get_scenario(scenario_name)
        bkg_spectrum = [(session.query(BackgroundSpectrum)
                         .filter_by(detector_name=detector.name,
                                    material_name=scenMaterial.material_name)).first()
                        for scenMaterial in scenario.scen_bckg_materials
                        ]
        scales = [mat.dose for mat in scenario.scen_bckg_materials]
        # if None in bkg_spectrum:
        if create:
            if create:
                self.create_spectra(detector_name=detector.name)
                return self.get_bg_spectra(detector_name, scenario_name, create=False)
            else:
                raise ValueError('Spectra not found in DB and couldn\'t be created')
        # if the detector has an internal calibration source, it needs to be added with special treatment
        # NOT IMPLEMENTED RIGHT NOW, so detectors with secondary spectra of different types should replicate those
        # in the template, not ask DRASE to handle
        # if detector.includeSecondarySpectrum and detector.secondary_type == 2:
        #     secondary_spectrum = (session.query(BackgroundSpectrum).filter_by(detector_name=detector.name)).first()
        #     bkg_spectrum.append(secondary_spectrum)
        return zip(bkg_spectrum,scales)





