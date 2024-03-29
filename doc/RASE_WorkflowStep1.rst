.. _workflowStep1:

*******************************************
RASE Workflow Step 1: Instrument Definition
*******************************************


The “Add instrument” dialog window (Figure below) is called by clicking the “Add Instrument...” button in the main RASE window.

The user is required to enter an arbitrary name for the instrument in the top-left dialog. All other entries in this area are optional.

To associate a set of base spectra with the new instrument, press the “Add Base Spectra” button in the top-right area of the dialog. In the new window that pops up, navigate to the directory that contains the base spectra in the appropriate .n42 format and press the “Select Folder” button. Review the base spectra metadata and import details, then press “OK”.

Secondary spectra are sometimes required by certain replay tools; these secondary spectra may be pre-recorded background spectra, internal source spectra, or calibration spectra. The RASE software will automatically recognize and import second spectral data entries present in the base spectra files. RASE expects each spectrum to have one of five class codes: 

    1: Foreground

    2: Background  

    3: Calibration
    
    4: IntrinsicActivity

    5: NotSpecified

If more than one of a given classcode is present in the spectrum, RASE will use the first of that classcode. If the measurement does not have a classcode, RASE will assign the classcode "UnspecifiedSecondary". Note that RASE assumes all the imported base spectra have identical secondary spectra, and as such only saves the secondary spectra included in the first base spectrum file. 

The user must select how secondary spectra should be handled via the radio buttons in the group box in the bottom left of the dialog labeled "Secondary Spectrum Handling".
By selecting the "no secondary spectrum" radio button, the synthetic spectra generated by RASE will not include any secondary spectrum.  Selecting the second radio button (labeled "secondary as background spectrum") tells RASE to include a secondary spectrum as the instrument background. In this case, one of three sources of secondary spectra should be specified:

    1: The user may select one of the base spectra that has been associated with the detector to serve as the secondary spectrum. This option mimics the case where a specific background was acquired prior to executing the measurement campaign, which might be in a different location and consequently have a different background.

    2: The secondary spectrum will be automatically populated by the background(s) that are used to define a "scenario" (combinations of sources and backgrounds that can be paired with an instrument to simulate spectra; scenarios are described in more detail in the next section). If the user defines more than one source of background, the secondary spectrum will be a combination of the multiple sources, weighted according to their respectively defined intensities. In this case, the secondary spectrum will be different for each scenario (as opposed to the same across all scenarios simulated for a certain detector). If this option is selected, the user may not run a scenario where background is not defined.

    3: The secondary spectrum will be a direct copy-and-paste of one of the secondary spectra included in the base spectra files. Upon selecting this option, the user must select the classcode of the spectrum to be used in the "Secondary spectrum" drop-down menu.

The user is also provided with the option to specify the dwell time of the background spectrum and whether a Poisson resampling of the background should occur with every new spectrum being generated by RASE.

In addition to secondary background treatment, the user may indicate that an internal source is present. In this instance, the "Add secondary (intrinsic activity) to sample spectra" box should be checked. The spectrum associated with the classcode specified in the "Intrinsic Source Classcode" dropdown menu will then be sampled/scaled (based on scenario acquisition time) and added to any generated sample spectra, in addition to the sources specified in a scenario definition. In the case of dealing with internal sources, it is important that the secondary spectrum is an accurate representation of what the main detector would record *from the calibration source alone*, with no additional background signature. This is not always the case: the internal calibration source may be measured using a secondary detector and/or may not be uniquely separable from the background base spectrum. In instances such as this, the user should follow the guidance described in the ":ref:`intrinsic_source_handling`" section. 

Once base spectra are loaded, they can be quickly reviewed within RASE by double-clicking on a material name within the "Edit Detector" dialog. A separate plotting dialog will be displayed.

All other entries in the “Add Instrument” dialog can be modified later in the workflow and are covered later in this documentation.

|

.. _rase-WorkflowStep1:

.. figure:: _static/rase_WorkflowStep1.png
    :scale: 33 %

    **“Add Instrument” dialog.**
