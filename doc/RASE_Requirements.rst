.. _requirements:

*****************************
Requirements for Running RASE
*****************************

Requirements
============

The RASE software is intended to be compatible with all mainstream platforms and operation systems.  The binary executable works on Windows 7/10 systems without a need for installation procedure, or
downloading additional libraries, or requiring administrator's permissions. RASE is coded in Python and can be compiled to run also on MacOS or Linux operating systems.

In order to effectively utilize all functions of the RASE software, the user must locate the following additional
data sets and utilities:

*  **Base spectra** for the instruments under evaluation. The base spectra must be defined in the \*.n42 format and should follow the RASE standard requirements. See :ref:`create_base_spectra` The current library of base spectra is not included with the executable and should be requested separately.
*  **Replay tools** which are stand-alone programs that replicate the radioisotope identification software deployed on the instrument. These are generally provided by the manufacturer, and can be executed from the command line or have a native graphical user interface.
* **Instrument-specific n42 template** that are used by RASE to generate sample spectra in the native format used by the vendor replay tool. See :ref:`n42_templates` for details on creating a template for a new instrument.
*  **Results translators**: an executable program for converting replay tool outputs to a format compatible with RASE. If the replay tool output is already in RASE format, a results translator is not required.  Results translators for some instruments have already been developed and are included with the RASE distribution. If you need a translator for a specific instrument or a replay tool, please contact the RASE developers.


Good Practices and File Locations
=================================

*  Create a dedicated directory for the RASE software, and place the executable inside.
*  Create the following subdirectories (names are arbitrary), and place the appropriate content there:

	*  subdirectory for base spectra;
	*  subdirectory for replay tools;
	*  subdirectory for the correspondence table and its versions;
	*  subdirectory for translators.

*  Upon the first execution of the software, navigate to the Setup --> Preferences menu and set the "RASE Data Directory" field to a working directory where you would like to store RASE output results. Then close RASE and restart it for the change to take effect.

*  The software will automatically create a subdirectory in the working directory named "SampledSpectra" where all synthetic data and analysis results will be located.

*  Clicking on the "Sampled Spectra Dir" button in the main window immediately opens its content in a separate OS-based file explorer window.

*  Right-click on a specific scenario with an instrument selected to immediately open a corresponding directory with all data related to this scenario in a separate file explorer window.

*  RASE maintains a database in a sqlite file inside the RASE data directory. This file should not be deleted or modified by the user.
