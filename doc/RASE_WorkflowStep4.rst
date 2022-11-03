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


Advanced actions: Importing sample spectra and experimental data
================================================================

If the user clicks the "Enable advanced actions" checkbox, two buttons will appear alongside the "Generate Spectra" and "Run Replay Tool": the "Import Spectra" and
"Import Replay Results" buttons. Importing spectra allows the user to import experimental data into the RASE workflow for direct comparison to simulated data. To do
this, simply select a detector and a scenario and press the "Import Spectra" button. This will bring up a directory dialog; navigate to the directory that contains
the set of spectra to be imported into RASE and press "Okay". These spectra will be imported into RASE and from that point forward is treated identically to sample
spectra created within RASE. By importing experimental spectra into a scenario for one detector and simulating the spectra using another detector, the user may easily
compare replay results on experimental data with simulated results created via sampling from base spectra. RASE does not mark scenarios or detectors to identify them
as having imported spectra associated with them, so it is left to the user to keep track of which scenarios/detectors have experimentally imported spectra. It is not
necessary to define a separate instrument exclusively for experimental spectra: imported spectra and sampled spectra may co-exist associated with a single instrument.

Note that there are no checks in place that prevent the user from importing spectra that are incorrect. It falls to the user to verify that the live times, dwell times,
dose rates, etc, are the same as those defined in the scenario setup. It also falls to the user to verify that the spectra imported for a detector/scenario combination
is compatible with the replay tool in the same manner as spectra generated in RASE should be. RASE does not check to verify that the number of spectra imported is in
agreement with the number of replications defined by the user, but provided that the number of replications defined for a scenario is greater than the number of spectra
imported for that scenario the RASE workflow should operate normally and correctly.

|

.. _rase-WorkflowStep4:

.. figure:: _static/rase_WorkflowStep4.png
    :scale: 90%

    **Populated main RASE window showing how to generate sample spectra.**
