.. _base_spectra_creation_tool:

**************************
Base Spectra Creation Tool
**************************

A *Base Spectra Creation Tool* was introduced in RASE to help develop new base spectra from data acquired with an instrument. This page provides some details on how to use this tool.  For an overview of the process and information about what data are necessary for generating base spectra, see :ref:`create_base_spectra`

The Base Spectra Creation dialog can be accessed from the main RASE menu by selecting *Tools >> Base Spectra Creation*.

At the top of the dialog, enter the four-character manufacturer abbreviation and the three-character alphanumeric model number abbreviation for the instrument for which base spectra are being produced.

The *Add Files from Folder...* button allows the user to select a directory from which to import the long-dwell measurements that have been collected and will be used for generating the base spectra. All files with extension ``.n42`` within the selected folder will be imported. The files will appear in the table at the center of the dialog window. The button can be used multiple times to add files from multiple directories. Note that while only the filename is shown in the first column, the data folder name is also recorded and is shown in a tooltip when hovering the mouse on each filename.

Once the files are loaded in the table, additional information must be provided. The table cells in the columns *Source ID*, *Description*,  *Exposure Rate*, and/or *Flux* must be entered in correspondence to each listed file. The *Source ID* label should be entered according to the naming convention listed in :ref:`base_spectra_naming_convention`. The *Description* label is optional and is used to describe the shielding scenario or other relevant measurement conditions, or to distinguish between similar sources (e.g. different types of "NORM" sources). Examples of *Description* labels are "5mmSteel" or "KittyLitter" or "70mmPMMA". Finally the measured net dose rate, in μSv/h should be entered in the *Exposure Rate* column. Currently the software assumes that this dose is for the source-only term i.e. the dose rate for the background has been already subtracted. For the background file, enter the measured background dose rate.

The tools provides capabilities to import and export the main table as a CSV for convenient editing in an external spreadsheet software.

Since the instrument measurements inevitably include the background contribution to the measured spectra, the user must tell the software which of the loaded files should be used to perform the background subtraction. This can be done by selecting the appropriate row in the table and then clicking the *Set Selected File as Background* button. The selected row will be highlighted to indicate the selection.

Once all the information is entered, the software is ready to create RASE-compatible base spectra when the user press the *Create* button. The software will create the base spectra in the folder specified in the *Output Folder* field. Each base spectrum will have the automatically-generated filename indicated in the *Base Spectrum Name* column in the table. These files can then be loaded in RASE for further use as described in :ref:`workflowStep1`.

Note that the tool currently support most instrument file formats in the n42 data format. Extension to a broader set of file formats is planned. Unless a *Spectrum ID* or a *Sequence Number* are specified in the corresponding entry on the dialog, the software assumes that the source spectrum is the foreground source measurement from which the base spectrum must be created. It is recommended that each collected measurement contains only one foreground spectrum in addition to any secondary spectrum (background and/or intrinsic source) that are routinely present for that given instrument. Secondary spectra will be preserved in the base spectra creation process.