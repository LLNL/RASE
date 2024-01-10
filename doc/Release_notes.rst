.. _release_notes:

******************
RASE Release Notes
******************

RASE v2.4
=========

- Introduce detector import/export functionality
- Enable instrument cloning
- Allow users to rename detectors/replay tools
- Added a base spectrum creation wizard
- Expanded base spectrum template library
- Sample spectra can now be summed for visualization, comparison, and export
- Improved secondary spectrum handling

    - Can simultanously define on-board background and internal source spectrum
    - Base spectra can now include multiple secondaries
    - User can specify dwell time and sampling behavior of secondary background

- Improve compatibility with FullSpec WebID replay tool

    - Better DRF selection
    - Point web address to the appropriate url

- Export results improvements

    - Include detailed ID results
    - Export results into JSON format

- Automatic translation of isotope ID results for FLIR, Symetrica, Kromek, and RadSeeker replay tools, as well as instruments outputting in the standard n42-2011 format.
- Include python script compatible with GADRAS 19.3.3 API which creates base spectra for a new user-specified instrument from the source list in an exported RASE detector file.
- Various bug fixes
- Documentation updates


RASE v2.3
=========

- Integration with Full Spectrum Web ID directly from RASE
- Base spectra creation tool refactor:

    - config-file based for ease of use
    - added handling of PCF files
    - ingestion of PeakEasy/Interspec output

- Improved robustness of S-curve fit
- Users can manually adjust S-curve fit parameters from the GUI
- Dose-to-distance conversion in plots and scenario creation
- Initial handling of background with inseparable internal source
- Base spectra with different calibration coefficients are now acceptable


RASE v2.2
=========

- Improved plotting capabilities

  - 1D histograms
  - 3D results heat maps

- Isotope ID frequency analysis and plotting
- Extensive update of base spectra collection guidance documentation
- Added Kromek D5 replay tool documentation, template, and translator
- Improvements to development and testing capabilities

  - Unit test suite for developers

- Various bug fixes
- Documentation updates


RASE v2.1
=========

- Better secondary spectrum handling

  - Internal background can now be taken directly from scenario definition or from specific base spectrum

- Influences redesign

  - User can now define energy resolution degradation
  - Calibration coefficients and energy resolution terms can vary over time to model environmental effects

- A set of "code evaluation" base spectra with standard shapes, such as "delta", "flat", and "sawtooth" are now included
- Weighted F-score
- Import of experimental spectra to utilize the RASE workflow
- Improved internal project switching
- Improved internal spectra viewer
- Statistics on detailed ID results
- Various bug fixes
- Documentation updates, including GADRAS isotope ID replay tool documentation


RASE v2.0
=========

- Automated S-curve generation tool added

  - Automatic S-range finding and high statistics scenario creation
  - Arbitrary number of static backgrounds (e.g.: masking scenarios)
  - Regular and inverted S-curves

- Improved plotting options
- Scenario group redesign:

  - Scenarios can now exist in multiple groups simultaneously
  - Bulk scenario selection for group changes
  - Scenarios can be created based on already existing scenarios
  - Groups can be added and deleted freely

- Automatic scenario range generation tool
- Streamlined import of scenarios defined in .csv files
- Various bug fixes
- Documentation updates


RASE v1.2
=========
- Improved scenario results table providing:

  - More results information
  - User-customizable column display settings
  - Sorting capabilities
  - Source separation for multi-isotope scenarios

- Multi-instrument selection/scenario execution
- Full workflow execution via single button
- Addition of flux sensitivity unit
- Generic plotting features implemented
- S-curve fitting
- Various bug fixes
- Documentation updates


RASE v1.1
=========

- Base Spectra Creation Tool
- Most file/folder browsing dialogs now open in the last visited folder
- Replay tools details can be edited by double-clicking an entry directly in the Manage Replay Tools dialog
- Scenario group selection is retained across operations
- Improved sorting of the results table
- Updated documentation
- Other minor bug-fixes and clean-up


RASE v1.0
=========

- New background treatment in the workflow
- Compatibility with instruments from the INL-2018 data collection event, integration of replay tools from various vendors
- Improved Correspondence table and results analysis logic
- Added random seed control
- Refactored file handling, more formats for base spectra and results files are accepted
- Coded base spectra generation methods
- Extended the "Help" section with instructions and examples
- Multiple code and UI modifications to improve the workflow
- Extensive bug fixes and error intercepts
