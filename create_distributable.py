import os
import sys
from shutil import copytree, rmtree, copy

dirname = os.path.abspath(os.path.dirname(__file__))
templatepath_name = "n42Templates"
basespectra_name = "baseSpectra"
buildpath = os.path.join(dirname, "build")
distpath = os.path.join(dirname, "dist")

if not os.path.exists(distpath):
    os.makedirs(distpath)

os.system(sys.executable + " -m PyInstaller -a -y --clean" +
          " --distpath " + distpath +
          " --workpath " + buildpath +
          " rase.spec")

for source_name in (templatepath_name, basespectra_name):
    destination_path = os.path.join(distpath, source_name)
    rmtree(destination_path, ignore_errors=True)
    copytree(os.path.join(dirname, source_name), destination_path)

tools_path = os.path.join(distpath, "ReplayTools")
rmtree(tools_path, ignore_errors=True)
os.makedirs(tools_path)
copy(os.path.join(dirname, "tools", "FLIR-R440-ReplayTool-Wrapper.cmd"), tools_path)
