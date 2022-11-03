.. _dynamic_requirements:

*****************************
Requirements and Installation
*****************************

Distribution and Operation
==========================

Dynamic RASE is written in python, and is open source. The source code can be accessed in the "dynamic" branch of the repository at https://github.com/LLNL/RASE.

Despite heavily borrowing from the Static RASE code, the current v1.0 release is not natively accessible from the RASE GUI nor does it seamlessly link into the Static RASE workflow. This means that Dynamic RASE can be used completely independently from Static RASE while remaining intimately tied by approach and methodology. The source code that is found on the Dynamic RASE Github branch exclusively includes the files necessary to compile and run Dynamic RASE.

Like Static RASE, Dynamic RASE is intended to be compatible with all mainstream platforms and operating systems. The binary is currently distributed as a Windows executable, but because it is coded in python it can be compiled from source to run on MacOS and Linux operating systems. The windows binary executable has been tested in Windows 10, and can be run without any additional downloads or permissions. Instructions for compilation can be found on the Github distribution page in the "compilation_instructions.txt" file.


Requirements
============

In order to effectively utilize all functions of the Dynamic RASE software, the user must have access to the following additional files and utilities:

*  **Base spectra** for the instruments under evaluation. The base spectra must be defined in the \*.n42 format and should follow the Dynamic RASE standard requirements. See :ref:`dynamic_create_base_spectra`. The current library of dynamic base spectra is not included with the Dynamic RASE distribution and should be requested separately, but a set of example dynamic base spectra is provided with the distributable for workflow testing and demonstration.
*  **Replay tools** which are stand-alone programs that replicate the radioisotope identification software deployed on the instrument. These are generally provided by the manufacturer, and can be executed from the command line or have a native graphical user interface. A demo replay tool is provided with the RASE distribution for testing purposes.
*  **Instrument-specific n42 templates** that are used by RASE to generate sample spectra in the native format used by the vendor replay tool. See :ref:`dynamic_n42_templates` for details on creating a template for a new instrument specifically for dynamic instruments; instructions for creating templates for static systems can be found in the Static RASE manual. Templates for some compatible instruments are provided with the RASE distribution.
*  **Results translators**: are executable programs for converting replay tool outputs to a format compatible with RASE. If the replay tool output is already in RASE format, a results translator is not required.  Results translators for some instruments have already been developed and are included with the RASE distribution. If you need a translator for a specific instrument or a replay tool, please contact the RASE developers. Details on the format of the identification results files are provided in :ref:`dynamic_output`.


Installation and Getting Started
================================

*  Create a dedicated directory for the Dynamic RASE software to extract the Dynamic RASE archive, which contains the executable and various important subdirectories. By default, all the paths used by Dynamic RASE will be relative to the location of the Dynamic RASE executable using the structure seen when the archive is first extracted.

*  Make sure that the extracted archive contained the executable and the following files and subdirectories (names are arbitrary) with the appropriate contents:

    *  several .yaml files (see :ref:`dynamic_operation` for details on these files);
    *  subdirectory for base spectra;
	*  subdirectory for replay tools;
	*  subdirectory for translators.

*  Dynamic RASE maintains a database in a sqlite file inside the Dynamic RASE data directory. This file should not be deleted or modified by the user.

*  Output from Dynamic RASE is placed in a "tests" directory created in the working directory. This folder is created at runtime.
