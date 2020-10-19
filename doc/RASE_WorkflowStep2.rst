.. _workflowStep2:

*****************************************
RASE Workflow Step 2: Scenario Definition
*****************************************


The “Scenario Creation” dialog (figure below) is available by clicking the “Create Scenario” button in the main RASE window.

A scenario is defined by specifying some source and background materials. Each material can be quantified in either units of flux in a characteristic photopeak or as a net dose rate induced in the detector by the source. The acquisition time to be simulated, in seconds, must also be specified. Source materials are defined in the top table, and background materials are defined in the bottom table.

When RASE creates sample spectra, the base spectra of the constituent materials are sampled identically regardless of if the material is defined as a source material or background material. The difference between the two is largely a bookkeeping one to facilitate easier plotting and analysis. There is also no difference in how RASE treats source and background materials in terms of calculating isotope identification results for a scenario, *except* in the instance that an isotopic material in the format of XXnnn (as opposed to "Background" or "NORM") is defined in the background; for more detail on this difference, see :ref:`workflowStep6`.

To add a material (usually a nuclide) to the scenario, double-click in the second cell of either the source or the background table.
Select the appropriate entry from the drop-down list. Available material options are defined by the inventory of base spectra
associated with the previously added instruments. If no instruments are defined, no materials will be available to create the scenarios.

The leftmost column of either table indicates if the material is defined in units of flux or in units of dose rate. Upon selection of a material this value defaults to dose rate if there is a base spectrum for the material that has a rase_sensitivity factor defined-- else it defaults to flux.

RASE will not allow the user to define a material/units combination that is not defined in the loaded base spectra. If units are chosen before the material, only materials with a base spectrum containing a relevant sensitivity factor will be available for selection. If the user selects a material first and then attempts to change the units to those which are not reflected in a base spectrum for that material, the material column will reset and a new material must be selected.

The user is free to mix materials that are defined in units of flux and in units dose rate in a single scenario.

Input the dose rate above background (uSv/h), or the flux in a key photopeak (gammas/cm2s), for each material in the third cell of the table (the default value is 0.1 [uSv/h] / [gammas/cm2s] for flux/dose, respectively.
Entering a range of dose rates/fluxes in the format [min]-[max]:[number of steps] will produce multiple scenarios, one with each of the requested dose rates/fluxes. If the user right-clicks on the dose
rate/photopeak flux box, a dialog can be brought up where the user can interactively set a min, max, number of steps, and linear vs logrithmic spacing and RASE will automatically define a range of values.

Use the same sequence to define the background sources present in the scenario, and define the background dose rate/flux (or a range of dose rates/fluxes).

Define the acquisition time in seconds (the default value is 30 sec.). A range of acquisition time extents can be input using the same format as for
the dose rates: [min]-[max]:[step]

Define the number of replications (the default value is 100). This parameter determines how many sampled spectra will be created in this scenario.

Scenarios can be a part of groups for improved workflow organization. By clicking the "Scenario Groups" button in the top left of the scenario creation window, an additional dialog allows the user to define
any number of groups that the scenario (or scenarios) being defined should be a member of. The user can also create new groups through this dialog. If the scenario is not associated with any group, it is
automatically assigned to the "default_group". The group membership of a scenario can be changed at any point after creation. Note that once it has been created a scenario does not need to be a member
of any groups; even if the scenario is removed from all groups, it can still be found in "All Scenario Groups", as selected from the drop-down menu in the main window.

From the main window, right-clicking on a scenario offers several options, which include editing the scenario, deleting the scenario, assigning the scenario to a different group, and making a new scenario (using the scenario dialog)
that uses the currently selected scenario as preset parameters. Multiple scenarios can be selected and can together be deleted or added to different groups. If all selected scenarios are comprised of the same materials, the scenario set
can be duplicated as a set (so long as the user changes one material, the material intensities, or the acquisition time of the new scenarios to prevent exact copies). For example, if the user had created a range of scenarios for one
material and wanted to see how the detector would perform at those same doses for a different material, the user can simply select those scenarios in the main window, choose the option to duplicate the scenarios, and change that
one material to generate a whole new set of scenarios with the desired material.

.. _rase-WorkflowStep2:

.. figure:: _static/rase_WorkflowStep2.png
    :scale: 80 %

    “Add Scenario" dialog.
