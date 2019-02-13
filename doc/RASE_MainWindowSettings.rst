.. _mainWindow:

*****************************
RASE Main Window and Settings
*****************************


The RASE main window appears when the executable is launched, and is depicted in the figure below.

Prior to executing the RASE workflow, the user is encouraged to define a custom work directory where the RASE-generated
data (sampled spectra, replay tool outputs, and analysis reports) will be located. The work directory can be defined
using the “Preferences” dialog accessible through the “Setup” menu. The default location of data for Windows machines
is :code:`C:\Windows\Users\[UserName]\RaseData`  If the RASE work directory is modified, RASE should be restarted in order
for the change to take effect.

The RASE work directory can be accessed at any time from the RASE main window by clicking on the “Sample Spectra Dir”
button in the bottom-right corner.

Additional settings available in the “Preferences” dialog include the choice of the sampling algorithm and the current
correspondence table. These can be accessed and modified at any stage of the analysis workflow.

Additional options in the “Setup” menu include Replay Tool and the Correspondence Table management. These can be accessed
and modified at any stage of the analysis workflow.

The "Tools" menu contains a variety of add-on functionality (some under development) for extending RASE capabilities.
In particular, the user can fix the random seed number in order to generate identical spectra sets on different machines (for example, for a parallel independent analysis).
A tool for creating base spectra will be introduced in 2019. Streamlining complex evaluations, such as the Minimal Detectable Amount (MDA), and dynamic, in-motion
measurement scenarios are also under development.

The main window provides access to the instrument and scenario definitions. Once these are defined, the steps of the RASE workflow are executed using buttons in the bottom-right "Actions" area.

The color-coding of the alphanumeric scenario IDs in the RASE main window corresponds to different stages of the RASE
workflow. It is activated when an instrument is selected:

*  Black: the  scenario was defined, but sample spectra have not yet been generated.

*  Orange: Sample spectra have been generated for this instrument and scenario combination. Replay tool has not been yet executed.

*  Green: The replay tool has been successfully executed for this instrument and scenario combination.


.. _rase_mainWindow:

.. figure:: _static/rase_mainWindow.png
    :scale: 75 %

    RASE main window at the first start without pre-defined instruments or scenarios.
