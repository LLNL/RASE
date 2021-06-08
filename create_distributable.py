import os
import sys
from shutil import copytree, rmtree, copy
import platform

dirname = os.path.abspath(os.path.dirname(__file__))
templatepath_name = "n42Templates"
basespectra_name = "baseSpectra"
buildpath = os.path.join(dirname, "build")
distpath = os.path.join(dirname, "dist")

if not os.path.exists(distpath):
    os.makedirs(distpath)

# Ensure latest ui
r = os.system(sys.executable + " build-ui.py")
if r: exit(r)

# Ensure documentation is compiled
r = os.system(f"sphinx-build -M html \"{os.path.join(dirname, 'doc')}\" \"{os.path.join(dirname, 'doc', '_build')}\"")
if r: exit(r)

# Main RASE app
options = "--onedir --windowed" if platform.system() == "Darwin" else ""
r = os.system(sys.executable + " -m PyInstaller -a -y " + options +
          " --distpath " + distpath +
          " --workpath " + buildpath +
          " rase.spec")
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
copy(os.path.join(dirname, "tools", "FLIR-R440-ReplayTool-Wrapper.cmd"), tools_path)

# demo replay tool
r = os.system(sys.executable + " -m PyInstaller -a -y -F --noupx" +
          " --distpath " + os.path.join(distpath, 'ReplayTools') +
          " --workpath " + buildpath + " " +
          os.path.join(dirname, "tools","demo_replay.py"))
if r: exit(r)

# Translators
r = os.system(sys.executable + " " + os.path.join(dirname, "translators", "create_translators_exe.py"))
if r: exit(r)

if platform.system() == "Darwin":
    import dmgbuild
    print("Creating App Bundle")
    translators_path = os.path.join(dirname, 'translators', 'dist')
    dmgbuild.build_dmg(volume_name="RASE",
                       filename=os.path.join(distpath, "rase.dmg"),
                       settings_file="dmgbuild_settings.py",
                       settings={'files': [os.path.join(distpath, 'rase.app'),
                                           translators_path,
                                           tools_path,
                                           templatepath_name,
                                           basespectra_name]},
                       )
