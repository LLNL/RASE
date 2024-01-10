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
This module implements available sampling algorithms
"""

# Note: The first line in the docstring is used as the readable name for the downsampling method

import numpy as np


def generate_sample_counts_rejection(scenario, detector, countsDoseAndSensitivity, seed):
    """ Rejection Sampling
    This is a modified version of the rejection algorithm employed by the IAEA in the original
    iteration of RASE (10.1109/NSSMIC.2009.5402448)

    :param seed:
    :param scenario:
    :param detector:
    :param countsDoseAndSensitivity:
    :return:
    """

    np.random.seed(seed)

    sampleCounts = np.zeros(detector.chan_count, dtype=int)

    for counts, dose, sensitivity in countsDoseAndSensitivity:
        counts[counts < 0] = 0

        pdf = np.array(counts) / sum(counts.astype(float))
        integral = np.random.poisson(scenario.acq_time * dose * sensitivity)

        i = 0
        counts_len = len(counts)

        while integral > 0:
            # there might be an optimization possible between the size of the array of random numbers
            # and the looping through each array
            xx = np.random.randint(0, counts_len, size=integral * 10)
            yy = np.random.random_sample(integral * 10)

            for x in xx[np.where(yy <= pdf[xx])]:
                if i < integral:
                    sampleCounts[x] += 1
                    i += 1
                else:
                    break
            # this else is executed only if no 'break' statement was encountered in the for loop
            else:
                continue

            break

    return sampleCounts


def generate_sample_counts_poisson(scenario, detector, countsDoseAndSensitivity, seed):
    """Poisson Re-sampling (Default)
    Very quick downsampling method based on bin-by-bin Poisson re-sampling.

    :param scenario:
    :param detector:
    :param countsDoseAndSensitivity:
    :param seed:
    :return:
    """
    sampleCounts = [0] * detector.chan_count

    np.random.seed(seed)

    # sum up
    for counts, dose, sensitivity in countsDoseAndSensitivity:
        counts[counts < 0] = 0
        counts = counts.astype(float) * (scenario.acq_time * dose * sensitivity) / sum(counts.astype(float))
        counts = np.random.poisson(counts)  # Poisson noise
        sampleCounts += counts
    return sampleCounts.astype(int)


def generate_sample_counts_inversion(scenario, detector, countsDoseAndSensitivity, seed):
    """Inverse Transform Sampling
    This uses np.random.choice() which is rather fast and employs the inverse transform sampling method
    which generates random numbers from a probability distribution given its cumulative distribution function.

    :param scenario:
    :param detector:
    :param countsDoseAndSensitivity:
    :param seed:
    :return:
    """
    np.random.seed(seed)

    sampleCounts = np.zeros(detector.chan_count, dtype=int)

    for counts, dose, sensitivity in countsDoseAndSensitivity:
        counts[counts < 0] = 0

        pdf = np.array(counts) / sum(counts.astype(float))
        integral = np.random.poisson(scenario.acq_time * dose * sensitivity)

        x = np.random.choice(len(pdf), size=integral, p=pdf)
        for k in x:
            sampleCounts[k] += 1

    return sampleCounts

