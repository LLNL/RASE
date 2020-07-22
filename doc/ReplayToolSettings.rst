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
R400 analysis uses the same replay tool and settings as the IdentiFinder-2 .
R400 base spectra and the RASE analysis routine were tested with the 2018 version of the replay tool.

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
