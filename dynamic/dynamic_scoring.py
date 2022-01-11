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
from typing import Dict, Type
from abc import ABC, abstractmethod
import numpy as np
from scipy.interpolate import interp1d
from dynamic import dynamic_data_handling, dynamic_models, dynamic_scenarios


def make_scores(config) -> Dict[str, 'Score']:
    configscores = config.get('scores')
    if configscores:
        scores={}
        runscores = config.get('run', {}).get('scores')
        if runscores:
            it = zip(runscores,[configscores[sname] for sname in runscores])
        else:
            it = configscores.items()
        for sname, score_def in it:
            score_class = [cls for cls in Score.__subclasses__() if cls.__name__ == score_def['scorer']]
            if not score_class:
                raise ValueError("Scorer class defined by user does not exist")
            else:
                scores[sname] = score_class[0](score_def)
        return scores

class Score(ABC):

    def __init__(self, score_def:dict):
        self.score_def = score_def
        self.test_xyzs = score_def.get('test_points') #pull out this variable for special treatment since it's always necessary


    @abstractmethod
    def single_spectrum_FOM(self, truth, prediction) -> Float:
        pass

    @abstractmethod
    def combine_FOMs(self, list_of_FOMs):
        #this exists to be overridden. What's the best way to combine the FOMs of separate points?
        pass

    def score(self, model):
        #score function handles the behavior every scorer should replicate: pull appropriate spectra, query the model, etc.

        # if a scorer is attached to a set of tests that draw from different scenarios, it is not unreasonable to
        # have a different set of spectra available. This is an edge case that should really only happen if the user
        # defines no tests to look at and no specific test points.
        if self.test_xyzs is None:
            test_xyzs = np.array([[spec.x, spec.y, spec.z] for spec in model.spectra])
        else:
            test_xyzs = self.test_xyzs


        test_spectra = [spec for spec in model.spectra if [spec.x, spec.y, spec.z] in test_xyzs]
        test_xyzs = [[spec.x,spec.y,spec.z] for spec in test_spectra ] # reorder test_xyzs to match order of test_spectra

        if len(test_spectra) != len(test_xyzs):
            raise ValueError('requested test at points not present in the model')
            # If we ask for bad test points, we should fail noisily instead of quietly ignore the problem

        foms = np.full(len(test_xyzs),np.nan)

        predictions = model.query(test_xyzs) * np.array([spectrum.livetime for spectrum in test_spectra])[:,None]
        truths = np.array([spectrum.counts[:model.detector.chan_count] for spectrum in test_spectra])
        for i in range(len(truths)):
            foms[i] = self.single_spectrum_FOM(truths[i], predictions[i])
        return self.combine_FOMs(foms)



class ScoreMaxDifference(Score):

    def single_spectrum_FOM(self, truth, prediction):
        abs_difference = np.abs(truth - prediction)
        return np.max(abs_difference)

    def combine_FOMs(self, list_of_FOMs):
        return np.max(list_of_FOMs)


class ScoreMaxDifferenceDivTotalCounts(ScoreMaxDifference, Score): # inheriting from Score to maintain subclass

    def single_spectrum_FOM(self, truth, prediction):
        abs_difference = np.abs(truth - prediction)
        return np.max(abs_difference)/sum(truth)


class ScoreMaxDifferenceAcrossROI(ScoreMaxDifference, Score):

    def single_spectrum_FOM(self, truth, prediction):
        first = self.score_def['roi']['first']
        last = self.score_def['roi']['last']
        abs_difference = np.abs(truth[first:last] - prediction[first:last])
        return np.max(abs_difference)
