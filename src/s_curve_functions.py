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
This module defines key functions used in the s-curve
"""

from uncertainties import ufloat, correlated_values, umath  # correlated_values must be imported for inversion
from lmfit import Model
import numpy as np


def boltzmann_log(x, a1=1., a2=0., B=1., Q=1):
    return a2 + (a1 - a2) / (1 + Q * np.exp(-np.log(x) * B))


def boltzmann_lin(x, a1=1., a2=0., B=1., Q=1):
    return a2 + (a1 - a2) / (1 + Q * np.exp(-x * B))


def boltzmann_log_alt(x, a1=1., a2=0., B=1., Q=1):
    """Alternative fitting (1/B instead of B) that sometimes helps the plotter converge.
        Used only in cases where the original approach fails"""
    return a2 + (a1 - a2) / (1 + Q * np.exp(-np.log(x) * 1 / B))


def boltzmann_lin_alt(x, a1=1., a2=0., B=1., Q=1):
    """Alternative fitting (1/B instead of B) that sometimes helps the plotter converge.
        Used only in cases where the original approach fails"""
    return a2 + (a1 - a2) / (1 + Q * np.exp(-x * 1 / B))


def boltzmann_inverse(y, a1=1., a2=0., B=1., Q=1, logfit=True, altfit=0):
    """Inverts and finds the user defined crossing point (default at 80%)"""
    try:
        y = y.nominal_value
        if logfit:
            if altfit == 1:
                b_inv = np.power((1 / Q * ((a1 - y) / (y - a2))), -B)
            else:
                b_inv = np.power((1 / Q * ((a1 - y) / (y - a2))), -1 / B)
        else:
            if altfit == 1:
                b_inv = -B * umath.log(1 / Q * ((a1 - y) / (y - a2)))
            else:
                b_inv = -1 / B * umath.log(1 / Q * ((a1 - y) / (y - a2)))
    except:
        print('Failed to invert')
        b_inv = []
    return b_inv


def thresh_mark(a1=1., a2=0., B=1., Q=1, id_mark=0.8, logfit=True, altfit=0):
    """
    Find at what dose rate you achieve 80% PID, as determined by the S-curve
    """
    thresh_mark_new = boltzmann_inverse(ufloat(id_mark, 0), a1=a1, a2=a2, B=B, Q=Q, logfit=logfit, altfit=altfit)
    if not thresh_mark_new:
        thresh_mark_nom = 0
        thresh_mark_sd = 0
    else:
        thresh_mark_nom = thresh_mark_new.nominal_value
        thresh_mark_sd = thresh_mark_new.std_dev
    return thresh_mark_nom, thresh_mark_sd

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


def s_fit(dose, pid, weights=None, p_guess=[1, 1], logfit=True, altfit=0):
    """
    Determines fit parameters from an S-curve fit to data
    """
    if logfit:
        if altfit == 1:
            model = Model(boltzmann_log_alt)
        else:
            model = Model(boltzmann_log)
    else:
        if altfit == 1:
            model = Model(boltzmann_lin_alt)
        else:
            model = Model(boltzmann_lin)

    params = model.make_params()
    params["a1"].set(1.0)
    params["a2"].set(0.0)
    params["B"].set(p_guess[0])
    params["Q"].set(p_guess[1])
    r = model.fit(pid, params, weights=weights, method='leastsq', x=dose)
    return r
