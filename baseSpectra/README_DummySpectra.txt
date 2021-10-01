The Dummy spectra folder has 8 spectra. They were sourced from a theoretical device that calls for a main and a secondary spectrum.

The spectra are named for the type of dummy spec in each of the two spectrum spaces: the first name is for the primary spectrum, and the second name is for the secondary spectrum. So for example, "DUMMY_M001_Delta_Flat" contains a delta function in the main spectrum and a flat region 500 channels wide in the secondary spectrum.

All spectra have different RASE sensitivity factors, but are calculated such that they were "taken" with a dose rate of 0.1 uSv/hr. Creating scenarios in RASE with each source specified to have a dose rate of 0.1 uSv/hr and a dwell time of 1200s should reproduce the base spectra (with some statistical fluctuation).