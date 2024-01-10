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
"""
This module defines key functions used in the s-curve
"""

from uncertainties import umath
from lmfit import Model
import numpy as np


def boltzmann_lin(x, a1=1., a2=0., B=0.1, M=0.001):
    return a2 + (a1 - a2) / (1 + np.exp(-(x - M) / B))


def boltzmann_inverse(y, a1=1., a2=0., B=0.1, M=0.001):
    """Inverts and finds the user defined crossing point (default at 80%)"""
    r = (a1 - y)/(y - a2)
    if r <= 0.:
        return np.nan
    else:
        return -B * umath.log(r) + M


def find_max_plot_dose(pid, index=1):
    """
    Does not attempt to fit an S-curve to Pid values that drop below a certain percentage of the max after the max
    has been reached. This is primarily useful in C&C situations, where the C&C will often decrease as dose passes
    critical levels. Recursive function.
    """
    if pid[-index] < 0.7 * max(pid):
        index += 1
        index = find_max_plot_dose(pid, index)
    return index


def get_default_fit_parameters():
    """
    Set initial guesses and fit constraints
    :return: lmfit model params object
    """
    model = Model(boltzmann_lin)
    params = model.make_params()
    params["a1"].set(0.99, min=0.5, max=1.05)
    params["a2"].set(0.01, min=-0.05, max=0.3)
    params["B"].set(0.1, min=1.0e-9)
    params["M"].set(0.001, min=0., max=20.)
    return params


def s_fit(dose, pid, weights=None, params=None):
    """
    Determines fit parameters from an S-curve fit to data
    """
    model = Model(boltzmann_lin)
    if not params:
        params = get_default_fit_parameters()
    r = model.fit(pid, params, weights=weights, method='least_squares', x=dose)
    return r
