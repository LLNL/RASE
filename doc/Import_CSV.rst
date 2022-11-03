.. _import_csv:


********************************
Import scenarios from .csv files
********************************

Scenarios may be directly imported from an .xml file through the "Import" button in the main window. However, when desiring to import many scenarios, importing from a .csv file might be more convenient.
When importing from a .csv file, each line represents a scenario. The .csv file can have an arbitrarily large number of scenarios, but can only have up to one source and one background material per scenario. The .csv file should have the following eight key words in the first line, in any order:

    s_fd_mode, s_material, s_intensity, b_fd_mode, b_material, b_intensity, acq_time, replications

This first line should be followed by any number of subsequent lines. Each of these lines should be filled with the following information (in the column associated with the respective header):

    - s_fd_mode: Source Units (DOSE or FLUX)
    - s_material: Source Material
    - s_intensity: Source intensity, in units of μSv/h or :math:`\gamma/cm^2s`
    - b_fd_mode Background Units (DOSE or FLUX)
    - b_material: Background Material
    - b_intensity: Background intensity, in units of μSv/h or :math:`\gamma/cm^2s`
    - acq_time: Scenario acquisition time
    - replications: Number of scenario replications

Of these terms, only acq_time and replications are absolutely necessary. If no source (or background) material is desired, leave the three source (or background) columns blank.

Each scenario line must correspond to a unique scenario.

Upon import, a new scenario group is created and labeled using the name of the imported file.
