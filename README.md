RASE - Replicative Assessment of Spectroscopic Equipment
========================================================

RASE is a software for evaluating the performance of radiation detectors and isotope identification algorithms.
It uses a semi-empirical approach to rapidly generate synthetic spectra and inject into detector’s software
to obtain nuclide identification response.

For more information on RASE see:
* [R. Arlt et al, IEEE NSS Conf Record, 2009](https://doi.org/10.1109/NSSMIC.2009.5402448)


Required Libraries
----------------------------------
* Qt6, PySide6
* declxml, lxml, pyyaml
* isodate
* SQLAlchemy < 2.0
* Matplotlib >= 3.5, 
* Numpy, Pandas, Scipy
* Uncertainties, LmFit
* Mako
* Seaborn
* marshmallow-sqlalchemy
* pytest, pytest-qt (for unit testing)

The relevant packages can be conveniently installed using `pip` with the included `requirements.txt` file.

Creating a standalone executable
--------------------------------
[PyInstaller](http://www.pyinstaller.org/) can be used to generate a standalone executable for distribution on Windows
operating systems.

Note that PyInstaller is rather sensitive to the overall python configuration. These instructions assume a clean
python environment with the minimal set of python packages installed. We recommend starting with a clean empty python environment 
(e.g. using WinPythonZero)

* Install pyinstaller and pypiwin32 packages via `pip install pyinstaller pypiwin32`
* The file `rase.spec` contains the specifications to create a single executable file `dist\rase.exe`.
* Run `pyinstaller -a -y rase.spec`  or `python create_distributable.py` from the RASE base folder


Generating documentation with Sphinx
------------------------------------
RASE documentation is maintained using [Sphinx](http://www.sphinx-doc.org/en/stable/).
The documentation resides in the `doc` folder.

Install Sphinx from PyPi using
`$ pip install Sphinx`

<!-- For referencing figures by number it is required to install the numfig extension for Sphinx. -->
<!-- Installation is performed with the following steps: -->
<!-- 1. Download and untar the file at this [link](https://sourceforge.net/projects/numfig/files/Releases/sphinx_numfig-r13.tgz/download) -->
<!-- 1. Run `2to3 -w setup.py` -->
<!-- 1. Run `python setup.py install` -->

To update the documentation:
1. `cd $RASE\doc`, where `$RASE` is RASE base folder where rase.pyw lives
1. `make html` to generate html docs
1. `make latexpdf` to generate latex docs and immediately compile the pdf

The documentation is generated in the `doc\_build\` folder


Contributors
------------

- Lance Bentley-Tammero, LLNL
- Jason Brodsky, LLNL
- Joe Chavez, LLNL
- Steven Czyz, LLNL
- Greg Kosinovsky, LLNL
- Vladimir Mozin, LLNL
- Samuele Sangiorgio, LLNL

Citation
--------

Please cite use of the RASE software as:

L. Bentley-Tammero, J. P. Brodsky, J. Chavez, S. A. Czyz, G. Kosinovsky, V. Mozin, & S. Sangiorgio. 
(2024, Jan 10). LLNL/RASE: RASE v2.4 (Version v2.4). Zenodo. http://doi.org/10.5281/zenodo.10480562


Acknowledgements
----------------

This work was performed by Lawrence Livermore National Laboratory under the auspices
of the U.S. Department of Energy  under contract DEJAC52J07NA27344,
and of the U.S. Department of Homeland Security Domestic Nuclear Detection Office
under contract HSHQDC-15-X-00128.

Lawrence Livermore National Laboratory (LLNL) gratefully acknowledges support from
the U.S. Department of Energy (DOE) Nuclear Smuggling Detection and Deterrence
program and from the Countering Weapons of Mass Destruction Office of the U.S.
Department of Homeland Security.


License
-------

RASE is released under an MIT license and LGPL License. For more details see the [LICENSE]
(/LICENSE-MIT) and [LICENSE](/LICENSE-LGPL) files.

LLNL-CODE-858590, LLNL-CODE-829509
