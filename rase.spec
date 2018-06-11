# -*- mode: python -*-

block_cipher = None

# import sys
# sys.setrecursionlimit(10000)

import PyQt5

a = Analysis(['rase.pyw'],
             pathex=[PyQt5.__path__[0] + '\\Qt\\bin',],
             binaries=[],
             datas=[('doc/_build/html','doc/_build/html')],
             # this hidden import is required for sqlalchemy 1.2
             hiddenimports=['sqlalchemy.ext.baked'],
             hookspath=[],
             runtime_hooks=[],
             excludes=['IPython','tcl','tk','_tkinter', 'tkinter', 'Tkinter', 'Sphinx'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          # exclude_binaries=True,
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
