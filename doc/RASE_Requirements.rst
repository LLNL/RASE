.. _requirements:

*****************************
Requirements and Installation
*****************************

Requirements
============

The RASE software is intended to be compatible with all mainstream platforms and operation systems.  The binary executable works on Windows 7/10 systems without a need for installation procedure,
downloading additional libraries, or requiring administrator's permissions. RASE is coded in Python and can be compiled to run also on MacOS or Linux operating systems.

In order to effectively utilize all functions of the RASE software, the user must have acces to the following additional
files and utilities:

*  **Base spectra** for the instruments under evaluation. The base spectra must be defined in the \*.n42 format and should follow the RASE standard requirements. See :ref:`create_base_spectra` The current library of base spectra is not included with the RASE distributable version and should be requested separately. A set of example base spectra is provided with the distributable for the workflow testing and demonstration.
*  **Replay tools** which are stand-alone programs that replicate the radioisotope identification software deployed on the instrument. These are generally provided by the manufacturer, and can be executed from the command line or have a native graphical user interface. A demo replay tool is provided with the RASE distributable version for testing purposes.
*  **Instrument-specific n42 templates** that are used by RASE to generate sample spectra in the native format used by the vendor replay tool. See :ref:`n42_templates` for details on creating a template for a new instrument. Templates for some compatible instruments are provided with the RASE distributable version.
*  **Results translators**: an executable program for converting replay tool outputs to a format compatible with RASE. If the replay tool output is already in RASE format, a results translator is not required.  Results translators for some instruments have already been developed and are included with the RASE distribution. If you need a translator for a specific instrument or a replay tool, please contact the RASE developers. Details on the format of the identification results files are provided in :ref:`results_format`.


Installation and Getting Started
================================

*  Create a dedicated directory for the RASE software, and place inside it the RASE executable along with the enclosed directories.
*  Make sure that the following subdirectories (names are arbitrary), and the appropriate content are present along with the executable:

	*  subdirectory for base spectra;
	*  subdirectory for replay tools;
	*  subdirectory for the correspondence table and its versions;
	*  subdirectory for translators.

*  Upon the first execution of the software, navigate to the Setup --> Preferences menu and set the "RASE Data Directory" field to a working directory where you would like to store RASE output results. Then close RASE and restart it for the change to take effect.

*  The software will automatically create a subdirectory in the working directory named "SampledSpectra" where all synthetic data and analysis results will be located.

*  Clicking on the "Sampled Spectra Dir" button in the main window immediately opens its content in a separate OS-based file explorer window.

*  A correspondence table is required in order to view the isotope identification results. An empty correspondence table (just a name and no content) is sufficient to start the analysis. Navigate to the Setup --> Preferences dialogue and create a table or select an existing one.

*  RASE maintains a database in a sqlite file inside the RASE data directory. This file should not be deleted or modified by the user.

*  A human-readable log text file "rase.log" will be created in the working directory. It will record only information pertaining to errors encountered during the code operation. Please include this file when reporting errors to RASE developers.
