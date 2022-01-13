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

from src.table_def import *
from typing import Dict, Type, AnyStr
from abc import ABC, abstractmethod
import numpy as np
from scipy.interpolate import interp1d
from dynamic import dynamic_data_handling, dynamic_models


def is_sorted(l):
    return all(a <= b for a, b in zip(l, l[1:]))


class Path(ABC):
    def __init__(self, pathconfig:Dict, acq_time:float):#auto-fills instance attributes (self.X) based on
        # dictionary. Paths can have arbitrary attributes. Add in final acquisition time because it is necessary for
        # path definition in dynamic scenarios but not included in times list
        for key in pathconfig.keys():
            setattr(self, key, pathconfig[key])
        self.acq_time = acq_time
    @abstractmethod
    def xyz(self,t:float):#t is a float, not an array. This is to make it simpler to add paths, at the cost of being able to do array math slightly faster.
        pass
    def xyz_array(self,ts:Sequence[float]):
        output = np.empty((len(ts),3))
        for i,t in enumerate(ts):
            output[i]=self.xyz(t)
        return output


class StayPutPath(Path):
    def xyz(self,t):
        return self.pos


class OneStepPath(Path):
    def xyz(self,t):
        if t<self.switchtime:
            return self.firstpos
        else:
            return self.secondpos


class NStepPath(Path):
    def __init__(self, pathconfig, acq_time):
        super().__init__(pathconfig, acq_time)#do regular init-from-dict
        assert len(self.times) + 1 == len(self.pos) , "NStepPath should be given N times and N+1 positions. (t=0 for first position is assumed)"
        assert is_sorted(self.times), "NStepPath expects sorted list of times."
        self.nexttime_i = 0

    def xyz(self,t):
        if self.nexttime_i < len(self.times) and t >= self.times[self.nexttime_i]:
            self.nexttime_i += 1
        return self.pos[self.nexttime_i]


class InMotionPath(Path):
    def __init__(self, pathconfig, acq_time):
        super().__init__(pathconfig, acq_time)#do regular init-from-dict
        assert len(self.times) + 1 == len(self.pos) , "InMotionPath should be given N times and N+1 positions. (t=0 for first position is assumed)"
        assert is_sorted(self.times), "InMotionPath expects sorted list of times."
        self.pos_interpolator = interp1d(x=[0] + self.times, y=self.pos, axis=0, fill_value="extrapolate")

    def xyz(self, t):
        if t <= max(self.times):
            return self.pos_interpolator(t)
        else:
            return self.pos[-1]

class ScenarioException(Exception):
    pass

class DynamicScenario:
    path:Path
    sampletimes:np.ndarray
    xyz:np.ndarray
    sources:dict
    replication:int


    def __init__(self, name, scenconfig,  ):
        # scenconfig is config just for this scenario. Eventually can transfer over to DB-stored properties (storing a yaml string for path properties)
        self.name = name
        self.config = scenconfig
        self.acq_time = self.config['acquisition_time']
        self.output_period = self.config['output_period']
        self.n_periods = int(self.acq_time / self.output_period)
        self.output_times = np.arange(start=0, stop=self.n_periods) * self.output_period
        self.replication = self.config['replications']

        path_type = scenconfig['path']['path_type']
        try:
            self.path = [cls for cls in Path.__subclasses__() if cls.__name__==path_type][0](self.config['path'],
                                                                                     self.config['acquisition_time'])
        except AssertionError as e:
            raise ScenarioException(f"Scenario {self.name} path setup error: {str(e)}")
        self.sampletimes = self._sampletimes()
        self.xyz = self._samplexyz()
        self.sources :dict = self.config['sources']


    def _sampletimes(self):
        start = 0  # assumption is we always start at t=0. Test if you are breaking things if you ever remove this assumption.
        stop = self.config['acquisition_time']
        npoints = (stop * self.config['sample_hz'] + 1)
        assert npoints == int(npoints) , f"Scenario {self.name} calculates a non-integer number of points ({npoints}). Fix 'sample_hz' to evenly divide 'acquisition_time'"
        npoints = int(npoints)
        return np.linspace(start=start, stop=stop, num=npoints)

    def _samplexyz(self):
        return self.path.xyz_array(self.sampletimes)

    def sum_to_period(self,generated_spectrum):
        time_points = np.concatenate((self.output_times,[self.output_times[-1]+self.output_period]))
        cumsum = np.cumsum(generated_spectrum, axis=0) / self.config['sample_hz']
        interpolator = interp1d(x=self.sampletimes, y=cumsum, axis=0, fill_value="extrapolate")
        cum_result = interpolator(time_points)
        result = (cum_result[1:] - cum_result[:-1])
        return result




class DynamicIDSet:

    #analogous to IdentificationSet in RASE
    def __init__(self, name, detector:Detector,scenario:DynamicScenario,model_name,model_def):
        self.name = name
        self.data = dynamic_data_handling.DynamicData.get()
        self.detector = detector
        self.scenario : DynamicScenario = scenario
        self.model_name = model_name
        self.model_def = model_def
        self.models = {}
        self.generated_spectra = {}
        self.integrated_spectra = {}
        self.sampled_spectra = {}
        self.sampled_bg = {}
        self.spectra = {}
        self.shortest_bg_time = min(
            [spec.livetime for spec, scale in self.data.get_bg_spectra(self.detector.name, self.scenario.name)])

    def clear(self):
        self.generated_spectra = None
        self.integrated_spectra = None
        self.sampled_spectra = None
        self.sampled_bg = None
        self.spectra = None

    @classmethod
    def from_config(cls,name,data, scenarios, tspec):
        return cls(name = name, detector=data.get_detector(tspec['detector']),
                            scenario=scenarios[tspec['scenario']],
                            model_name=tspec['model'],
                            model_def=tspec['model_def']
                            )

    def make_models(self, force=False):
        for source_name in self.scenario.sources.keys():
            if force:
                self.data.delete_model(detector_name=self.detector.name, material_name=source_name,
                                              model_name=self.model_name, model_def=self.model_def)
                model_store = None
            else:
                model_store = self.data.get_model(detector_name=self.detector.name, material_name=source_name,
                                              model_name=self.model_name, model_def=self.model_def)
            if model_store==None:
                model_class = getattr(dynamic_models,self.model_name)
                model = model_class(self.detector.name,source_name,self.model_def)
                model.build()
                self.data.store_model(model)
            else:
                model = model_store.model
                if not model.built:
                    model.build()
            self.models[source_name] = model

    def generate_spectra(self):
        xyzs = self.scenario.xyz
        for source_name in self.scenario.sources.keys():
            self.generated_spectra[source_name] = self.models[source_name].query(xyzs) #(sources, (locations,energies))

    def integrate_spectra(self):
        assert self.generated_spectra, 'Spectrum generation step not completed.'
        for source_name in self.scenario.sources.keys():
            self.integrated_spectra[source_name] = self.scenario.sum_to_period(self.generated_spectra[source_name]) #(sources, (times,energies))

    def sample_spectra(self):
        assert self.integrated_spectra, "Spectrum integration step not completed."
        for source_name, source_spec in self.scenario.sources.items():
            scen_strength = source_spec['quantity']
            sensitivity = self.data.get_spectra_xyz(self.detector.name,source_name)[0].sensitivity #todo: deal with base spectra xyz with different sensitivities--probably by forcing the whole set to have the same sensitivity
            scaled_counts = self.integrated_spectra[source_name] * (scen_strength)
            scaled_counts[scaled_counts < 0] = 0
            self.sampled_spectra[source_name] = np.random.poisson(scaled_counts[None,:],size=(self.scenario.replication, scaled_counts.shape[0], scaled_counts.shape[1]))



        for bg_spectrum, scale in self.data.get_bg_spectra(self.detector.name, self.scenario.name):
            scaled_counts = (bg_spectrum.counts * (self.scenario.output_period / bg_spectrum.realtime *
                                                   (scale * bg_spectrum.sensitivity)))[:self.detector.chan_count]
            self.sampled_spectra['bg_' + bg_spectrum.material_name] = np.random.poisson(scaled_counts,
                                                        size=(self.scenario.replication, int(self.scenario.n_periods),
                                                              self.detector.chan_count))  # added to periodized spectra

            bg_overall_scale = self.shortest_bg_time / bg_spectrum.realtime * (scale * bg_spectrum.sensitivity)
            scaled_counts_overall = (bg_spectrum.counts * bg_overall_scale)[:self.detector.chan_count]
            self.sampled_bg[bg_spectrum.material_name] = np.random.poisson(scaled_counts_overall)

    def sum_spectra(self):
        self.spectra = np.sum([spectrum for spectrum in self.sampled_spectra.values()], axis=0)
        self.bg_spectrum = np.sum([spectrum for spectrum in self.sampled_bg.values()],axis=0)
        return self.spectra

    def do_all(self):
        self.make_models()
        self.generate_spectra()
        self.integrate_spectra()
        self.sample_spectra()
        self.sum_spectra()

    def get_spectra(self):
        if not self.models:
            self.make_models()
        if not self.generated_spectra:
            self.generate_spectra()
        if not self.integrated_spectra:
            self.integrate_spectra()
        if not (self.sampled_spectra and self.sampled_bg):
            self.sample_spectra()
        if not (self.spectra and self.bg_spectrum):
            self.sum_spectra()
        return self.spectra, self.bg_spectrum




def make_tests(config:dict) -> Dict[str, DynamicIDSet]:
    tests = {}
    scenarios = {}
    for sname, sspec in config['scenarios'].items():
        scenarios[sname] = DynamicScenario(sname,sspec)
    data = dynamic_data_handling.DynamicData.get(config)
    runtests= config.get('run',{}).get('tests')
    if runtests:
        it = zip(runtests,[config['tests'][tname] for tname in runtests])
    else:
        it = config['tests'].items()
    for tname,tspec in it:
        newtest = DynamicIDSet.from_config(tname, data, scenarios, tspec)
        tests[tname]=newtest

    return tests


