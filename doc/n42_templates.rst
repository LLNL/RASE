.. _n42_templates:

********************************************
How to create n42 spectra templates for RASE
********************************************

The vast majority of replay tools ingest spectra formatted according to N42.42 ANSI standard. However, there is significant variability in the specific content of the n42 file used by each manufacturer and replay tools often expect that specific format and content. In order to accommodate a variety of .n42 formats, RASE uses a templating approach based on Python's Mako_ library. Simply put, RASE replaces certain blocks in the template file with the specific content created during the sample generation step.

The following table provides a list of the basic variables accessible for use within a template file:

+----------------------------------------------------------------+----------------------------------------------------------------------+
| Variable                                                       | Description                                                          |
+================================================================+======================================================================+
| scenario.acq_time                                              | Acquisition time in seconds for the scenario                         |
+----------------------------------------------------------------+----------------------------------------------------------------------+
| sample_counts                                                  | Generated sample spectrum as space separated counts for each channel |
+----------------------------------------------------------------+----------------------------------------------------------------------+
| compressed_sample_counts                                       | Same as above but in N42.42 zero compressed format                   |
+----------------------------------------------------------------+----------------------------------------------------------------------+
| secondary_spectrum.realtime                                    | Realtime of the secondary spectrum, if present                       |
+----------------------------------------------------------------+----------------------------------------------------------------------+
| secondary_spectrum.livetim                                     | Livetime of the secondary spectrum, if present                       |
+----------------------------------------------------------------+----------------------------------------------------------------------+
| secondary_spectrum.get_counts_as_str()                         | Secondary spectrum as space separated counts for each channel        |
+----------------------------------------------------------------+----------------------------------------------------------------------+
| secondary_spectrum.get_compressed_counts_as_str()              | Same as above but in N42.42 zero compressed format                   |
+----------------------------------------------------------------+----------------------------------------------------------------------+
| detector.ecal0, detector.ecal1, detector.ecal2, detector.ecal3 | Energy calibration coefficients                                      |
+----------------------------------------------------------------+----------------------------------------------------------------------+


Examples of .n42 templates are distributed with RASE.



.. _Mako: http://www.makotemplates.org/
