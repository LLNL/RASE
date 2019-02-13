.. _influences:

***************************
Detector Influences in RASE
***************************

The influences functionality of the RASE code provides the user with a method for perturbing sampled spectra as a way to mimic energy
calibration distortions in response to the temperature, detector bias voltage, EMI interferences or other environmental effects.

The sampled spectra can be shifted along the energy axis using the following quadratic equation:

E' = C0 + C1 * E + C2 * E^2,

where

* E is the original energy bin value in the sampled spectrum (defined by the energy calibration of the base spectra), keV;
* E' is the resulting energy bin value after implementing the influence, keV;
* C0 is a constant offset value, keV;
* C1 is a linear offset coefficient (consistent with the gain change);
* C2 is a quadratic offset coefficient.

Please note that the three coefficients that define the influence do not substitute the original energy calibration coefficients
that are imported from the base spectra. Any influences are applied after the spectra are sampled, and the original energy calibration
coefficients are recorded in the resulting .n42 files as during the normal process.

To define an influence, navigate to the "Edit Detector" dialogue (for exampple, by double-clicking on one of an existing
instrument in the bottom table of the main window). Use the "Influences" table at the bottom of the "Edit Detector" dialogue to
specify the influence identification (name), and three coefficients: C0, C1, C2.

NOTE: All three coefficients must be defined for the influences to operate appropriately. Use a zero entry for the unused coefficient.

To implement an influence for an existing scenario, open the "Scenario Edit" dialogue (by double-clicking on a scenario
in the main window). Highlight the appropriate influences in the bottom-left field under "Influences". Repeat the procedure
for generating the sampled spectra for this scenario. "Switch off" the influences for the same scenario to generate unperturbed spectra.

NOTE: Several influences can be activated at the same time, they will be applied sequentially to the sampled spectra.

Example 1. A constant shift of sampled spectra by 100 kev can be defined using the following values for the three coefficients:
C0 = 100, C1 = 1, C2 = 0. Note the C1 = 1 is required in this case for the correct mathematical operation.

Example 2. To mimic a distortion that stretches the spectrum by 10% use the following values for the three coefficients:
C0 = 0, C1 = 1.1, C2 = 0.