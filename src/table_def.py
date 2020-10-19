###############################################################################
# Copyright (c) 2018 Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory
#
# Written by J. Chavez, S. Czyz, G. Kosinovsky, V. Mozin, S. Sangiorgio.
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
This module defines persistable objects in sqlalchemy framework
"""

from sqlalchemy import ForeignKey, Column, Integer, String, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm             import relationship, sessionmaker, scoped_session
from sqlalchemy.sql.schema import Table, CheckConstraint
from sqlalchemy import event
import numpy as np
import hashlib
from typing import Set
from src.utils import compress_counts

DB_VERSION_NAME = 'rase_db_v1_1'

Base    = declarative_base()
# Session = sessionmaker()

# This allows access to sessions when multithreading
session_factory = sessionmaker()
Session = scoped_session(session_factory)

# These form many-to-many association tables
scen_infl_assoc_tbl = Table('scenario_influences', Base.metadata,
    Column('scenario_id',    Integer, ForeignKey('scenarios.id')),
    Column('influence_name', String, ForeignKey('influences.name')))

scen_group_assoc_tbl = Table('scen_group_association', Base.metadata,
    Column('group_id', Integer, ForeignKey('scenario_groups.id')),
    Column('scenario_id', String, ForeignKey('scenarios.id'))
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
    associated_spectrum_counter = Column(Integer)

    def name_no_shielding(self) -> Set[str]:
        return set(self.name.split("-")[0].split("+"))
    def increment_associated_spectrum_counter(self):
        self.associated_spectrum_counter = self.associated_spectrum_counter + 1
    def decrement_associated_spectrum_counter(self):
        self.associated_spectrum_counter = self.associated_spectrum_counter - 1


class Influence(Base):
    __tablename__ = 'influences'
    name          = Column(String, primary_key=True)


class IdentificationSet(Base):
    """set of id reports based on a scenario and a detector"""
    __tablename__ = 'identification_sets'
    id            = Column(Integer, primary_key=True)
    scenario      = relationship('Scenario')
    replay        = relationship('Replay')
    detector      = relationship('Detector')
    id_reports    = relationship('IdentificationReport', cascade='save-update, merge, delete, delete-orphan')
    scen_id       = Column(String, ForeignKey('scenarios.id'))
    repl_name     = Column(String, ForeignKey('replays.name'))
    det_name       = Column(String, ForeignKey('detectors.name'))


class IdentificationReport(Base):
    """single output of the replay tool given a single input spectrum"""
    __tablename__ = 'identification_reports'
    id            = Column(Integer, primary_key=True)
    filenum       = Column(Integer)
    results       = relationship('IdentificationResult', cascade='save-update, merge, delete')
    id_set_id     = Column(Integer, ForeignKey('identification_sets.id'))


class IdentificationResult(Base):
    """one line of the replay output"""
    __tablename__ = 'identification_results'
    id            = Column(Integer, primary_key=True)
    name          = Column(String)
    confidence    = Column(Float)
    id_rept_id    = Column(Integer, ForeignKey('identification_reports.id'))


class Scenario(Base):
    __tablename__       = 'scenarios'
    id                  = Column(String, primary_key=True)
    acq_time            = Column(Float)
    replication         = Column(Integer)
    # eager loading required by the import/export scenario functions in scenarios_io module
    scen_materials      = relationship('ScenarioMaterial', cascade='save-update, merge, delete', lazy='joined')
    scen_bckg_materials = relationship('ScenarioBackgroundMaterial', cascade='save-update, merge, delete', lazy='joined')
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
            ''.join(sorted('{}{:9.12f}{}'.format(
                scenMat.material.name, scenMat.dose, scenMat.fd_mode) for scenMat in scen_materials)) + \
            ''.join(sorted('{}{:9.12f}{}'.format(
                scenMat.material.name, scenMat.dose, scenMat.fd_mode) for scenMat in scen_bckg_materials)) + \
            ''.join(sorted(infl.name for infl in influences))
        return hashlib.md5(s.encode('utf-8')).hexdigest()[:6].upper()

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
    scenario_id   = Column(String, ForeignKey('scenarios.id'))
    material_name = Column(String, ForeignKey('materials.name'))

class ScenarioBackgroundMaterial(Base):
    """many-to-many table between scenario and material"""
    __tablename__ = 'scenario_background_materials'
    id            = Column(Integer, primary_key=True)
    dose          = Column(Float)
    fd_mode       = Column(String, CheckConstraint("fd_mode IN ('DOSE','FLUX')"))
    material      = relationship('Material', lazy='joined')
    scenario_id   = Column(String, ForeignKey('scenarios.id'))
    material_name = Column(String, ForeignKey('materials.name'))

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
    secondary_type = Column(Integer)    # 1=long_background, 2=internal_calibration
    replay_name  = Column(String, ForeignKey('replays.name'))
    replay       = relationship('Replay')
    results_translator_name  = Column(String, ForeignKey('resultsTranslators.name'))
    resultsTranslator       = relationship('ResultsTranslator')
    influences   = relationship('DetectorInfluence')
    base_spectra = relationship('BaseSpectrum')
    bckg_spectra = relationship('BackgroundSpectrum')


class DetectorInfluence(Base):
    __tablename__  = 'detector_influences'
    id             = Column(Integer, primary_key=True)
    infl_0         = Column(Float)
    infl_1         = Column(Float)
    infl_2         = Column(Float)
    influence      = relationship('Influence')
    detector_name  = Column(String, ForeignKey('detectors.name'))
    influence_name = Column(String, ForeignKey('influences.name'))


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


class BaseSpectrum(Base):
    __tablename__ = 'base_spectra'
    id            = Column(Integer, primary_key=True)
    filename      = Column(String)
    material      = relationship('Material')
    baseCounts    = Column(String)
    realtime      = Column(Float)
    livetime      = Column(Float)
    rase_sensitivity   = Column(Float)  # aka static efficiency
    flux_sensitivity   = Column(Float)
    detector_name = Column(String, ForeignKey('detectors.name'))
    material_name = Column(String, ForeignKey('materials.name'))

    def get_counts_as_np(self):
        if self.is_spectrum_float():
            return np.array([float(c) for c in self.baseCounts.split(",")])
        else:
            return np.array([int(float(c)) for c in self.baseCounts.split(",")])

    def is_spectrum_float(self):
        """Checks if spectrum has floats in it or not"""
        for binval in self.baseCounts.split(','):
            c = float(binval)
            if c and (c < 1 or int(c) % c):
                return True
        return False

# TODO: Secondary background currently does not have flux/dose sensitivity parameters, it is a direct copy/paste from
#  the base spectra
class BackgroundSpectrum(Base):
    __tablename__ = 'background_spectra'
    id            = Column(Integer, primary_key=True)
    filename      = Column(String)
    material      = relationship('Material')
    baseCounts    = Column(String)
    realtime      = Column(Float)
    livetime      = Column(Float)
    detector_name = Column(String, ForeignKey('detectors.name'))
    material_name = Column(String, ForeignKey('materials.name'))

    def get_counts_as_np(self):
        if self.is_spectrum_float():
            return np.array([float(c) for c in self.baseCounts.split(",")])
        else:
            return np.array([int(float(c)) for c in self.baseCounts.split(",")])


    def get_counts_as_str(self):
        if self.is_spectrum_float():
            return ' '.join([str(float(c)) for c in self.baseCounts.split(",")])
        else:
            return ' '.join([str(int(float(c))) for c in self.baseCounts.split(",")])


    def get_compressed_counts_as_str(self):
        if self.is_spectrum_float():
            return ' '.join('{:f}'.format(x) for x in
                            compress_counts(np.array([float(c) for c in self.baseCounts.split(",")])))
        else:
            return ' '.join('{:d}'.format(x) for x in
                            compress_counts(np.array([int(float(c)) for c in self.baseCounts.split(",")])))

    def is_spectrum_float(self):
        """Checks if spectrum has floats in it or not"""
        for binval in self.baseCounts.split(','):
            c = float(binval)
            if c and (c < 1 or int(c) % c):
                return True
        return False


class MaterialNameTranslation(Base):
    __tablename__ = 'material_translations'
    name          = Column(String, primary_key=True)
    toName        = Column(String)