.. _results_format:

*******************************************
Identification Results File Format for RASE
*******************************************

The following guidelines are provided to ensure that the identification result files produced by replay tools are natively compatible with RASE. Alternatively, they can be used to develop a translator tool to convert the native replay tool output to the RASE format.

The file name for output file containing identification results of the replay tool must be the same as an input sample spectrum with extension changed in :code:`.res`. For example, the file with the name ``Vabcd_M123_S80FBDC_04.res`` contains identification results of sample spectrum with the name ``Vabcd_M123_S80FBDC_04.n42``


The data in the identification results files must be ASCII characters. The data must be encapsulated using the extensible mark-up language (XML) that provides a mechanism for the data file to be self-describing as to content. The file must provide the list of isotopes identified and corresponding confidence index – a measure of how reliable the indication of the given isotope in the results of identification is, expressed as a number from 1 to 10 that indicates the degree of certainty to which result is correct.

An example of the identification result file is given below:

.. code-block:: XML

    <?xml version="1.0" encoding="UTF-8"?>
    <IdentificationResults>
         <Identification>
              <IDName>K-40</IDName>
              <IDConfidence>9</IDConfidence>
         </Identification>
         <Identification>
              <IDName>Ra-226</IDName>
              <IDConfidence>4</IDConfidence>
         </Identification>
         <Identification>
              <IDName>U-238</IDName>
              <IDConfidence>8</IDConfidence>
         </Identification>
    </IdentificationResults>

A legacy format is also acceptable where identification are provided as a newline-separated list of identification labels followed by a newline-separated list of confidence indices, as in the following example:

.. code-block:: XML

    <?xml version="1.0" encoding="UTF-8"?>
    <IdentificationResults>
         <Isotopes>
            K-40
            Ra-226
         </Isotopes>
         <ConfidenceIndex>
            4
            8
         </ConfidenceIndex>
    </IdentificationResults>