.. _workflowStep4:

**********************************************
RASE Workflow Step 4: Generate Sampled Spectra
**********************************************


Confirm that the desired instruments and scenarios are present and properly specified in the appropriate tables.
If necessary, entries in the “Scenarios” and “Instruments” tables can be modified or deleted by the user by double-clicking
on the corresponding row or using the context menu.

At this point, RASE can be used to generate sampled spectra. To do this, execute the following steps:

#.  Highlight one or more entries in the “Instruments” table

#.  Highlight one or more entries in the “Scenarios” table

#.  At this point, there are two possible routes to proceed through the workflow execution:

  a. Press the “Gen Sampled Spectra” button that becomes available in order to generate the sampled spectra.

  b. Press the "Run Scenario" button that becomes available in order to sequentially execute the entire workflow (generate sample spectra, run replay, and run translator) for all selected scenarios and instruments without additional input from the user. This option only becomes available if all of the selected instruments have command line-based replay tools.

  The rest of this guide will work under the assumption that the option (a) was selected, and the steps of the workflow are to be executed manually. However, it should be noted that the workflow will end in the same place, regardless of if the workflow is executed manually (option a) or using the "Run Scenario" button (option b).

If a selected instrument does not have base spectra for materials present in the scenario, the “Gen Sampled Spectra” and "Run Scenario" buttons remain unavailable. The missing materials for the instrument will be highlighted red in the “Scenarios” table.

The directory containing the resulting sampled spectra can be accessed by pressing the “Sample Spectra Dir” button.
If an n42 template file was specified in the replay tool settings associated with the current instrument, then a second
directory will also be present containing the sampled spectra in the format ready for injection in the specified replay
tool.

The directory containing data associated with the specific scenario can be accessed using the context menu in the
"Scenarios" table. An instrument must be selected in order for this option to become available.


.. _rase-WorkflowStep4:

.. figure:: _static/rase_WorkflowStep4.png
    :scale: 90%

    Populated main RASE window showing how to generate sample spectra.
