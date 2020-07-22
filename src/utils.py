###############################################################################
# Copyright (c) 2018 Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory
#
# Written by J. Chavez, G. Kosinovsky, V. Mozin, S. Sangiorgio.
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
This module defines profileit() and compress_counts() utility functions
"""

import re

PROFILE = False


def profileit(func):
    """
    wrapper for profiling specific functions
    profiles only if global 'PROFILE' variable is set to True

    :param func:
    :return:
    """

    def wrapper(*args, **kwargs):
        if PROFILE:
            import cProfile
            datafn = func.__module__ + "." + func.__name__ + ".profile"  # Name the data file sensibly
            prof = cProfile.Profile()
            retval = prof.runcall(func, *args, **kwargs)
            prof.dump_stats(datafn)
        else:
            retval = func(*args, **kwargs)

        return retval

    return wrapper

def compress_counts(counts):
    """

    :param counts:
    :return:
    """
    compressedCounts = []

    zeroTimes = 0
    for count in counts:
        if count == 0:
            zeroTimes += 1
        else:
            if zeroTimes != 0:
                compressedCounts.append(0)
                compressedCounts.append(zeroTimes)
                zeroTimes = 0
            compressedCounts.append(count)
    if counts[-1] == 0:
        compressedCounts.append(0)
        compressedCounts.append(zeroTimes)
    return compressedCounts


def atoi(text):
    return int(text) if text.isdigit() else text


def natural_keys(text):
    '''
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (See Toothy's implementation in the comments)
    '''
    return [atoi(c) for c in re.split(r'(\d+)', text)]