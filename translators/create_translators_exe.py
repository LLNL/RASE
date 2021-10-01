import os
import sys
from shutil import copy2

dirname = os.path.abspath(os.path.dirname(__file__))
buildpath = os.path.join(dirname, "..", "build", "translators")
distpath = os.path.join(dirname,"..", "dist", "translators")

if not os.path.exists(distpath):
     os.makedirs(distpath)

translators = ['ORTEC-CmdLineReplayTool-ResultsTranslator.py',
               'ORTEC-StndAloneGUIReplayTool-ResultsTranslator.py',
               'FLIR-IdentiFinder-ResultsTranslator.py',
               'GADRAS_CL_ResultsTranslator-v2.py',
               'KromekD5-ResultsTranslator.py',
               'Smith_RadSeeker_ResultsTranslator.py',
               'Symetrica-ResultsTranslator.py']
translators = map(lambda x: os.path.join(dirname, x), translators)

for translator in translators:
    os.system(sys.executable + " -m PyInstaller -a -y -F -c --clean --noupx" +
          " --distpath " + distpath +
          " --workpath " + buildpath +
          " --specpath=" + dirname +
          " " + translator)
    print("\n\n")
