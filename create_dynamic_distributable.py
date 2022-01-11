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

import os
import sys
from shutil import copytree, rmtree, copy
import platform

dirname = os.path.abspath(os.path.dirname(__file__))
templatepath_name = "n42Templates"
basespectra_name = "dynamicBaseSpectra"
buildpath = os.path.join(dirname, "dynamic_build")
distpath = os.path.join(dirname, "dynamic_dist")

if not os.path.exists(distpath):
    os.makedirs(distpath)

# Ensure documentation is compiled
r = os.system(
    f"sphinx-build -M html \"{os.path.join(dirname, 'doc', 'dynamic_doc')}\" \"{os.path.join(dirname, 'doc', 'dynamic_doc', '_build')}\"")
if r: exit(r)

# Main RASE app
options = "--onedir --windowed" if platform.system() == "Darwin" else ""
r = os.system(sys.executable + " -m PyInstaller -a -y " + options +
          " --distpath " + distpath +
          " --workpath " + buildpath +
          " drase.spec")
if r: exit(r)

# Templates and base spectra
for source_name in (templatepath_name, basespectra_name):
    destination_path = os.path.join(distpath, source_name)
    rmtree(destination_path, ignore_errors=True)
    copytree(os.path.join(dirname, source_name), destination_path)

# tools
tools_path = os.path.join(distpath, "ReplayTools")
rmtree(tools_path, ignore_errors=True)
os.makedirs(tools_path)

# demo replay tool
r = os.system(sys.executable + " -m PyInstaller -a -y -F --noupx" +
              " --distpath " + os.path.join(distpath, 'ReplayTools') +
              " --workpath " + buildpath + " " +
              os.path.join(dirname, "tools", "demo_replay.py"))
if r: exit(r)

# Translators
# r = os.system(sys.executable + " " + os.path.join(dirname, "translators", "create_translators_exe.py"))
# if r: exit(r)

if platform.system() == "Darwin":
    import dmgbuild

    print("Creating App Bundle")
    translators_path = os.path.join(dirname, 'translators', 'dist')
    dmgbuild.build_dmg(volume_name="DYNAMIC_RASE",
                       filename=os.path.join(distpath, "dynamic_rase.dmg"),
                       settings_file="dmgbuild_settings.py",
                       settings={'files': [os.path.join(distpath, 'dynamic_rase.app'),
                                           translators_path,
                                           tools_path,
                                           templatepath_name,
                                           basespectra_name]},
                       )
