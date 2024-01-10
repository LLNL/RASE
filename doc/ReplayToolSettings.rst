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
    *  Executable: none - leave empty
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
    *  Executable: none - leave empty
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
    *  Command Arguments: -r INPUTDIR -o OUTPUTDIR [see the replay tool manual for additional command line parameters that can be used here]
* Sampled Spectra n42 Template:
    *  n42 Template File: FLIR_R400_UW-LGH_template.n42
    *  Suffix of input files: .n42
* Identification Results Translator:
    *  Executable: none - leave empty
    *  Command Line checkbox: checked
    *  Command Arguments: INPUTDIR OUTPUTDIR [this is the default entry]


FLIR R425 Replay Tool
=====================
FLIR R425 requires a different replay tool and settings than the previous FLIR instruments tested with the RASE code.
This RASE analysis routine was tested with the 2022 version of the replay tool, v425.22.1.


**Settings**

* Replay Tool:
    *  Executable: r425ReplayTool.exe
    *  Command Line checkbox: checked
    *  Command Arguments: INPUTDIR -o OUTPUTDIR -w [see the replay tool manual for additional command line parameters that can be used here]
* Sampled Spectra n42 Template:
    *  n42 Template File: FLIR_R425_template.n42
    *  Suffix of input files: .n42
* Identification Results Translator:
    *  Executable: none - leave empty
    *  Command Line checkbox: checked
    *  Command Arguments: INPUTDIR OUTPUTDIR [this is the default entry]


FLIR R440 Replay Tool
=====================
FLIR R440 requires a different replay tool and settings than the FLIR Identifinder instruments tested with the RASE code.

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
ORTEC RadEagle and RadEaglet instruments require a different replay tool and settings than the HPGe-based systems. These instructions are for the most current (as of 04/2023) version of the innoRIID RadEagle and RadEaglet replay tool. 

**Settings**

* Replay Tool:
    *  Executable: ReplayTool_3.8.9.exe
    *  Command Line checkbox: checked
    *  Command Arguments: 2048 INPUTDIR/ OUTPUTDIR/
* Sampled Spectra n42 Template:
    *  n42 Template File: ORTEC-RadEaglet_spectrum.n42
    *  Suffix of input files: .n42
* Identification Results Translator:
    *  Executable: none - leave empty
    *  Command Line checkbox: checked
    *  Command Arguments: INPUTDIR OUTPUTDIR [this is the default entry]


ORTEC RadEagle and RadEaglet Replay Tool (Legacy)
=================================================
ORTEC RadEagle and RadEaglet instruments require a different replay tool and settings than the HPGe-based systems. Note that these instructions are for the older version of the replay tool; for the latest replay tool, see above.

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
    *  Executable: none - leave empty
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
    *  Executable: none - leave empty
    *  Command Line checkbox: checked
    *  Command Arguments: INPUTDIR OUTPUTDIR [this is a default entry]


Kromek D5 Replay Tool
=====================
Kromek provides a replay tool for their D5 instrument, called :code:`PCSOffiline`, that is packaged for Linux operating systems.
As of version 170.1.5.7, the replay tool only accepts a single file as input.  To facilitate use within RASE, which
requires processing an entire folder, a wrapper shell script :code:`KromekD5_replaytool_wrapper.sh` is provided in the :code:`tools`.

If you are not running RASE on a unix system, one way to run the replay tool on other machines is to dockerize it.
To facilitate this process, we provide the :code:`Dockerfile-KromekD5` file in the :code:`tools` folder.
Note that it assumes the :code:`PCSOffile.deb` package and the wrapper shell script are in the same directory as the :code:`Dockerfile`.
To create the image, simply run :code:`docker build -t kromek-rt -f Dockerfile-KromekD5 .`

**Settings**

* Replay Tool:
    *  Executable: path to the docker executable e.g. :code:`/usr/local/bin/docker`
    *  Command Line checkbox: checked
    *  Command Arguments: :code:`run --rm -v INPUTDIR:/data/in -v OUTPUTDIR:/data/out kromek-rt KromekD5_replaytool_wrapper.sh /data/in/ /data/out`
* Sampled Spectra n42 Template:
    *  n42 Template File: :code:`Kromek_D5_template.n42`
    *  Suffix of input files: :code:`.csv`
* Identification Results Translator:
    *  Executable: :code:`none - leave empty`
    *  Command Line checkbox: checked
    *  Command Arguments: :code:`INPUTDIR OUTPUTDIR` [this is a default entry]

Note that the Replay Tool command arguments should be entered exactly as described above.
If the replay tool fails to yield results on Windows, and if the replay tool log file says something along the lines of "no such file or directory," try opening the :code:`KromekD5_replaytool_wrapper.sh` file in Notepad++, go to edit -> EOL conversion, and change from CRLF to LF (credit to Vikas Rathore Oct 5, 2018 on Stack Overflow).


CAEN DiscoveRAD Replay Tool
===========================
The CAEN DiscoveRAD replay tool has been tested to work on Windows 10. When running the tool, an additional interrupting pop-up window is generated when analyzing each scenario that cannot be suppressed. As such, it is recommended that when running CAEN DiscoveRAD replay analysis, the user refrains from parallel work to limit interference in the replay tool operation.
Otherwise, regular analysis procedure applies.

**Settings**

* Replay Tool:
    *  Executable: Target.F501.ReplayTool.exe
    *  Command Line checkbox: checked
    *  Command Arguments: :code:`-o OUTPUTDIR INPUTDIR`
* Sampled Spectra n42 Template:
    *  n42 Template File: :code:`C:/Users/czyz1/PycharmProjects/rase/n42Templates/CAEN_DiscoveRAD_template.n42`
    *  Suffix of input files: :code:`.csv`
* Identification Results Translator:
    *  Executable: :code:`none - leave empty`
    *  Command Line checkbox: checked
    *  Command Arguments: :code:`INPUTDIR OUTPUTDIR` [this is a default entry]


GADRAS Full Spectrum Isotope ID (web version)
=============================================
Sandia National Laboratory has released an online version of the GADRAS Isotope ID tool which is publicly available at
`https://full-spectrum.sandia.gov <https://full-spectrum.sandia.gov/>`_.
The tool is very flexible, works with standard RASE-formatted sample spectra, and may be used with any
detector so long as a suitably compatible Detector Response Function (DRF) is specified.

To use Full Spectrum ID as the identification algorithm in RASE, simply select the "Full Spectrum Web ID" option in the :code:`Edit
Replay Software` menu. The web address to access the WebID server is already pre-populated. The user must select the
appropriate DRF from the drop-down list. The updated list can be retrieved by clicking on the corresponding button.
Once configured, RASE will take care of sending spectra to the server and parsing the results automatically.

Spectra supplied to Full Spectrum should contain a secondary background for optimal results.  Please configure
the detector accordingly using the :code:`Edit Detector` dialog.


GADRAS Full Spectrum Isotope ID (standalone version)
====================================================
A standalone version of the GADRAS Full Spectrum Isosope ID is also available as an executable.
This can be run in two modes: (1) as a web server, and (2) as a standard command line replay tool. When run in web
server mode, the tool works equivalent as the one on the public website (described above), but running on the
localhost at `http://127.0.0.1:8002 <http://127.0.0.1:8002>`_.

If the user is using the command line capability, use the settings that follow. The command line tool is made to accept files
one at a time, so a wrapper shell script has been written to accommodate RASE directory structure. The
:code:`FullSpec_replaytool_wrapper.sh` can be found in the :code:`tools`. A corresponding version with extension :code:`.cmd`
can be used on Windows operating system. Note that the path to the executable *must not have any spaces*.

**Settings**

* Replay Tool:
    *  Executable: path to the wrapper e.g. :code:`usr/local/rase/tools/FullSpec_replaytool_wrapper.cmd`
    *  Command Line checkbox: checked
    *  Command Arguments: :code:`/usr/path/to/full-spec.exe INPUTDIR OUTPUTDIR <DRF_name_here>`
* Sampled Spectra n42 Template:
    *  n42 Template File: none - leave empty
    *  Suffix of input files: .n42
* Identification Results Translator:
    *  Executable: :code:`SandiaWebID-CmdLine_ResultsTranslator.exe`
    *  Command Line checkbox: checked
    *  Command Arguments: :code:`INPUTDIR OUTPUTDIR` [this is a default entry]

For the :code:`<DRF_name_here>` field, the user should supply the name of whichever DRF they would like to use with the detector, with
proper capitalization. The user may review which DRFs are available in the drop-down "Instrument DRF" menu in the "Full Spectrum
Web ID" window of the :code:`Edit Replay Software` menu.

To add custom DRFs, a folder must be added to the :code:`/usr/path/to/fullspec_exe/gadras_isotope_id_run_directory/drfs` directory
which contains the following files:

    * :code:`DB.pcf`
    * :code:`Detector.dat`
    * :code:`Rebin.dat`
    * :code:`Response.win`

As for the web version, spectra supplied to Full Spectrum should contain a secondary background for optimal results.  Please configure
the detector accordingly using the :code:`Edit Detector` dialog.


