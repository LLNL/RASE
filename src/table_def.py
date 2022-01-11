###############################################################################
# Copyright (c) 2018-2022 Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory
#
# Written by J. Brodsky, J. Chavez, S. Czyz, G. Kosinovsky, V. Mozin, S. Sangiorgio.
# RASE-support@llnl.gov.
#
# LLNL-CODE-819515, LLNL-CODE-829509
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
This module defines persistable objects in sqlalchemy framework
"""

from sqlalchemy import ForeignKey, Column, Integer, String, Float, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm             import relationship, sessionmaker, scoped_session, backref
from sqlalchemy.sql.schema import Table, CheckConstraint
from sqlalchemy import event
import numpy as np
import hashlib
from typing import Set, Sequence, MutableSequence
import json
from src.utils import compress_counts


DB_VERSION_NAME = 'rase_db_v1_2_d4'

Base    = declarative_base()
# Session = sessionmaker()

# This allows access to sessions when multithreading
session_factory = sessionmaker()
Session = scoped_session(session_factory)

# These form many-to-many association tables
scen_infl_assoc_tbl = Table('scenario_influences', Base.metadata,
    Column('scenario_id',    Integer, ForeignKey('scenarios.id')),
    Column('influence_name', String, ForeignKey('influences.name')))

det_infl_assoc_tbl = Table('det_influences', Base.metadata,
    Column('det_name', String, ForeignKey('detectors.name')),
    Column('influence_name', String, ForeignKey('influences.name')))

scen_group_assoc_tbl = Table('scen_group_association', Base.metadata,
    Column('group_id', Integer, ForeignKey('scenario_groups.id',ondelete='cascade')),
    Column('scenario_id', String, ForeignKey('scenarios.id', ondelete='cascade'))
)

class CorrespondenceTableElement(Base):
    __tablename__   = 'correspondence_table_element'
    id              = Column(Integer, primary_key=True)
    isotope         = Column(String)
    corrList1       = Column(String)
    corrList2       = Column(String)
    corr_table_name = Column(String, ForeignKey('correspondence_table.name'))


class CorrespondenceTable(Base):
    __tablename__   = 'correspondence_table'
    name            = Column(String, primary_key=True)
    corr_table_elements     = relationship('CorrespondenceTableElement')
    is_default = Column(Boolean, default=False, nullable=False)

@event.listens_for(CorrespondenceTable, "after_insert")
@event.listens_for(CorrespondenceTable, "after_update")
def _check_default(mapper, connection, target):
    if target.is_default:
        connection.execute(
            CorrespondenceTable.__table__.
                update().
                values(is_default=False).
                where(CorrespondenceTable.name != target.name)
        )


class Material(Base):
    __tablename__ = 'materials'
    name          = Column(String, primary_key=True)
    description   = Column(String)

    def name_no_shielding(self) -> Set[str]:
        return set(self.name.split("-")[0].split("+"))


class Influence(Base):
    __tablename__ = 'influences'
    name          = Column(String, primary_key=True)


class Scenario(Base):
    __tablename__       = 'scenarios'
    id                  = Column(String, primary_key=True)
    acq_time            = Column(Float)
    replication         = Column(Integer)
    # eager loading required by the import/export scenario functions in scenarios_io module
    scen_materials      = relationship('ScenarioMaterial', cascade='all, delete', lazy='joined')
    scen_bckg_materials = relationship('ScenarioBackgroundMaterial', cascade='all, delete', lazy='joined')
    influences          = relationship('Influence', secondary=scen_infl_assoc_tbl, lazy='joined')
    scenario_groups     = relationship('ScenarioGroup', secondary=scen_group_assoc_tbl, backref='scenarios')

    def __init__(self, acq_time=1, replication=1, scen_materials=[], scen_bckg_materials=[], influences=[],
                 scenario_groups=[],
                 description = '', ):
        # id: a hash of scenario parameters, truncated to a 6-digit hex string
        self.id = self.scenario_hash(acq_time, scen_materials, scen_bckg_materials, influences)
        self.acq_time = acq_time
        self.replication = replication  # number of sample spectra to create
        self.influences = influences
        self.scen_materials = scen_materials
        self.scen_bckg_materials = scen_bckg_materials
        self.scenario_groups = scenario_groups

    @staticmethod
    def scenario_hash(acq_time, scen_materials, scen_bckg_materials, influences=[]):
        s = f'{acq_time}' + \
            ''.join(sorted('SRC{}{:9.12f}{}'.format(
                scenMat.material.name, scenMat.dose, scenMat.fd_mode) for scenMat in scen_materials)) + \
            ''.join(sorted('BKGD{}{:9.12f}{}'.format(
                scenMat.material.name, scenMat.dose, scenMat.fd_mode) for scenMat in scen_bckg_materials)) + \
            ''.join(sorted(infl.name for infl in influences))
        try:
            return hashlib.md5(s.encode('utf-8')).hexdigest()[:6].upper()
        except ValueError:
            return hashlib.md5(s.encode('utf-8'),usedforsecurity=False).hexdigest()[:6].upper()

    def get_material_names_no_shielding(self) -> Set[str]:
        return set(name for scenMat in self.scen_materials for name in scenMat.material.name_no_shielding())

    def get_bckg_material_names_no_shielding(self) -> Set[str]:
        return set(name for scenMat in self.scen_bckg_materials for name in scenMat.material.name_no_shielding())


class SampleSpectraSeed(Base):
    __tablename__='sample_spectra_seeds'
    id       = Column(Integer, primary_key=True)
    seed     = Column(Integer)
    scenario = relationship('Scenario')
    detector = relationship('Detector')
    scen_id  = Column(String, ForeignKey('scenarios.id'))
    det_name = Column(String, ForeignKey('detectors.name'))


class ScenarioGroup(Base):
    __tablename__= 'scenario_groups'
    id          = Column(Integer, primary_key=True)
    name        = Column(String, unique=True)
    description = Column(String)


class ScenarioMaterial(Base):
    """many-to-many table between scenario and material"""
    __tablename__ = 'scenario_materials'
    id            = Column(Integer, primary_key=True)
    dose          = Column(Float)
    fd_mode       = Column(String, CheckConstraint("fd_mode IN ('DOSE','FLUX')"))
    material      = relationship('Material', lazy='joined')
    scenario_id   = Column(String, ForeignKey('scenarios.id', ondelete='cascade'))
    material_name = Column(String, ForeignKey('materials.name',ondelete='cascade'))

class ScenarioBackgroundMaterial(Base):
    """many-to-many table between scenario and material"""
    __tablename__ = 'scenario_background_materials'
    id            = Column(Integer, primary_key=True)
    dose          = Column(Float)
    fd_mode       = Column(String, CheckConstraint("fd_mode IN ('DOSE','FLUX')"))
    material      = relationship('Material', lazy='joined')
    scenario_id   = Column(String, ForeignKey('scenarios.id',ondelete='cascade'))
    material_name = Column(String, ForeignKey('materials.name',ondelete='cascade'))

class Detector(Base):
    __tablename__= 'detectors'
    name         = Column(String, primary_key=True)
    description  = Column(String)
    manufacturer = Column(String)
    class_code   = Column(String)
    hardware_version = Column(String)
    instr_id     = Column(String)
    chan_count   = Column(Integer)
    ecal0        = Column(Float)
    ecal1        = Column(Float)
    ecal2        = Column(Float)
    ecal3        = Column(Float)
    includeSecondarySpectrum = Column(Boolean)
    secondary_type = Column(Integer)    # 0=long_back from scen, 1=long_back from basespec, 2=internal_source, 3=long_back from file
    replay_name  = Column(String, ForeignKey('replays.name'))
    replay       = relationship('Replay')
    results_translator_name  = Column(String, ForeignKey('resultsTranslators.name'))
    resultsTranslator       = relationship('ResultsTranslator')
    influences          = relationship('Influence', secondary=det_infl_assoc_tbl, lazy='joined', backref='detectors')
    base_spectra : MutableSequence = relationship('BaseSpectrum')
    base_spectra_xyz : MutableSequence = relationship('BaseSpectrumXYZ')
    bckg_spectra = relationship('BackgroundSpectrum')


class DetectorInfluence(Base):
    __tablename__   = 'detector_influences'
    id              = Column(Integer, primary_key=True)
    infl_0          = Column(Float)
    infl_1          = Column(Float)
    infl_2          = Column(Float)
    fixed_smear     = Column(Float)
    linear_smear    = Column(Float)
    degrade_infl0   = Column(Float)
    degrade_infl1   = Column(Float)
    degrade_infl2   = Column(Float)
    degrade_f_smear = Column(Float)
    degrade_l_smear = Column(Float)
    influence       = relationship('Influence', backref=backref("detector_influences", cascade="all,delete"))
    influence_name  = Column(String, ForeignKey('influences.name'))


class Replay(Base):
    __tablename__  = 'replays'
    name           = Column(String, primary_key=True)
    exe_path       = Column(String)
    is_cmd_line    = Column(Boolean)
    settings       = Column(String)
    n42_template_path   = Column(String)
    input_filename_suffix = Column(String)


class ResultsTranslator(Base):
    __tablename__  = 'resultsTranslators'
    name           = Column(String, primary_key=True)
    exe_path       = Column(String)
    is_cmd_line    = Column(Boolean)
    settings       = Column(String)

class Spectrum_mixin():
    id            = Column(Integer, primary_key=True)
    filename      = Column(String)
    _counts    = Column(String)
    realtime      = Column(Float)
    livetime      = Column(Float)

    @declared_attr
    def material(cls): return relationship('Material')

    @declared_attr
    def detector_name(cls):
        return Column(String, ForeignKey('detectors.name', ondelete='cascade'))

    def is_spectrum_float(self):
        """Checks if spectrum has floats in it or not"""
        for binval in self._counts.split(','):
            c = float(binval)
            if c and (c < 1 or int(c) % c):
                return True
        return False


    @declared_attr
    def material_name(cls): return Column(String, ForeignKey('materials.name', ondelete='cascade'))

    def as_json(self, detector):
        return json.dumps([{"title": self.material_name,
                            "livetime": self.livetime,
                            "realtime": self.realtime,
                            "xeqn": [detector.ecal0, detector.ecal1, detector.ecal2],
                            "y": [float(c) for c in self._counts.split(',')],
                            "yScaleFactor": 1,
                            }])

    @property
    def counts(self):
        return np.array([float(c) for c in self._counts.split(",")])
    @counts.setter
    def counts(self, value):
        self._counts = ','.join([str(c) for c in value])

    #legacy
    def get_counts_as_np(self)->Sequence[float]:
        return np.array([float(c) for c in self._counts.split(",")])

    #legacy
    def get_counts_as_str(self):
        if self.is_spectrum_float():
            return ' '.join([str(float(c)) for c in self._counts.split(",")])
        else:
            return ' '.join([str(int(float(c))) for c in self._counts.split(",")])


    def get_compressed_counts_as_str(self):
        if self.is_spectrum_float():
            return ' '.join('{:f}'.format(x) for x in
                            compress_counts(np.array([float(c) for c in self._counts.split(",")])))
        else:
            return ' '.join('{:d}'.format(x) for x in
                            compress_counts(np.array([int(float(c)) for c in self._counts.split(",")])))

class BaseSpectrum(Spectrum_mixin,Base):
    __tablename__ = 'base_spectra'
    sensitivity   = Column(Float)  # aka static efficiency

class BaseSpectrumXYZ(Spectrum_mixin,Base):
    __tablename__ = 'base_spectra_xyz'
    sensitivity   = Column(Float)  # aka static efficiency
    x             = Column(Float)  # units of cm
    y             = Column(Float)  # units of cm
    z             = Column(Float)  # units of cm

class BackgroundSpectrum(Spectrum_mixin,Base):
    __tablename__ = 'background_spectra'


class MaterialNameTranslation(Base):
    __tablename__ = 'material_translations'
    name          = Column(String, primary_key=True)
    toName        = Column(String)


from sqlalchemy import PickleType, UniqueConstraint

def are_elements_equal(x, y):
    return x == y

class DynamicModelStorage(Base):
    __tablename__ = 'dynamic_models'
    id = Column(Integer, primary_key=True)
    detector_name = Column(String)
    material_name = Column(String)
    model_name    = Column(String)
    model_def     = Column(JSON)
    model = Column(PickleType(comparator=are_elements_equal))
    __table_args__ = (UniqueConstraint('detector_name', 'material_name', 'model_name', 'model_def',
                                       name='_customer_location_uc'),
                      )

# class ProxySource(Base): #removed for the moment, since I am trying to specify proxies in the train set instead
#     __tablename__ = 'proxy_sources'
#
#     material_name = Column(String,primary_key=True)
#     proxy         = Column(JSON) #dict

