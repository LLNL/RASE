# -*- mode: python -*-

block_cipher = None

# import sys
# sys.setrecursionlimit(10000)

import PySide6
import platform

pathex = []
exclude_binaries = True
if platform.system() == "Windows":
    pathex.append(PySide6.__path__[0])
    exclude_binaries=False

a = Analysis(['rase.pyw'],
             pathex=pathex,
             binaries=[],
             datas=[('doc/_build/html', 'doc/_build/html'),
                    ('d3_resources', 'd3_resources'),
                    ('tools', 'tools')],
             hiddenimports=['sqlalchemy.ext.baked', 'pandas._libs.tslibs.base'],
             hookspath=[],
             runtime_hooks=[],
             excludes=['IPython','tcl','tk','_tkinter', 'tkinter', 'Tkinter', 'Sphinx'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe_args = (a.scripts, a.binaries, a.zipfiles, a.datas) if platform.system() == 'Windows' else (a.scripts, [])
exe = EXE(pyz,
          *exe_args,
          exclude_binaries=exclude_binaries,
          name='rase',
          debug=False,
          strip=False,
          upx=False,
          # switch to console=True to debug issues with .exe execution
          console=False)

# This is for the one-folder option, useful for debugging
# coll = COLLECT(exe,
#                a.binaries,
#                a.zipfiles,
#                a.datas,
#                strip=False,
#                upx=False,
#                name='rase')

if platform.system() == "Darwin":
    app = BUNDLE(exe,
                 a.binaries,
                 a.zipfiles,
                 a.datas,
                 name='rase.app',
                 icon=None,
                 bundle_identifier=None)