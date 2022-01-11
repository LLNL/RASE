# -*- mode: python -*-

block_cipher = None

# import sys
# sys.setrecursionlimit(10000)

import platform

pathex = []
exclude_binaries = True
if platform.system() == "Windows":
    exclude_binaries = False

a = Analysis(['dynamic/DRASE.py'],
             pathex=pathex,
             binaries=[],
             datas=[('doc/dynamic_doc/_build/html', 'doc/dynamic_doc/_build/html')],
             hiddenimports=['sqlalchemy.ext.baked'],
             hookspath=[],
             runtime_hooks=[],
             excludes=['IPython', 'Sphinx'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe_args = (a.scripts, a.binaries, a.zipfiles, a.datas) if platform.system() == 'Windows' else (a.scripts, [])
exe = EXE(pyz,
          *exe_args,
          exclude_binaries=exclude_binaries,
          name='dynamic_rase',
          debug=False,
          strip=False,
          upx=False,
          # switch to console=True to debug issues with .exe execution
          console=True)

# This is for the one-folder option, useful for debugging
# coll = COLLECT(exe,
#                a.binaries,
#                a.zipfiles,
#                a.datas,
#                strip=False,
#                upx=False,
#                name='dynamic_rase')

if platform.system() == "Darwin":
    app = BUNDLE(exe,
                 a.binaries,
                 a.zipfiles,
                 a.datas,
                 name='dynamic_rase.app',
                 icon=None,
                 bundle_identifier=None)