.. _replayToolSettings:

********************
Replay Tool Settings
********************

This section contains information on the configuration settings for the replay tools of a number of radioisotope identification instruments. These settings should be entered in the RASE "Add Replay Tool" dialog.

It is important to note that for executable and template files, the full path should be specified. This can be done using the corresponding "Browse" button within the RASE "Add Replay Tool" dialog.

Note also that some templates indicated here may be specific to a given model of an instrument, even though the replay tool may be compatible with other models as well.


Demo Replay Tool
================
Use this replay tool for demonstration purposes together with the ABCD-instrument Base Spectra included with the RASE code Distribution.
Note that the Demo Replay Tool generates random isotope identification results, and does not perform the analysis of  sampled spectra.
Otherwise, the spectra generation and results analysis process is performed as usual.

**Settings**

* Replay Tool:
    *  Executable: demo_replay.exe
    *  Command Line checkbox: checked
    *  Command Arguments: INPUTDIR OUTPUTDIR [this is a default entry]
* Sampled Spectra n42 Template:
    *  n42 Template File: none - leave empty
    *  Suffix of input files: .n42 or empty
* Identification Results Translator:
    *  Executable: none - leave empty
    *  Command Line checkbox: checked
    *  Command Arguments: INPUTDIR OUTPUTDIR [this is a default entry]


FLIR IdentiFinder-2 Replay Tool
===============================
RASE code was successfully tested with 2016, 2017, and 2018 versions of the FLIR replay tool. Regular analysis procedure applies.

**Settings**

* Replay Tool:
    *  Executable: replay.exe
    *  Command Line checkbox: checked
    *  Command Arguments: -r INPUTDIR -o OUTPUTDIR [see the replay tool manual for additional command line parameters that can be used here]
* Sampled Spectra n42 Template:
    *  n42 Template File: FLIR_ID2_template_spectrum.n42
    *  Suffix of input files: .n42
* Identification Results Translator:
    *  Executable: FLIR-IdentiFinder-ResultsTranslator.exe
    *  Command Line checkbox: checked
    *  Command Arguments: INPUTDIR OUTPUTDIR [this is a default entry]


FLIR R300 Replay Tool
=====================
R300 analysis uses the same replay tool as the IdentiFinder-2 with a different template file.
R300 base spectra and the RASE analysis routine were tested with the 2018 version of the replay tool.

**Settings**

* Replay Tool:
    *  Executable: replay.exe
    *  Command Line checkbox: checked
    *  Command Arguments: -r INPUTDIR -o OUTPUTDIR [see the replay tool manual for additional command line parameters that can be used here]
* Sampled Spectra n42 Template:
    *  n42 Template File: FLIR_R300_template.n42
    *  Suffix of input files: .n42
* Identification Results Translator:
    *  Executable: FLIR-IdentiFinder-ResultsTranslator.exe
    *  Command Line checkbox: checked
    *  Command Arguments: INPUTDIR OUTPUTDIR [this is the default entry]


FLIR R400 Replay Tool
=====================
R400 analysis uses the same replay tool and settings as the IdentiFinder-2.
R400 base spectra and the RASE analysis routine were tested with the 2018 version of the replay tool.

Note: Care should be taken with the selection of .n42 template, as the correct template depends on the dataset being used. If the base spectra set is taken from the INL 2018 measurement campaign, the FLIR_R400_UW-LGH_INL2018_template.n42 should be used. This template has a fixed internal calibration source spectrum that also includes the influence of background, and is necessary for the correct operation of the replay tool. Otherwise, the user may use the FLIR_R400_UW-LGH_template.n42 template, which sources the secondary spectrum from the scenario definition or one of the base spectra selected by the user (as described in the "second spectrum treatment" section of the :ref:`workflowStep1` page).


**Settings**

* Replay Tool:
    *  Executable: replay.exe
    *  Command Line checkbox: checked
    *  Command Arguments: -r INPUTDIR -o OUTPUTDIR [see the replay tool manual for additional command line paprmeters that can be used here]
* Sampled Spectra n42 Template:
    *  n42 Template File: FLIR_R400_UW-LGH_template.n42
    *  Suffix of input files: .n42
* Identification Results Translator:
    *  Executable: FLIR-IdentiFinder-ResultsTranslator.exe
    *  Command Line checkbox: checked
    *  Command Arguments: INPUTDIR OUTPUTDIR [this is the default entry]


FLIR R440 Replay Tool
=====================
FLIR R440 requires a different replay tool and settings than the rest of the FLIR instruments tested with the RASE code.

**Settings**

* Replay Tool:
    *  Executable: FLIR-R440-ReplayTool-Wrapper.cmd [included with the RASE distribution. Place it in the same folder where Target.NID.ReplayTool.exe file is located.]
    *  Command Line checkbox: checked
    *  Command Arguments: INPUTDIR OUTPUTDIR [this is the default entry]
* Sampled Spectra n42 Template:
    *  n42 Template File: FLIR_R440_template.n42
    *  Suffix of input files: .n42
* Identification Results Translator:
    *  Executable: none - leave empty
    *  Command Line checkbox: checked
    *  Command Arguments: INPUTDIR OUTPUTDIR [this is the default entry]


ORTEC Replay Tool for HPGe Devices
==================================
RASE code was tested with the version 9.3.4 of the ORTEC command-line replay tool. Earlier versions may also work. It also can be used to analyse sampled spectra
generated for ORTEC HX-2 MicroDetective, EX-1, D200, Trans-Spec, and Detective-X instruments.
Please note that on some Windows machines execution of the replay tool may fail with the following error message:
"Error reading the XML library. Error message: This implementation is not part of the Windows Platform FIPS validated cryptographic algorithms."
This error may also yield no message, leaving the user with an empty replay folder with no explanation. To resolve this
issue, the user can go to the following location and disable the relevant Windows registry flag:

**Administrative Tools -> Local Security Policy -> Local Policies -> Security Options -> System Cryptography -> Use
FIPS compliant algorithms for encryption, hashing, and signing**

This option will automatically return to "enabled" upon logging out.

**Settings**

* Replay Tool:
    *  Executable: ORTEC_ID_Engine_RASE.exe
    *  Command Line checkbox: checked
    *  Command Arguments: INPUTDIR OUTPUTDIR [this is the default entry]
* Sampled Spectra n42 Template:
    *  n42 Template File: ORTEC-HX_template_spectrum.n42
    *  Suffix of input files: .n42
* Identification Results Translator:
    *  Executable: ORTEC-CmdLineReplayTool-ResultsTranslator.exe
    *  Command Line checkbox: checked
    *  Command Arguments: INPUTDIR OUTPUTDIR [this is the default entry]


ORTEC RadEagle and RadEaglet Replay Tool
========================================
ORTEC RadEagle and RadEaglet instruments require a different replay tool and settings than the HPGe-based systems.

**Settings**

* Replay Tool:
    *  Executable: elia-rp.exe
    *  Command Line checkbox: checked
    *  Command Arguments: INPUTDIR OUTPUTDIR [this is the default entry]
* Sampled Spectra n42 Template:
    *  n42 Template File: none - leave empty
    *  Suffix of input files: .n42
* Identification Results Translator:
    *  Executable: none - leave empty
    *  Command Line checkbox: checked
    *  Command Arguments: INPUTDIR OUTPUTDIR [this is the default entry]


Smiths Replay Tool
==================
The procedure for Smiths Radseeker CL and Radseeker CS instruments involves a stand-alone replay tool that is called by the RASE code during the analysis workflow but the user must manually interact with it to perform the identification analysis.

Define the instrument using the base spectra and generate sampled spectra as usual. Define the Smiths replay tool using the settings identified below.

**Settings**

* Replay Tool:
    *  Executable: BatchAnalysis.exe
    *  Command Line checkbox: unchecked
    *  Command Arguments: INPUTDIR OUTPUTDIR [this is a default entry]
* Sampled Spectra n42 Template:
    *  n42 Template File: Smith_RadseekerCL_template_spectrum.n42 [or Smith_RadseekerCS_template_spectrum.n42]
    *  Suffix of input files: _U.n42
* Identification Results Translator:
    *  Executable: Smith_RadSeeker_ResultsTranslator.exe
    *  Command Line checkbox: checked
    *  Command Arguments: INPUTDIR OUTPUTDIR [this is a default entry]

After generating sampled spectra, use the "Run Replay Tool" button to open the external window of the stand-alone Smiths replay tool.
Keep the pop-up window that specifies the input and output directories open.
In the Replay Tool window (HPRID Batch Analysis) enter the "File" menu and click on the "Batch Analysis..." command.
In the new "Batch Analysis" window, use the "Add Files" button to add the sampled spectra (use the "Input folder" path in
the RASE pop-up window to locate the files). Sampled spectral files will be listed in the Replay Tool.
Specify the Output directory to match the "Output folder" path in the RASE pop-up window (use the "Browse" button).
Press the "Start" button to make the Replay Tool perform the analysis of sampled spectra. Feel free to close the Replay Tool window once the analysis is completed.
Close the RASE pop-up window and continue with the results analysis within the RASE main window as usual: use the "Run Result Translator" and "View Results" buttons.


Symetrica Verifinder SN33-N Backpack Replay Tool
================================================
The Symetrica Verifinder backpack utilizes only static spectra for isotope identification, and requires no additional transient data for correct functionality.
The Symetrica template has been tested and verified for the SN33-N replay tool. This replay tool is compatible with base spectra sourced from backpack models SN31-N, SN32-N, and SN33-N. Installation instructions for this replay tool can be found in the README for the Symetrica Replay Tool.
Please note that the Symetrica replay tool is sensitive to installation location, and issues may develop if the tool is installed somewhere other than the C: drive. Problems have also been observed when the sample spectra directory is not located on the same drive as the replay tool. To ensure smooth functionality, it is strongly recommended that any sample directory that includes Symetrica backpack sample spectra exist on the C: drive along with the replay tool.
The current implementation of the template makes use of a fixed background with a dose rate of 0.08 μSv/h. To ensure reliable results, when using the scenario creator tool to define scenarios for the Symetrica backpack a background spectrum of 0.08 μSv/h should be set.

**Settings**

* Replay Tool:
    *  Executable: Replay.cmd
    *  Command Line checkbox: checked
    *  Command Arguments: -r -c SN33-N -i INPUTDIR -o OUTPUTDIR
* Sampled Spectra n42 Template:
    *  n42 Template File: Symetrica_SN33N_template.n42
    *  Suffix of input files: .n42
* Identification Results Translator:
    *  Executable: Symetrica-ResultsTranslator.exe
    *  Command Line checkbox: checked
    *  Command Arguments: INPUTDIR OUTPUTDIR [this is a default entry]

Kromek D5 Replay Tool
================================================
Kromek provides a replay tool for their D5 instrument, called :code:`PCSOffiline`, that is packaged for Linux operating systems.
As of version 170.1.5.7, the replay tool only accepts a single file as input.  To facilitate use within RASE, which
requires processing an entire folder, a wrapper shell script :code:`KromekD5_replaytool_wrapper.sh` is provided in the :code:`tools`.

If you are not running RASE on a unix system, one way to run the replay tool on other machines is to dockerize it.
To facilitate this process, we provide the :code:`Dockerfile-KromekD5` file in the :code:`tools` folder.
Note that it assumes the :code:`PCSOffile.deb` package and the wrapper shell script are in the same directory as the :code:`Dockerfile`.
To create the image, simply run :code:`docker build -t kromek-rt -f Dockerfile-KromekD5`.

**Settings**

* Replay Tool:
    *  Executable: path to the docker executable e.g. :code:`/usr/local/bin/docker`
    *  Command Line checkbox: checked
    *  Command Arguments: :code:`run --rm -v INPUTDIR:/data/in -v OUTPUTDIR:/data/out kromek-rt KromekD5_replaytool_wrapper.sh /data/in/ /data/out`
* Sampled Spectra n42 Template:
    *  n42 Template File: :code:`Kromek_D5_template.n42`
    *  Suffix of input files: :code:`.csv`
* Identification Results Translator:
    *  Executable: :code:`KromekD5-ResultsTranslator.exe`
    *  Command Line checkbox: checked
    *  Command Arguments: :code:`INPUTDIR OUTPUTDIR` [this is a default entry]


GADRAS Isotope ID Replay Tool
=============================

Starting from version 2, the RASE code supports seamless integration of the GADRAS Isotope ID engine in the analysis workflow.
This capability allows the user to use GADRAS Isotope ID as a "universal" replay tool for any instrument (provided that an appropriate DRF is defined)
that can be executed directly from the RASE main window without a need to switch between applications.
This feature is available only for approved users. Please contact the RASE developement team to request it.
The executable that enables calls to the GADRAS API can be used as a stand-alone utility or can be defined in the RASE graphical
user interface follows the same general approach as for a typical command-line replay tool.

Prerequisites
--------------

1. GADRAS version 18.8.11 (64-bit) version must be installed. Using other versions of GADRAS may result in errors. If compatibility with another GADRAS version or a 32-bit compilation is needed, please contact the RASE development team.

2. Presently, a standard complete GADRAS installation with defaults setting is required (i.e. code installed in :code:`C:\\GADRAS directory`).

3. Three directories should be set up:
    * Detector directory. This is a folder that contains the GADRAS detector model and DRF. It can be placed at a default :code:`C:\\GADRAS\\Detector path`, or in any other location on the hard drive. This directory must contain the detector.dat file with the DRF of the particular instrument. Additionally, it is best practice (but not required) that the directory contain the :code:`DB.pcf` file.  This can be generated by running the IsotopeID algorithm from within the GADRAS GUI with the desired detector and copying the file from the GADRAS detector directory to the working detector directory.  If :code:`DB.pcf` is not present in the detector directory, the first time the code is run it will generate the :code:`DB.pcf` file, which takes several minutes to generate.

    * Input directory. This directory contains the RASE-generated .n42 sampled spectra to be analyzed. This directory is created by the RASE code automatically, and a path to its location is contained under the INPUTDIR keyword.
    * Output directory. An empty directory that will contain the GADRAS Isotope ID analysis results in text files (one file per each input sampled spectrum in the .n42 format). This directory is also created automatically by the RASE code, and its path is contained in the OUTPUTDIR keyword.

User Notes
----------

The GADRAS Isotope ID requires input spectra in a .pcf file format. The RASE code generates sampled spectra in the .n42 format, therefore these files must be converted prior to making calls through the GADRAS API. This is completed automatically by the provided executable.

Background spectra can be provided for the GADRAS Isotope ID analysis in two ways:
    - As a second spectra entry in the sampled .n42 file. This is currently specified in the "template" file, where the first spectral entry contains placeholders for the sampled foreground spectrum, and the second entry is the pre-existing background spectrum.
    - As a single file with one background spectrum entry; it is specified as a command-line argument. This file will be used as a fixed background for the analysis of all sampled spectra in the current scenario.

If no fixed background file is provided, the code will try to use the second spectrum listed in each of the .n42 sampled files
(the first spectrum in the n42 file is assumed to be the foreground, the second spectrum is assumed to be the background).
If the n42 files each only contain a single foreground spectrum, and no fixed background spectrum is supplied, the GADRAS IsotopeID
will be called without any background spectrum, which may degrade the identification performance.
Note that the fixed background file could be specified either as an .n42 file or a GADRAS .pcf format. If the fixed background file is an n42 file,
the executable will automatically create a .pcf file with the same spectrum and put it in the same location as the original background .n42 file.
If the fixed background file is in the .pcf format, it will remain unchanged.


**RASE settings if background is included as a second entry on each sampled file or when no background is provided:**

* Replay Tool:
    *  Executable: run_gadras_isotopeID.exe
    *  Command Line checkbox: checked
    *  Command Arguments: :code:`-d <path to a directory containing the detector.dat file for this instrument> -i INPUTDIR -o OUTPUTDIR`
* Sampled Spectra n42 Template:
    *  n42 Template File: :code:`GADRAS_IsotopeID_Template.n42` or :code:`GADRAS_IsotopeID+NoBKG_Template.n42`
    *  Suffix of input files: .n42 or empty
* Identification Results Translator:
    *  Executable: :code:`GADRAS_CL_ResultsTranslator-v2.py`
    *  Command Line checkbox: checked
    *  Command Arguments: :code:`INPUTDIR OUTPUTDIR` [this is a default entry]


**RASE settings if a fixed background is provided as a single file:**

* Replay Tool:
    *  Command Line checkbox: checked
    *  Command Arguments: :code:`-d <path to a directory containing the detector.dat file for this instrument> -b <background file in .n42 or .pcf format> -i INPUTDIR -o OUTPUTDIR`
* Sampled Spectra n42 Template:
    *  n42 Template File: :code:`GADRAS_IsotopeID_Template.n42` or :code:`GADRAS_IsotopeID+NoBKG_Template.n42`
    *  Suffix of input files: .n42 or empty
* Identification Results Translator:
    *  Executable: :code:`GADRAS_CL_ResultsTranslator-v2.py`
    *  Command Line checkbox: checked
    *  Command Arguments: :code:`INPUTDIR OUTPUTDIR` [this is a default entry]


**Complete list of command line parameters and syntax:**

.. code-block:: bash

   python run_gadras_isotopeID.py [-h] -i INPUT_DIR -d DETECTOR_DIR
                                       -o OUTPUT_DIR [-b BKG_FILE] [-v]

Script that converts input n42 files to .pcf files and makes the call to
IsotopeID via the GADRAS API

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT_DIR, --inputDir INPUT_DIR
                        Directory containing input (n42) files
  -d DETECTOR_DIR, --detectorDir DETECTOR_DIR
                        Directory containing GADRAS detctor model
  -o OUTPUT_DIR, --outputDir OUTPUT_DIR
                        Directory to contain output resutls files
  -b BKG_FILE, --backgroundFile BKG_FILE
                        fixed background file to use for IsotopeID
  -v                    verbose mode

**Example command line calls**

Example call for the case when the background spectra are included in the same .n42 file as the sampled foreground spectra:

.. code-block:: bash

   run_gadras_isotopeID.exe --detectorDir=Microdetective
                            --inputDir=test_n42
                            --outputDir=test_out -v*

or, equivalent:

.. code-block:: bash

   run_gadras_isotopeID.exe -d ./Microdetective/ -i ./test_n42/ -o ./test_out/ -v*

Example call for the case when a fixed background spectrum spectrum is provided in a separate file:

.. code-block:: bash

   run_gadras_isotopeID.exe --detectorDir=Microdetective --inputDir=test_n42
                            --outputDir=test_out  --backgroundFile=bkg.n42 -v*

or, equivalent:

.. code-block:: bash

   run_gadras_isotopeID.exe -d ./Microdetective/ -i ./test_n42/
                            -o ./test_out/ -b bkg.n42 -v*
