.. rase-gadras_integration:


***************************
RASE and GADRAS Integration
***************************

With the release of GADRAS version 19.3.3, users have been granted access to a python version of the API. This makes it possible to call various GADRAS capabilities directly from custom python scripts. One such capability is generating spectra for an instrument described by a detector response function (DRF), which can be used to supplement a RASE workflow in various ways. For example, a user may want to compare several instruments but lack the base spectra for one of the detectors they are interested in, or they may have data for an instrument but may be missing base spectra for one or two sources they are interested in. GADRAS can be used to simulate the response for that detector, and RASE can convert the resulting pcfs into base spectra. 

One of the most obvious use cases is the desire to replicate the base spectra set of an existing detector with another detector which is simulated in GADRAS in order to compare the two. To support this, the :code:`gadras_clone_detector.py` script is included with the distribution of RASE in the `tools` folder. Though the user must modify or write their own python script to implement the functionality, said implementation is fairly straightforward. The script contains one function, :code:`clone_detector_yaml()`, which takes as arguments:

	* an RASE detector :code:`.yaml` file (exported from an existing RASE session)
	* the path to the drf for the instrument the user wants to model
	* the path to the local GADRAS installation. 

The function will sift through the RASE detector :code:`.yaml` file, identify all source names, and simulate all those sources for the user-specified DRF. The output detector responses will automatically be converted into base spectra .n42 files, which the user can then load into RASE to define an detector. The script will only be able to simulate source names it can understand: for example, the script will not work if the detector :code:`.yaml` file has a source by the name of "MyPocketCs137," and will simply skip over the source (unless the user specifies a :code:`force=True` argument, in which case the code will crash if it encounters a source name it does not recognize.). Because the script is only looking for source names, and no other information about the sources, the user is freely able to modify the source names in the :code:`.yaml` file to generate any number of desired sources.

The spectra are simulated with an assumed standoff of 100 cm. All base spectra are all yielded in units of dose only. 