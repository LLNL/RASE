import os
import sys
from shutil import copy2

dirname = os.path.dirname(os.path.dirname(__file__))
buildpath = os.path.join(dirname,"build")
distpath = os.path.join(dirname,"dist","translators")

if not os.path.exists(distpath):
     os.makedirs(distpath)

translators = [('ORTEC-CmdLineReplayTool-ResultsTranslator.py',''),
               ('ORTEC-StndAloneGUIReplayTool-ResultsTranslator.py',''),
               ('FLIR-IdentiFinder-ResultsTranslator.py','')]

for translator, template in translators:
    os.system(sys.executable + " -m PyInstaller -a -y -F -c --clean --noupx" +
          " --distpath " + distpath +
          " --workpath " + buildpath +
          " " + translator)
    if template:
        copy2(template, distpath)
    print("\n\n")
