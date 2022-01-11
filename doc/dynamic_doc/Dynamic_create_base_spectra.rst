.. _dynamic_create_base_spectra:

****************************
Base spectra in Dynamic RASE
****************************

To simulate the detector response to a source in Dynamic RASE, a detector response map must be built for that source. This map is built using measured spectra, or "base spectra", recorded in multiple locations. These base spectra encode various pieces of information necessary for simulation, such as a gamma spectrum, calibration coefficients, measurement real and live time, source location in relation to the center of the detector face, and "quantity" of the source.

To create base spectra for Dynamic RASE, the following must be done:

#. Acquire a set of source and background measurements at multiple locations
#. Process the measured spectra to separate the source from the background
#. Produce a properly formatted n42 file for ingestion into RASE

Dynamic RASE is released alongside several sets of example dynamic base spectra. These spectra were simulated using GADRAS for an non-specific instrument. They can be found in the `dynamicBaseSpectra` directory.

For additional details about base spectra, refer to [RASE_standard]_


General considerations for spectra acquisition
==============================================

Each source to be simulated in a dynamic scenario must have a detector response map associated with it. This map is built over all space by interpolating and extrapolating from spectra recorded at many locations. The more spectra that are acquired, and the more widely distributed those measurements are across the space of interest, the more true to reality the response map will be over that space. Because the map takes counting uncertainty into consideration when creating a universal fit, the higher the total number of counts in each spectrum, the more precise the detector response map will be.

With these in mind, there are three ways that a user might acquire base spectra to generate a good detector response map:

#. Acquire high statistics static spectra in various locations. This involves setting the detector/source in a fixed geometry, measuring for a significant amount of time, recording the spectrum, and then repeating this procedure in many locations. This approach is recommended for high precision, particularly if the points are well-suited for the paths that will be simulated (e.g.: measuring points at and around the standoff where the user expects to simulate source pass-bys)
#. Acquire short dwell static spectra in a large number of locations. This approach is recommended for large detector response maps, where it may not be feasible to take enough long-dwell static measurements to fully characterize the detector response over a large space.
#. Conduct a dynamic measurement, where the source and detector are in constant relative motion, and from that measurement create many integrated, short spectra. Each integrated short spectrum would be assigned a location along the path. This approach is ideal for users who have a programmable track available, such that the detector can be set to measure the source moving slowly past it over a long period of time. This minimizes the demands on the experimentalist, while still acquiring a potentially large number of spectra.

This procedure should be completed for each source of interest. If the user is planning on using proxy sources (see :ref:`mechanics_proxy_sources` for details on proxy source simulations), it may only be necessary to repeat the procedure above for a small number of sources. In the proxy source case, the detector response maps created for those other sources can be applied as a scaling map to a single anchor point spectrum with high counting statistics from a different source. For example, if the user created a full detector response map for Cs137, it may be sufficient to record one spectrum of WGPu at a known location and use the detector response map relationships determined for Cs137 a to scale the WGPu spectrum over space. If possible, the detector response map being used as a proxy should be taken for a source that has photopeaks close in energy to the photopeaks of the source of interest.

Note that there are no strict requirements established in the Dynamic RASE code in terms of number of spectra or spectrum quality expectations; Dynamic RASE will not scold the user for providing a small number of spectra with poor counting statistics, nor will it raise a fuss if the user provides a huge number of high statistics spectra. As such, options 1 and 2 above are effectively the same procedure, differing only in number of spectra and the acquisition time of each spectrum. Base spectra do not necessarily need to be acquired at the same locations for each source: the detector response map for each source is uniquely built, and each is defined over all space. The base spectra used to define the map for a source also do not need to be recorded with the same live time, or even the same source intensity: the live time and the "quantity" of the source is uniquely associated with each base spectra. This makes it possible for the user to build a detector response map for a single isotope using multiple sources. For instance, to build a Cs137 response map the user could use a low activity source when measuring up close (to avoid pileup effects) and switch to a high activity source when measuring far away (to reduce the necessary measuring time to achieve high counting statistics).

It is assumed that the background spectra provided by the user are spatially uniform. There is no map that is generated, and there is only one single background measurement that needs to be taken for a given detector.

Each base spectrum file should note the calibration coefficients of the detector when the measurement was recorded. The calibration coefficients for all base spectra associated with a certain detector, regardless of source, must be the same. Each file should also note the real and live time of the measurement and the location of the source in relation to center of the detector face in (x, y, z). For Dynamic RASE, x is associated with horizontal offset from the center of the detector face, y is associated with standoff, and z is associated with vertical offset. Finally, each file should note the "quantity" of the source and the units of that quantity. Currently, Dynamic RASE only supports sources described in units that are fixed regardless of relative source-detector position, such as activity (in terms of "uCi") or mass (in terms of "kg"). The only exception to this is background: the quantity of background is expressed in terms of dose, in units of "uSv_h". The units of the base spectra must be consistent for a given detector response map, but different sources can use different units (this holds true for proxy sources as well, as the relationships between the spectra are still the same regardless of units). As an example: the user could make a detector response map for Cs137 with units of "uCi", and a response map for WGPu in terms of "kg". In the case of Cs137, each base spectrum would note the activity of the source used to make the measurement (if all measurements used the same source, then all base spectra would have the same quantity term). Likewise, for WGPu, each base spectrum would note the mass of the WGPu sample measured. When defining a scenario using Cs137 and WGPu, the quantity of Cs137 will be expressed in units of "uCi" and the quantity of WGPu in units of "kg". It should be noted that Dynamic RASE does not account for self-shielding effects that might occur when increasing the mass of SNM, and as such some caution may be prudent when interpreting results in cases where the masses of SNM are large and the difference between base spectrum mass and scenario definition mass is significant.


Specific guidance for spectra acquisition
=========================================

A measurement should be performed usually in well-controlled laboratory conditions with one or more radioactive sources. Adherence to the following recommendations will result in high-quality base spectra:

- The measurement scenario (source strength, shielding) should be chosen such as to ensure that a significant fraction of the count rate in the instrument arises from the source term alone. If noting the dose rate, the dose rate from the source should be at least 5 times above background. If measuring the source in units of flux, the net counts in the photopeak of interest should be at least 350-550. Note that this may not be possible for measurements where the source is far from the detector.
- If acquiring long dwell spectra with high statistics, the measurement time should be long enough such that the photopeaks of interest have at least 10,000 counts each. Adherence to this guidance becomes less critical as the number of measured base spectra, as well as the proximity of base spectra to each other, increases.
- Verify that no significant pile-up or dead time is present in the instrument. Ideally dead time should be limited to no more than 2%.
- Measurements should, if possible, be taken with the detector as fixed, while the source is moved as necessary. The detector should not be rotated either during or between measurements (in order to properly capture angular effects).
- The instrument’s orientation with respect to the source shall reflect how the instrument is intended to be used in the field.
- Acquisition times for the raw spectra should be adjusted such that the total counts in any base spectrum is at least ten times greater than the total counts observed during a scenario along the part of the source path nearer to that base spectrum than any other. This can be calculated according to the formula: :math:`Q_0 \cdot T_0 > 10 \cdot Q_s \cdot {T_{sseg}}`, where :math:`Q_0` is the quantity of the source material noted in the base spectrum, :math:`T_0` is the measurement live time of the base spectrum, :math:`Q_s` is the quantity of that source specified in the scenario definition, and :math:`{T_{sseg}}` is the total time that the scenario path is closer to that base spectrum than any other (i.e.: the time spent on that segment of the path). In the case of proxy sources, this same approach should be used but modified by replacing each point used to make the surrogate detector map with an appropriately scaled version of the anchor point.
- If creating base spectra using a continuously moving track, the velocity of track times the activity of the source should be at least 10 times that of a the scenario being simulated along the same track. This can be calculated using the following formula: :math:`Q_0 \cdot V_0 > 10 \cdot Q_s \cdot V_s`, where :math:`Q_0` is the quantity of the source material noted in the base spectrum, :math:`V_0` is the velocity of the track, :math:`Q_s` is the quantity of that source specified in the scenario definition, and :math:`V_s` is the velocity described in the scenario.

A high-statistics long-dwell (at least 1 hour) background spectrum should also be acquired in the same experimental conditions as for the source measurements.

Record the activity or mass of the source used to create each base spectrum.

If measured spectra cannot be obtained, simulated spectra can also be used with RASE.


Recommended spatial distribution of base spectra
================================================

The detector response map for any source will better represent reality at points near base spectra and will be a more thorough model of spatial trends as more data is provided. As such, it is a benefit to the user to have as many base spectra as possible in a simulation. However, in limited data collection situations, certain recommendations should be adhered to in order to create smooth and accurate detector response maps. Note that Dynamic RASE is capable of establishing symmetry. If the user is attempting to simulate a symmetric space, it is not necessary to take points on both sides of the centerline of the detector. The following recommendations, unless otherwise noted, assume that the user will be taking spectra with high counting statistics, enforcing symmetry conditions, and simulating several different kinds of paths: passby at a fixed standoff, approaching/passing by diagonally, approaching straight on/backing directly away from the source, etc. It is also assumed that the user is both taking base spectra and simulating paths in a plane at the same height of the detector (i.e.: the vertical standoff is zero).

- In unshielded, symmetric, conditions, simulations using GADRAS-based spectra have indicated that a smooth map can be generated by as few as four points. However, the user is strongly encouraged to acquire more to avoid potential degeneracies, particularly in energy bins with low counting statistics. It has been found that seven well-distributed points is sufficient to consistently create smooth maps.
- At least two, and preferably three, measurements should be taken directly in front of the detector at various distances to well-capture standoff dependency.
- Aside from the head-on acquisitions, the user should avoid taking more than two measurements at any fixed radius or angle, as this can result in degeneracies and response map artifacts.
- Measurements should exist beyond the extremes of any simulated path in all directions.


Beyond these general recommendations, an additional set of recommendations exist for more specific cases:

- If attempting to simulate a specific path only (e.g.: a passby from :math:`x_1` to :math:`x_2` at a particular standoff), the user will have the most accurate results by focusing efforts on creating base spectra specifically along the path (instead of widely distributed throughout space).
- If instead of using high-statistics measurements the user chooses to supply Dynamic RASE with many low statistics measurements, efforts should be taken such that the counts of those spectra sum to agree with the acquisition recommendations from this and above sections. In other words, the user would want to take something on the order of 14 measurements with 5,000 counts in each photopeak to replace 7 measurements with 10,000 counts in each photopeak.
- If simulating instances with sharp changes, a denser set of measurements around the transition space is necessary. For example, if attempting to simulate the edge of a shield, the user should take at least one measurement at either side of the shield at multiple distances.


Process measured spectra
========================

In order to allow for generation of varying scenarios with different sources and dose rates, RASE needs spectra that reproduce the instrument response to the radiation arising from the source term alone. For this reason, the background and any spurious component (e.g. intrinsic calibration source) must be removed from the collected base spectra.

The resulting background-subtracted spectrum can be obtained through channel-by-channel subtraction of measured source and background spectra after normalizing both spectra by live time. Re-binning should be performed if needed to account for any gain shift between source and background spectra. If an intrinsic calibration source is visible in the measured source spectrum, it should be also subtracted. When generating base spectra of natural radiation background, background subtraction should not be performed.


.. _base_spectra_naming_convention:

Base spectra naming convention
==============================

The file name for the base spectra follows the format ``Vvvvv_Mmmm_Source_Description.n42`` consists of four fields (vendor’s abbreviation, instrument model abbreviation, source name and scenario description) each separated by an underscore character:

* Vvvvv = a four-character manufacturer abbreviation
* Mmmm = a three -character alphanumeric model number abbreviation
* Source = a label describing the source
* Description = a label describing the shielding scenario or other relevant measurement conditions, such as position and quantity
* Other = a label that distinguishes between files based on source strength, location, etc.

The source description label shall follow a defined naming convention:

+-------------------------------------------+-----------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| **Nuclide or aggregate**                  | **Source label**            | **Comments**                                                                                                                                                                                                                                                        |
+===========================================+=============================+=====================================================================================================================================================================================================================================================================+
| 235U                                      | HEU                         | Highly enriched uranium with 235U/U above or equal to 20%                                                                                                                                                                                                           |
+-------------------------------------------+-----------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 235U+238U                                 | LEU                         | Low enriched uranium with 235U/U between 0.7% and 20%                                                                                                                                                                                                               |
+-------------------------------------------+-----------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 238U                                      | DU                          | Depleted uranium with 235U/U below 0.7%                                                                                                                                                                                                                             |
+-------------------------------------------+-----------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 239Pu+240Pu+241Pu                         | WGPu                        | Weapons grade plutonium with 239Pu/Pu above or equal to 93%                                                                                                                                                                                                         |
+-------------------------------------------+-----------------------------+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| 239Pu+240Pu+241Pu                         | RGPu                        | Reactor grade plutonium with 239Pu/Pu below 93%                                                                                                                                                                                                                     |
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

For example, the name ``Vabcd_M123_Am241.n42`` would represent the spectrum of a Am241 source for instrument ‘123’ manufactured by ‘abcd’.  Similarly, ``Vabcd_M123_Cs137_12mmSteel.n42`` would represent the spectrum of a Cs137 source shielded behind 12 mm of steel. ``Vabcd_M123_Ba133_{100uCi}{dx=-250}{dy=150}{dz=0}`` would represent a Ba133 source at 100 uCi located at position x = -250, y = 150, and z = 0.

Format n42 base spectrum file
=============================

The format of the base spectra is based on the ANSI N42.42 format.

The ``<N42InstrumentData>`` element is the parent element for all data in the file. It must contain one ``<Measurement>`` element, representing a measurement. The ``<Measurement>`` element contains various child elements that describe the instrument and the data collected.

Notes:

*	The element ``<Position Units="___">`` describes the location of the source in relation to the center of the detector face. The user may define arbitrary units for the position. The <x>, <y>, and <z> subelements are all in the same units as specified by the user in the position tag.
*   The element ``<Quantity Units="___">`` describes the intensity or amount of the source, depending on the units specified by the user. Background units should be specified in dose, with Units="uSv_h". Sources should be specified with values that do not change based on position, such as activity ("uCi") or mass ("kg"). All base spectra used to build a single detector response map for a source must have the same units, but each spectrum can have different quantities.
*	All base spectra for a given instrument including background must have the same <calibration> element, i.e. be defined in the same energy scale.
*	If required by the identification algorithm, a secondary spectrum (e.g. a background spectrum or the spectrum of the internal calibration source) can be provided after the measurement spectrum as an additional ``<spectrum></spectrum>`` element.
* For additional details, refer to IEC Standard, *Radiation instrumentation – semi-empirical method for performance evaluation of detection and radionuclide identification*, 2016

The following example of the XML data file is from a 1024-channel MCA. The indented formatting is purely for readability and is not required. Line breaks are not required, and there is no limit to line length. Spectrum compression according to the ANSI N42.42 is allowed.

.. code-block:: XML

    <?xml version="1.0" ?>
    <N42InstrumentData>
      <Measurement>
        <Spectrum>
          <RealTime Unit="sec">PT1800.0S</RealTime>
          <LiveTime Unit="sec">PT1797.3070068359375S</LiveTime>
          <Calibration Type="energy" EnergyUnits="keV">
            <Equation Model="Polynomial">
              <Coefficients>0  2.83783197265625  0.0</Coefficients>
            </Equation>
          </Calibration>
          <ChannelData>0 0 1560 5141 5228 5096 5412 5694 6685 11419 45485 110351
          97985 47801 22268 8826 6145 7343 10605 14652 16109 12933 10873 13076
          17162 20769 23530 29227 46107 73393 93887 89434 59289 28738 11569 5858
          4486 4369 4479 4534 4619 4690 4830 4694 4766 4691 4862 4888 5284 5102
          5482 5646 5963 6480 6989 7469 8151 8916 9826 10011 10477 10398 10440
          10170 9954 9653 9526 9212 8994 8675 8078 7712 7548 6895 6467 6120 6078
          6117 5862 5955 5580 5682 5686 5414 5192 4851 4790 4615 4659 4708 4581
          4857 5023 5300 6225 7177 8216 9755 10896 11776 12579 13142 13525 13928
          14760 16180 17801 19036 20401 20702 20675 18828 16807 14324 11730 9431
          8189 7360 8030 9806 12809 16990 22334 28555 35163 41337 46127 49192
          49921 48783 45073 39966 34241 28240 23061 18318 14706 11792 9620 7959
          6297 5366 4199 3429 2421 1794 1201 870 485 270 187 140 22 99 63 49 61
          0 24 7 0 11 35 30 0 29 22 39 62 7 23 46 0 0 0 0 0 0 0 122 16 0 0 0 0 0
          154 0 0 0 0 65 0 4 22 32 31 0 13 10 0 37 0 25 39 0 43 9 25 3 20 24 0 19
          28 19 2 25 0 24 0 38 39 0 30 26 18 3 8 28 0 8 1 15 0 13 38 14 0 0 108
          47 31 28 40 0 15 53 10 4 2 0 44 3 34 47 11 13 7 0 24 34 29 10 7 0 7 0
          41 21 19 17 0 0 2 0 0 0 0 6 0 0 0 0 22 0 0 0 0 8 17 0 34 0 11 8 0 5 31
          0 0 4 30 18 1 0 35 21 8 0 17 8 51 0 0 0 26 19 7 15 44 0 0 6 0 11 0 0 9
          14 0 24 0 7 0 0 31 0 7 33 7 14 0 0 0 11 0 1 27 0 0 0 0 0 0 9 0 2 0 0 33
          0 0 0 13 5 0 4 8 0 6 14 0 0 0 0 19 0 0 28 2 0 0 0 17 0 10 26 0 0 0 18 0
          10 2 6 0 0 0 0 0 0 0 21 0 0 0 1 13 12 0 0 0 5 11 0 0 0 11 0 4 37 40 0 0
          0 34 20 0 33 0 0 0 0 0 0 0 20 0 7 0 0 0 0 19 33 0 0 0 16 31 0 31 21 10
          0 27 0 0 26 0 14 0 0 0 26 26 15 0 0 21 0 4 0 0 0 0 0 0 19 0 0 0 28 1 3
          0 2 13 0 3 0 0 14 0 2 3 0 6 0 0 0 15 0 21 0 0 0 0 9 0 27 32 0 0 5 11 0
          0 0 35 28 0 6 11 2 0 4 0 0 0 0 45 0 0 7 13 13 0 0 0 16 21 0 32 0 15 25
          6 10 11 0 1 6 1 0 11 3 0 0 4 0 2 22 0 0 8 0 8 0 8 0 0 0 0 6 1 0 0 0 4
          0 0 13 2 0 8 12 0 0 8 0 3 0 0 0 0 1 0 5 0 0 0 0 0 0 0 13 0 0 0 0 0 9 0
          0 0 0 13 12 0 64 0 18 0 0 6 11 14 5 0 7 16 0 5 2 0 14 18 0 3 2 11 0 0
          0 7 0 0 4 1 0 12 4 0 8 0 1 3 5 0 0 0 0 0 0 3 5 0 0 0 7 0 0 0 1 3 3 4 1
          9 1 0 4 0 0 0 0 0 0 1 4 0 0 0 0 6 0 0 0 1 4 0 0 0 2 4 0 5 0 1 0 0 4 3 0
          2 3 0 2 1 0 0 3 0 0 7 0 5 0 0 5 5 0 0 0 5 0 0 1 0 1 0 2 0 1 0 0 3 0 0 0
          4 0 0 5 6 0 1 6 2 5 0 0 4 1 0 2 2 4 0 2 0 0 3 6 0 0 7 2 0 0 0 1 0 0 1 0
          0 0 0 0 3 3 0 2 0 5 0 0 0 0 1 1 2 0 0 6 4 0 2 0 0 0 0 0 0 2 0 0 2 0 1 0
          1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 2 0 4 0 0 0 2 0 2 1 0 0 0 0 0 0 0 0
          0 2 0 2 0 3 0 2 3 0 0 0 0 0 0 0 0 0 0 2 0 8 8 3 0 0 0 8 5 0 6 0 0 0 0 0
          3 4 0 0 0 0 8 0 2 4 0 6 0 5 2 2 4 8 0 4 0 0 1 4 5 0 0 0 0 3 1 0 0 0 0 1
          0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0
          0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 
          0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 </ChannelData>
          <Position Units="cm">
            <x>-50</x>
            <y>100</y>
            <z>0</z>
          </Position>
          <Quantity Units="uCi">100</Quantity>
        </Spectrum>
      </Measurement>
    </N42InstrumentData>

.. _dynamic-create_base_spectra:
