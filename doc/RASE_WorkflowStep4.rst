.. _workflowStep4:

************************************************************
RASE Workflow Step 4: Define the Replay Tool and Translators
************************************************************

Before the "Run Replay Tool" button on the main window can be used, the instrument must have its replay tool specified.

Two types of replay tools can be implemented in the RASE workflow:

*  Command line-based tools can be executed directly from the RASE main window

*  Stand-alone replay tools that should be manipulated outside of the RASE software

In addition to the replay tool, the user must specify an instrument specific n42 template and a results translator.
See :ref:`requirements` for more details on these.
The user should be aware of the instrument manufacturer's instructions on replay tool operation and the command line syntax requirements.

To define the replay tool:

*  Double-click on an entry in the “Instruments” table

*  In the “Edit Detector” window, click the “New” button near the “Replay Tool” field.

*  In the “New Replay Software” dialog, use the “Browse” button to navigate to the command line replay tool executable. Make sure that the “Command line” checkbox is selected.

*  In the “Replay Settings:” field, type in the command line parameters (obligatory). The RASE software will automatically substitute the INPUTDIR and OUTPUTDIR entries with the path to the directories where the sampled spectra and replay tool results are located.

*  Similarly, use the "Browse" buttons to identify the path to the “Replay Tool n42 Input Template” and the “Replay Results Translator.”


Once the replay tool is defined, the “Run Replay Tool” and "Run Results Translator" buttons become available in the RASE main window.
The entry in the “Instruments” table should now list your newly defined replay tool.

Replay tool settings can be edited at any time by double-clicking in the “Instruments” table.

Once the replay tool is defined, it can be assigned to any other instrument by using a drop-down menu near the “Replay”
field in the “Edit Instrument” window.



.. _rase-WorkflowStep4:

.. figure:: _static/rase_WorkflowStep4.png
    :scale: 75 %

    “Add Detector” dialog.