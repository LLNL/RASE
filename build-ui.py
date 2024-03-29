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
Creates .py script from .ui files in the /src/ui/ folder
Mimics qt_tool_wrapper from PySide6.scripts.py_side_tool to run `uic` command
"""

import os
import sys
import glob
from pathlib import Path
from subprocess import Popen, PIPE

import PySide6


def get_uic_exe():
    pyside_dir = Path(PySide6.__file__).resolve().parent
    if sys.platform != "win32":
        exe = pyside_dir / 'Qt' / 'libexec' / 'uic'
    else:
        exe = pyside_dir / 'uic.exe'
    return exe


def main():
    exe = get_uic_exe()
    for path in Path("./src/ui/").glob('*.ui'):
        outpath = Path('src', 'ui_generated', 'ui_' + path.name).with_suffix('.py')
        print(path, '>>', outpath)

        cmd = [os.fspath(exe), '-g', 'python', str(path), '-o', str(outpath)]
        proc = Popen(cmd, stderr=PIPE)
        out, err = proc.communicate()
        if err:
            msg = err.decode("utf-8")
            command = ' '.join(cmd)
            print(f"Error: {msg}\nwhile executing '{command}'")


if __name__ == "__main__":
    main()
