.. _workflowStep2:

*****************************************
RASE Workflow Step 2: Scenario Definition
*****************************************


The “Scenario Creation” dialog (figure below) is available by clicking the “Create Scenario” button in  the main RASE window.

A scenario is defined by specifing some background and source materials, each inducing a certain dose in the detector, and by the acquisition time.

To add a material (usually a nuclide) to the scenario, double-click in the first cell of the table in the top-left area of the window.
Select the appropriate entry from the drop-down list. Available material options are defined by the inventory of base spectra
associated with the previously added instruments. If no instruments are defined, no materials will be available to create the scenarios.

Input the dose rate above background (uSv/h) for each material in the second cell of the table (the default value is 0.1 uSv/h). 
Entering a range of dose rates in the format [min]-[max]:[step] will produce multiple scenarios, one with each of the requested dose rates.

Use the same sequence to define the background sources present in the scenario, and define tha backgroind dose rate (or a range of dose rates).

Define the acquisition time in seconds (the default value is 30 sec.). A range of acquisition time extents can be input using the same format as for
the dose rates: [min]-[max]:[step]

Define the number of replications (the default value is 100). This parameter determines how many sampled spectra will be created in this scenario.


.. _rase-WorkflowStep2:

.. figure:: _static/rase_WorkflowStep2.png
    :scale: 75 %

    “Add Scenario" dialog.
