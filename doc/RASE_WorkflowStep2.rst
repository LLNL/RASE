.. _workflowStep2:

*****************************************
RASE Workflow Step 2: Scenario Definition
*****************************************


The “Scenario Creation” dialog (figure below) is available by clicking the “Create Scenario” button in the main RASE window.

A scenario is defined by specifying some background and source materials. Each material can be quantified in either units of flux in a characteristic photopeak or as a net dose rate induced in the detector by the source. The acquisition time, in seconds, must also be specified.

To add a material (usually a nuclide) to the scenario, double-click in the second cell of the table in the top-left area of the window.
Select the appropriate entry from the drop-down list. Available material options are defined by the inventory of base spectra
associated with the previously added instruments. If no instruments are defined, no materials will be available to create the scenarios.

The leftmost column of this table indicates if the material is defined in units of flux or in units of dose rate. Upon selection of a material this value defaults to dose rate if there is a base spectrum for the material that has a rase_sensitivity factor defined-- else it defaults to flux.

RASE will not allow the user to define a material/units combination that is not defined in the loaded base spectra. If units are chosen before the material, only materials with a base spectrum containing a relevant sensitivity factor will be available for selection. If the user selects a material first and then attempts to change the units to those which are not reflected in a base spectrum for that material, the material column will reset and a new material must be selected.

The user is free to mix materials that are defined in units of flux and in units dose rate in a single scenario. 

Input the dose rate above background (uSv/h), or the flux in a key photopeak (gammas/cm2s), for each material in the second cell of the table (the default value is 0.1 [uSv/h] / [gammas/cm2s] for flux/dose, respectively.
Entering a range of dose rates/fluxes in the format [min]-[max]:[step] will produce multiple scenarios, one with each of the requested dose rates/fluxes.

Use the same sequence to define the background sources present in the scenario, and define the background dose rate/flux (or a range of dose rates/fluxes).

Define the acquisition time in seconds (the default value is 30 sec.). A range of acquisition time extents can be input using the same format as for
the dose rates: [min]-[max]:[step]

Define the number of replications (the default value is 100). This parameter determines how many sampled spectra will be created in this scenario.


.. _rase-WorkflowStep2:

.. figure:: _static/rase_WorkflowStep2.png
    :scale: 20 %

    “Add Scenario" dialog.
