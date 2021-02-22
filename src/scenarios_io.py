###############################################################################
# Copyright (c) 2018 Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory
#
# Written by J. Chavez, S. Czyz, G. Kosinovsky, V. Mozin, S. Sangiorgio.
# RASE-support@llnl.gov.
#
# LLNL-CODE-819515
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
This module provides a utility to read/write scenarios to/from XML files
"""

# Execute as 'python -m src.scenarios_io' for testing

from pathlib import Path

import declxml as xml
import pandas as pd
import numpy as np
import xml.etree.ElementTree as ET
from sqlalchemy.orm import Session

from src.table_def import Scenario, Session, ScenarioMaterial, Material, \
    ScenarioBackgroundMaterial, Influence, ScenarioGroup


class ScenariosIO:

    def __init__(self, group_name="Imported", group_desc=""):

        self.group_name = group_name
        self.group_desc = group_desc
        self.scenario_group = None

        def dict_to_scenario(state, value):
            session = Session()
            value['id'] = Scenario.scenario_hash(value['acq_time'],
                                    value['scen_materials'],
                                    value['scen_bckg_materials'],
                                    value['influences'])
            q = session.query(Scenario).filter_by(id=value['id']).first()
            if q:
                if self.scenario_group:
                    self.scenario_group.scenarios.append(q)
                return q
            else:
                scenario = Scenario(value['acq_time'],
                                    value['replication'],
                                    value['scen_materials'],
                                    value['scen_bckg_materials'],
                                    value['influences'],
                                    [self.scenario_group])

            return scenario

        def scenario_to_dict(state, value):
            return value.__dict__

        def material_validate(state, value):
            session = Session()
            q = session.query(Material).filter_by(name=value.name).first()
            if q:
                return q
            else:
                session.add(value)
                return value

        def trace(state, value):
            print('Got {} at {}'.format(value, state))
            print(value.__dict__)
            return value

        def influence_validate(state, value):
            session = Session()
            q = session.query(Influence).filter_by(name=value.name).first()
            if q:
                return q
            else:
                session.add(value)
                return value

        self.scenario_hooks = xml.Hooks(
            after_parse=dict_to_scenario,
            before_serialize=scenario_to_dict,
        )

        self.material_hooks = xml.Hooks(
            after_parse=material_validate,
            before_serialize=lambda _, x: x,
        )

        self.influence_hooks = xml.Hooks(
            after_parse=influence_validate,
            before_serialize=lambda _, x: x,
        )

        self.material_processor = xml.user_object('Material', Material, [
            xml.string('BaseMaterialName', alias='name')
        ], alias='material', hooks=self.material_hooks)

        self.sourcematerials_processor = xml.user_object('ScenarioMaterial', ScenarioMaterial, [
            self.material_processor,
            xml.string('fd_mode'),
            xml.floating_point('dose'),
        ], alias='scen_materials')

        self.bkgmaterial_processor = xml.user_object('ScenarioBackgroundMaterial', ScenarioBackgroundMaterial, [
            self.material_processor,
            xml.string('fd_mode'),
            xml.floating_point('dose'),
        ], alias='scen_bckg_materials', required=False)

        self.influence_processor = xml.user_object('Influence', Influence, [
            xml.string('InfluenceName', alias='name')
        ], alias='influences', hooks=self.influence_hooks, required=False)

        self.scenario_processor = xml.dictionary('Scenario', [
            xml.string("id", required=False),
            xml.floating_point("acq_time"),
            xml.integer("replication"),
            xml.array(self.sourcematerials_processor),
            xml.array(self.bkgmaterial_processor),
            xml.array(self.influence_processor)
        ], hooks=self.scenario_hooks)

        self.scenarios_processor = xml.dictionary('Scenarios', [
            xml.array(self.scenario_processor)
        ])

    def scenario_export(self, scenarios: list) -> str:
        s = {"Scenario": scenarios}
        return xml.serialize_to_string(self.scenarios_processor,
                                       s, indent='    ')

    def scenario_import(self, xml_string) -> list:
        self._create_scenario_group()
        imported = xml.parse_from_string(self.scenarios_processor, xml_string)
        return imported['Scenario']

    def _create_scenario_group(self):
        session = Session()
        r = session.query(ScenarioGroup).filter_by(name=self.group_name).first()
        if r:
            self.scenario_group = r
        else:
            self.scenario_group = ScenarioGroup(name=self.group_name, description=self.group_desc)
            session.add(self.scenario_group)

    def xmlstr_from_csv(self, CsvFileName):
        """Returns an xml string from a list of scenarios in CSV format"""
        df = pd.read_csv(CsvFileName)
        return self.xmlstr_from_df(df)

    def xmlstr_from_df(self, df):

        root = ET.Element('Scenarios')

        for index, row in df.iterrows():

            if not np.isnan(row['acq_time']) and not np.isnan(row['replications']):
                scenario = ET.SubElement(root, 'Scenario')
                id_field = ET.SubElement(scenario, 'id')
                id_field.text = ''
                acq_time = ET.SubElement(scenario, 'acq_time')
                acq_time.text = str(row['acq_time'])
                replication = ET.SubElement(scenario, 'replication')
                replication.text = str(row['replications'])
            else:
                return False

            # if source materials are defined
            if not np.isnan(row['s_intensity']):
                scenarioMaterial = ET.SubElement(scenario, 'ScenarioMaterial')
                material = ET.SubElement(scenarioMaterial, 'Material')
                baseMaterialName = ET.SubElement(material, 'BaseMaterialName')
                baseMaterialName.text = row['s_material']
                fdmode = ET.SubElement(scenarioMaterial, 'fd_mode')
                fdmode.text = row['s_fd_mode']
                dose = ET.SubElement(scenarioMaterial, 'dose')
                dose.text = str(row['s_intensity'])

            # if background materials are defined
            if not np.isnan(row['b_intensity']):
                scenarioBkgMaterial = ET.SubElement(scenario, 'ScenarioBackgroundMaterial')
                Bkgmaterial = ET.SubElement(scenarioBkgMaterial, 'Material')
                baseBkgMaterialName = ET.SubElement(Bkgmaterial, 'BaseMaterialName')
                baseBkgMaterialName.text = row['b_material']
                fdmode = ET.SubElement(scenarioBkgMaterial, 'fd_mode')
                fdmode.text = row['s_fd_mode']
                Bkgdose = ET.SubElement(scenarioBkgMaterial, 'dose')
                Bkgdose.text = str(row['b_intensity'])

        tree = ET.ElementTree(root).getroot()
        return ET.tostring(tree, 'utf-8', method='xml')


def main():
    from src.rase_functions import initializeDatabase
    initializeDatabase(str(Path(Path.home(), "test.sql")))
    session = Session()

    m1 = Material(name="TTT")
    m2 = Material(name="NORM")
    s1 = ScenarioMaterial(material=m1, dose=11.2)
    s2 = ScenarioMaterial(material=m1, dose=111)
    sb = ScenarioBackgroundMaterial(material=m2, dose=1.0)
    i = Influence(name="Temperature")
    sc1 = Scenario(30, 100, [s1, s2], [], [])
    sc2 = Scenario(40, 200, [s1], [sb], [i])

    sio = ScenariosIO("Test", "My test")

    print("\n***\nTest export of newly created scenario\n***\n")
    xml_str = sio.scenario_export([sc1, sc2])
    print(xml_str)

    print("\n***\nTest importing back the xml just generated\n***\n")
    ss = sio.scenario_import(xml_str)
    for s in ss:
        print(s.dump_xml())

    print("\n***\nTest exporting a scenario from the db\n***\n")
    prev = session.query(Scenario).first()
    print(prev.dump_xml())
    xml_str = sio.scenario_export([prev])
    print(xml_str)

    print("\n***\nTest importing a scenario that exists in the db\n***\n")
    ss = sio.scenario_import(xml_str)
    print(ss[0].dump_xml())

    print("\n***\nTest importing from a xml string\n***\n")
    xml_str = """<?xml version="1.0" encoding="utf-8"?>
<Scenarios>
    <Scenario>
        <id>E7XX64</id>
        <acq_time>30.0</acq_time>
        <replication>100</replication>
        <ScenarioMaterial>
            <Material>
                <BaseMaterialName>YYY</BaseMaterialName>
            </Material>
            <dose>11.2</dose>
        </ScenarioMaterial>
        <ScenarioMaterial>
            <Material>
                <BaseMaterialName>TTT</BaseMaterialName>
            </Material>
            <dose>111.0</dose>
        </ScenarioMaterial>
    </Scenario>
</Scenarios>"""

    ss = sio.scenario_import(xml_str)
    print(ss[0].dump_xml())

    session.commit()
    session.close()


if __name__ == '__main__':
    main()
