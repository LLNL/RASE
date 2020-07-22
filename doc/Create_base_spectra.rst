.. _create_base_spectra:

***************************************
How to create new base spectra for RASE
***************************************


Four steps are required to produce a new base spectra for a given instrument for use within RASE:

#. Obtain high statistics measurement of the source and background spectra at a known dose rate/photopeak flux.
#. Process the measured spectra to extract the source term
#. Calculate the ``rase_sensitivity/flux_sensitivity`` factor
#. Produce a properly formatted n42 file for ingestion in RASE, either manually or using the :ref:`base_spectra_creation_tool`

For additional details, refer to [RASE_standard]_

Obtain high-statistics source spectra
=====================================

A measurement should be performed usually in well-controlled laboratory conditions with one or more radioactive sources. Adherence to the following recommendation will result in high-quality base spectra:

- The measurement scenario (source strength, source-instrument distance, shielding) should be chosen such as to ensure that a significant fraction of the count rate in the instrument arises from the source term alone. If possible, the dose rate from the source should be at least 5 times above background. If measuring the source in units of flux, the net counts in the photopeak of interest should be at least 350-550.
- Verify that no significant pile-up or dead time is present in the instrument. Ideally dead time should be limited to no more than 2%.
- The instrument’s orientation with respect to the source shall be the same as how it is intended to be used in the field.
- Collect sufficient statistics so that the relevant source peaks are known to high confidence. Acquisition times for raw spectra shall be adjusted such that the base spectra they are processed into contain at least ten times the number of counts contained in any individual sample spectrum expected to be generated from them. This should be done according to the formula: :math:`R_0 \cdot T_0 > 10 \cdot R_S \cdot T_s` where :math:`R_0` is the dose rate/photopeak flux produced by the base material at the distance at which the base spectrum was collected, :math:`T_0`	is the live time of the base spectrum, :math:`R_s`	is the maximum dose rate/photopeak flux to be simulated in the sample spectra, and :math:`T_S` is the maximum live time to be simulated in the sample spectra


A high-statistics long-dwell (at least 1 hour) background spectrum should also be acquired in the same experimental conditions as for the source measurements.

Carefully measure and record the dose rate with a calibrated instrument (usually an ionization chamber) or the photopeak flux with and without the source.

If measured spectra cannot be obtained, simulated spectra can also be used with RASE.


Process measured spectra
========================

In order to allow for generation of varying scenarios with different sources and dose rates, RASE needs spectra that reproduce the instrument response to the radiation arising from the source term alone. For this reason, the background and any spurious component (e.g. intrinsic calibration source) must be removed from the collected base spectra.

The resulting background-subtracted spectrum can be obtained through channel-by-channel subtraction of measured source and background spectra after normalizing both spectra by live time. Re-binning should be performed if needed to account for any gain shift between source and background spectra. If an intrinsic calibration source is visible in the measured source spectrum, it should be also subtracted. When generating base spectra of natural radiation background, background subtraction should not be performed.

.. _compute_rase_sensitivity_factor:

Compute ``rase_sensitivity/flux_sensitivity`` factor
====================================================

The RASE sensitivity factor :math:`S_{\text{RASE}}` encodes all information necessary to properly scale the base spectra for different source dose rates and acquisition times.  It is computed according to the following equation:

.. math::

   S_{\text{RASE}} = \frac{\text{net count rate [cps]}}{\text{gamma dose equivalent rate }[\mu\text{Sv/h]}}

The net count rate is obtained by integrating the background-subtracted measured spectrum and dividing it by the measured live time. The gamma dose equivalent rate comes from the value obtained during measurement with the calibrated ionization chamber, again after the dose equivalent rate for background has been subtracted.

The flux sensitivity factor :math:`S_{\text{FLUX}}` fulfills the same role as the RASE sensitivity factor for measurements recorded in units of flux instead of dose. It is computed according to the following equation:

.. math::

   S_{\text{FLUX}} = \frac{\text{net count rate [cps]}}{\text{photopeak flux}[\gamma\text{/cm}^2\cdot s]}

The net count rate is obtained in the same manner as above. The photopeak flux is the net flux observed by the detector in a specific photopeak associated with the isotope.


IMPORTANT NOTES:

* The user can provide either an exposure rate, or a flux, or both. If neither is provided, the spectrum is assumed to be in dose and the rase_sensitivity factor is set to 1 while the flux_sensitivity factor is not defined.

* Background spectra are always given in units of dose.

* When creating base spectra for the background (from the measured background), use the raw spectra and the actual dose rates to calculate the RASE Sensitivity factor.

.. _base_spectra_naming_convention:

Base spectra naming convention
==============================

The file name for the base spectra follows the format ``Vvvvv_Mmmm_Source_Description.n42`` consists of four fields (vendor’s abbreviation, instrument model abbreviation, source name and scenario description) each separated by an underscore character:

* Vvvvv = a four-character manufacturer abbreviation
*	Mmmm = a three -character alphanumeric model number abbreviation
*	Source = a label describing the source
* Description = a label describing the shielding scenario or other relevant measurement conditions

The source description label shall follow a defined naming convention:

+-------------------------------------------+-----------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| **Nuclide or aggregate**                  | **Source label**            | **Comments**                                                                                                                                                                                                                                                        |
+===========================================+=============================+=====================================================================================================================================================================================================================================================================+
| 235U                                      | HEU                         | Highly enriched uranium with 235U/U above or equal to 20 %                                                                                                                                                                                                          |
+-------------------------------------------+-----------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 235U+238U                                 | LEU                         | Low enriched uranium with 235U/U between 0,7% and 20 %                                                                                                                                                                                                              |
+-------------------------------------------+-----------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 238U                                      | DU                          | Depleted uranium with 235U/U below 0,7 %                                                                                                                                                                                                                            |
+-------------------------------------------+-----------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 239Pu+240Pu+241Pu                         | WGPu                        | Weapons grade plutonium with 239Pu/Pu above or equal to 93 %                                                                                                                                                                                                        |
+-------------------------------------------+-----------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 239Pu+240Pu+241Pu                         | RGPu                        | Reactor grade plutonium with 239Pu/Pu below 93 %                                                                                                                                                                                                                    |
+-------------------------------------------+-----------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 40K                                       | Knorm                       | Potassium fertilizer or Potassium salt                                                                                                                                                                                                                              |
+-------------------------------------------+-----------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 238U decay chain                          | Unorm                       | Uranium decay chain in equilibrium with daughters (e.g. a base spectrum of phosphate fertilizer)                                                                                                                                                                    |
+-------------------------------------------+-----------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 232Th decay chain                         | Tnorm                       | Thorium decay chain in equilibrium with daughters (e.g. a base spectrum of welding rods, camera lenses or lantern mantles)                                                                                                                                          |
+-------------------------------------------+-----------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Natural radiation background              | Bgnd                        | Contribution from non-naturally occurring radioactive material into the spectrum shall be negligible                                                                                                                                                                |
+-------------------------------------------+-----------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| nnnMM                                     | MMnnn                       | All other nuclides, MM is a 2-alphabetic placeholder for the nuclide name according to *ISO 80000-9:2009, Quantities and units – Part 9: Physical chemistry and molecular physics* and nnn is an up to 3-digits placeholder for nuclide atomic number, e.g. Cf252   |
+-------------------------------------------+-----------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Other nuclides mixture                    | Name1+Name2                 | Separate each source name with a ‘+’ sign. Individual names are based on the rules above                                                                                                                                                                            |
+-------------------------------------------+-----------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

For example, the name ``Vabcd_M123_Am241.n42`` would represent the spectrum of a 241-Am source for instrument ‘123’ manufactured by ‘abcd’.  Similarly, ``Vabcd_M123_Cs137_12mmSteel.n42`` would represent the spectrum of a 137-Cs source shielded behind 12 mm of steel.

Format n42 base spectrum file
=============================

The format of the base spectra is based on the ANSI N42.42 format.

The ``<N42InstrumentData>`` element is the parent element for all data in the file. It must
contain one ``<Measurement>`` element, representing a measurement. The ``<Measurement>``
element contains various child elements that describe the instrument and the data collected.

Notes:

*	The element ``<RASE_Sensitivity>`` provides the gross sensitivity  in cps/(μSv/h) to the radionuclide whose abbreviation appears in the file name. Similarly, the element ``<FLUX_Sensitivity>`` provides the gross sensitivity  in :math:`\gamma/cm^2s` in the characteristic photopeak to the radionuclide whose abbreviation appears in the file name.
*	All base spectra for a given instrument including background must have the same <calibration> element, i.e. be defined in the same energy scale.
*	If required by the identification algorithm, a secondary spectrum (e.g. a background spectrum or the spectrum of the internal calibration source) can be provided after the measurement spectrum as an additional ``<spectrum></spectrum>`` element.
* For additional details, refer to IEC Standard, *Radiation instrumentation – semi-empirical method for performance evaluation of detection and radionuclide identification*, 2016




The following example of the XML data file is from a 2048-channel MCA. The indented formatting is purely for readability and is not required. Line breaks are not required, and there is no limit to line length. Spectrum compression according to the ANSI N42.42 is allowed.

.. code-block:: XML

  <?xml version="1.0" encoding="UTF-8"?>
  <N42InstrumentData>
  	<Measurement>
  		<Spectrum>
  			<StartTime>2007-05-22T15:05:00</StartTime>
  			<RealTime Unit="sec">PT110S</RealTime>
  			<LiveTime>PT110S</LiveTime>
  			<Calibration Type="Energy" EnergyUnits="keV">
  				<Equation Model="Polynomial">
  					<Coefficients>0.0 1.59 0.0</Coefficients>
  				</Equation>
  			</Calibration>
        <ChannelData> 8 14 17 18 36 38 41 50 76 97 102 105 142 150 167 192 163 203 194
        204 213 218 205 258 218 269 258 276 265 311 277 311 335 321 356 386 403 459 492
        524 567 575 591 656 677 694 797 816 898 958 919 1097 1026 1182 1169 1302 1374
        1465 1501 1686 1615 1645 1599 1597 1559 1605 1538 1584 1439 1453 1513 1456 1377
        1322 1261 1290 1340 1262 1383 1465 1471 1740 1985 2471 3223 4087 5105 6220 7288
        8093 8209 8085 7551 6536 5379 4119 3060 2260 1648 1230 875 671 541 406 316 247
        224 161 117 114 90 100 91 69 77 68 69 76 81 56 58 61 63 63 46 81 58 55 65 60 57
        62 63 75 52 57 49 43 64 41 63 42 49 45 52 42 44 43 44 49 53 47 49 31 57 40 48 34
        41 40 40 37 31 25 42 28 33 28 34 35 36 30 33 21 21 28 32 30 29 29 20 17 44 36 37
        30 22 29 20 22 26 25 19 25 24 14 23 18 23 21 18 24 21 22 14 19 14 21 16 28 20 24
        17 19 10 15 20 10 19 19 13 13 20 9 28 26 18 11 8 14 8 12 13 10 10 19 10 9 11 20
        10 14 12 15 10 12 13 13 11 13 9 16 10 9 10 14 11 17 8 12 6 10 10 9 10 8 16 10 11
        10 9 7 8 13 8 8 9 12 7 9 11 5 7 11 7 8 8 9 8 7 7 6 12 10 13 8 5 6 10 8 6 12 10 7
        8 7 9 3 11 5 5 10 5 9 16 5 5 8 13 9 4 4 9 8 6 7 3 4 4 7 7 4 9 8 7 4 3 9 7 8 7 3
        8 0 5 5 2 4 5 6 8 11 2 5 4 3 3 5 5 3 5 6 6 7 4 3 7 5 4 8 9 1 4 4 4 3 3 9 4 4 4 3
        4 11 5 4 5 8 5 5 4 3 4 3 4 4 4 4 5 6 2 6 3 1 4 3 9 3 1 6 8 6 5 2 5 3 5 7 3 3 2 6
        3 6 2 6 7 4 6 6 3 10 8 2 0 7 5 3 3 3 7 6 2 4 1 1 2 2 3 2 4 7 5 3 4 5 6 3 7 2 3 4
        5 1 5 8 1 2 2 0 4 2 1 0 2 7 2 5 3 0 2 1 3 4 2 4 4 6 7 4 4 3 4 2 4 5 0 2 4 2 2 3
        3 2 3 2 4 2 6 4 1 1 4 1 2 6 2 1 3 2 5 4 1 7 1 3 9 1 2 2 6 4 1 3 1 6 2 3 2 1 4 2
        2 4 3 1 3 4 0 2 3 1 3 1 2 3 6 2 1 1 2 2 2 5 1 2 3 2 3 2 5 3 1 3 3 0 3 0 4 2 3 2
        2 2 2 3 2 1 3 0 6 3 5 4 3 1 3 4 6 2 4 1 3 1 2 3 3 1 4 4 1 4 2 1 4 2 3 1 2 0 2 1
        1 3 2 2 2 2 3 3 2 3 1 0 1 2 1 3 5 0 1 1 3 4 4 3 0 1 2 2 2 2 3 1 2 3 3 1 0 0 1 3
        0 2 1 1 1 1 0 4 3 0 1 0 0 0 0 1 0 0 2 1 2 2 0 1 2 0 0 3 1 2 2 2 3 0 1 0 1 4 4 2
        1 5 1 2 0 4 0 0 3 7 1 4 2 0 2 1 4 2 3 0 4 3 2 2 1 3 5 2 0 1 3 2 0 1 2 0 6 1 1 4
        2 1 1 1 3 0 0 0 1 2 3 1 1 2 2 1 2 0 1 1 1 3 2 4 0 3 1 1 2 3 2 1 0 1 0 3 2 3 0 0
        1 1 1 2 2 0 2 2 2 0 2 1 0 3 0 2 1 0 2 2 2 0 0 0 0 3 1 2 1 0 2 0 2 1 1 1 1 1 2 3
        0 0 1 0 1 0 2 1 0 0 1 0 0 0 0 3 1 0 0 2 1 0 0 0 0 0 1 2 0 0 2 0 1 0 1 0 0 1 0 0
        2 0 0 1 1 1 1 2 0 2 3 0 2 1 3 2 2 1 1 2 0 2 2 3 1 1 2 2 2 0 2 1 5 1 5 3 5 3 1 3
        3 4 4 2 3 2 3 3 4 3 4 2 3 1 0 1 1 1 5 4 2 6 2 3 2 4 1 5 2 2 0 2 2 0 0 2 1 2 1 0
        0 1 1 1 0 1 0 1 2 1 0 0 0 1 1 3 0 1 1 1 0 0 0 1 0 0 0 0 0 0 0 1 0 0 0 0 0 0 0 1
        0 0 0 1 0 1 0 0 1 1 2 0 0 1 0 0 1 0 0 0 0 1 0 0 0 0 0 1 0 1 0 0 0 0 1 0 0 0 1 0
        2 1 0 0 1 0 0 0 2 0 0 0 0 0 1 0 0 0 0 0 0 1 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0
        0 0 0 1 0 0 0 0 1 0 1 0 0 0 0 1 0 0 0 0 0 1 1 0 0 0 0 0 0 0 1 1 0 0 1 0 0 0 0 0
        0 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 2 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0 1 0 0 0 0 0 0 0
        1 1 0 0 0 0 0 0 0 0 0 0 0 0 3 0 0 0 0 1 0 1 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
        0 1 0 0 0 0 0 0 0 1 0 0 0 1 0 0 1 0 0 1 0 0 2 0 0 0 0 1 0 1 0 0 0 0 1 0 0 1 0 0
        0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0 0 2 0 0 0 0 0 1 0 0 0 0 0 0 0 1 0 0 0 0
        0 0 0 0 0 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1
        0 0 0 0 1 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0 0 0 0 1 0 0 0 0 0 0 0 1 1
        0 0 1 0 0 1 0 0 0 1 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0
        1 0 0 0 1 0 0 0 0 0 0 0 0 0 1 0 0 0 0 0 0 1 0 0 1 0 0 1 0 0 0 1 0 0 0 1 0 0 0 0
        0 0 0 0 0 0 0 1 0 0 0 0 0 0 0 0 1 0 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
        0 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0 1 0 0 0 0 0 0 0 0 0
        0 0 1 0 0 0 0 0 0 0 0 0 0 0 1 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
        0 0 0 1 0 0 0 0 0 0 0 0 0 0 1 0 1 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0
        1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 2 0 0 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0
        0 0 0 0 0 0 0 1 0 1 0 0 0 0 0 1 0 1 1 0 0 0 0 0 0 0 1 0 0 0 0 0 0 0 1 0 0 0 0 1
        0 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
        0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0 0 0 0 0 0
        0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
        0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
        0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
        0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
        0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1
        0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
        0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
        0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 </ChannelData>
  			<RASE_Sensitivity>1234.5</RASE_Sensitivity>
  		</Spectrum>
  	</Measurement>
  </N42InstrumentData>
