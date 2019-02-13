.. _introduction:

************
Introduction
************


The Replicative Assessment of Spectrometric Equipment (RASE) methodology is a semi-empirical approach to generating
synthetic gamma-ray spectra for injection into a radionuclide identification algorithm of a vendor-provided radiological detection
system. RASE facilitates studies of the spectroscopic device performance and a quantitative assessment of its capabilities
to correctly distinguish and identify isotopes of interest in simulated scenarios. Deployment of this methodology
reduces the need for full-scale experimental tests, and permits investigation of hard-to-implement measurement situations.
Because of the semi-empirical nature of the analysis, the RASE approach allows factoring in both the physical effects on the
spectrometer response, such as the detector package construction, and various influences (temperature, EMT, count rate,
etc.). This is achieved by acquiring a set of high-accuracy Base Spectra from individual isotopic sources with an actual
instrument. These spectra can be subsequently down-sampled and combined to generate large sets of synthetic spectra (called Sampled Spectra) simulating data
acquisition at a variety of dose rates and dwelling times.

The RASE methodology is described in detail in [RASE_IEEE]_. Some validation of the methodology is reported in [RASE_validation]_. Additional validation work is ongoing. The RASE software described in this manual implements the RASE methodology in an intuitive and user-friendly interface.

With any feedback, bug reports, observations and recommendations,
please contact the LLNL development team at rase-support@llnl.gov
