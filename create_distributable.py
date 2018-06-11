import os
import sys
from shutil import copytree, rmtree

dirname = os.path.abspath(os.path.dirname(__file__))
templatepath_name = "n42Templates"
templatepath = os.path.join(dirname, templatepath_name)
buildpath = os.path.join(dirname, "build")
distpath = os.path.join(dirname, "dist")
print(templatepath)

if not os.path.exists(distpath):
    os.makedirs(distpath)

os.system(sys.executable + " -m PyInstaller -a -y --clean" +
          " --distpath " + distpath +
          " --workpath " + buildpath +
          " rase.spec")

rmtree(os.path.join(distpath, templatepath_name))
copytree(templatepath, os.path.join(distpath, templatepath_name))
