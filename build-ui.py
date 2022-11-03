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
