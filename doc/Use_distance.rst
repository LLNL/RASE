.. _Use_distance:

*******************************
Use Source-to-detector Distance
*******************************

It may be convenient at times to work in units of distance between the source and the detector rather than in units of source dose or flux. This becomes particularly useful when the user is comparing  RASE predictions against data collected with a source of a given intensity at certain distances.

The conversion of dose to distance can be achieved trivially by scaling for :math:`1/d^2` if the dose or flux are known at one distance value for the source of interest. To make things easier, RASE offers the ability to perform this :math:`1/d^2` scaling in the create scenario range dialog and when plotting results when selecting the `distance` label for an axis.

The required dose or flux values at a fixed distance can be obtained thru a direct measurement or from modeling. Among others, modeling tools like GADRAS and `InterSpec <https://sandialabs.github.io/InterSpec/>`_ offer this capability.
