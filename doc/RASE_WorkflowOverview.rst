.. _workflowOverview:

**********************
RASE Workflow Overview
**********************


The overall RASE evaluation workflow is shown in the figure below. The
current version of the software implements seamless end-to-end functionality. First instruments are defined and their corresponding base spectra loaded. Scenarios can then be defined to reproduce measurements conditions of interest. Generation of the synthetic spectra (sample spectra) follows which can then be injected into the instrument replay tool for analysis. This analysis can be done "internally" by RASE for replay tool with a command-line interface. Finally the ouput of the identification analysis is loaded into RASE and can be inspected for evaluating the instrument performance.

RASE base spectra library comprises more than 24 different spectroscopic instruments. Access to the base spectra library is given upon request and requires approval. RASE is compatible with most replay tools that provide a command-line interface and batch (by folder) operation.

.. _rase-workflow:

.. figure:: _static/rase_workflow.png
    :scale: 50 %

    RASE analysis workflow and beta-version functionality.
