.. _dynamic_n42_templates:

********************************************
How to create n42 spectra templates for RASE
********************************************

The vast majority of replay tools ingest spectra formatted according to n42.42 ANSI standard. However, there is significant variability in the specific content of the n42 file used by each manufacturer and replay tools often expect that specific format and content. In order to accommodate a variety of .n42 formats, RASE uses a templating approach based on Python's Mako_ library. Simply put, RASE replaces certain blocks in the template file with the specific content created during the sample generation step. Each piece of content to be replaced by a variable from the python code is marked in the template using the format (without angle brackets): ${<variable>}.

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
| secondary_spectrum.livetime                                    | Livetime of the secondary spectrum, if present                       |
+----------------------------------------------------------------+----------------------------------------------------------------------+
| secondary_spectrum.get_counts_as_str()                         | Secondary spectrum as space separated counts for each channel        |
+----------------------------------------------------------------+----------------------------------------------------------------------+
| secondary_spectrum.get_compressed_counts_as_str()              | Same as above but in N42.42 zero compressed format                   |
+----------------------------------------------------------------+----------------------------------------------------------------------+
| detector.ecal0, detector.ecal1, detector.ecal2, detector.ecal3 | Energy calibration coefficients                                      |
+----------------------------------------------------------------+----------------------------------------------------------------------+

Examples of .n42 templates are distributed with RASE.


Formatting templates specifically for dynamic data
==================================================

Dynamic RASE can make use of any static templates by integrating all counts on the path and passing that single integrated measurement to the template. However, many replay tools that might be used with Dynamic RASE require that data is formatted in a dynamic manner. In these file formats, many spectral data blocks taken in small time increments are placed one after the other throughout the bulk of the file. Designing these templates require the user to employ extended Mako functionality: namely, importing python libraries and defining loops and repeatable blocks of code in a form similar to functions. Note that each dynamic replay tool will require uniquely formatted input data, and as such the templates will all be designed differently. It is up to the user to examine experimental dynamic input files, identify repeated blocks, and design the template by maintaining essential .n42 structures while defining and repeating measurement blocks accordingly.

In the dynamic template shipped with Dynamic RASE, "Dynamic_template.n42" exemplifies these qualities. At the top of the file, there is a block for import statements:

.. code-block:: XML

    <%!
    import datetime
    from src import utils
    now = datetime.datetime.now()
    %>

This is followed by two definitions for repeated blocks. This example template works with a replay tool that expects to see a "sync" block followed by a "measurement" block for every short dynamically acquired spectrum. These blocks are designed like functions, and can take in arguments such as iteration index and a datetime. The two blocks are defined as follows:

.. code-block:: XML

    <%def name="sync(syncindex,datetime_obj)">
        <RadMeasurement id="SyncMeasure${f'{syncindex:06x}'}">
            <MeasurementClassCode>NotSpecified</MeasurementClassCode>
            <StartDateTime>${'{}-{}-{}T{}:{}:{}.{}-00:00'.format(datetime_obj.year,
                                                                 datetime_obj.month,
                                                                 datetime_obj.day,
                                                                 datetime_obj.hour,
                                                                 datetime_obj.minute,
                                                                 datetime_obj.second,
                                                                 int(datetime_obj.microsecond/1000))
                                                                 }</StartDateTime>
            <RealTimeDuration>PT${(datetime_obj-now).total_seconds()}S</RealTimeDuration>
            <sym:MessageID>${int(str(int((syncindex ) * 1E6)), 16)}</sym:MessageID>
        </RadMeasurement>
    </%def>

.. code-block:: XML

    <%def name="measurement(syncindex,measindex,datetime_obj,bins,duration)">
        <RadMeasurement id="ForegroundMeasure${int((syncindex + 111111) * 1E6 + measindex)}">
    		<MeasurementClassCode>Foreground</MeasurementClassCode>
    		<StartDateTime>${'{}-{}-{}T{}:{}:{}.{}-00:00'.format(datetime_obj.year,
                                                                 datetime_obj.month,
                                                                 datetime_obj.day,
                                                                 datetime_obj.hour,
                                                                 datetime_obj.minute,
                                                                 datetime_obj.second,
                                                                 int(datetime_obj.microsecond/1000))
                                                                 }</StartDateTime>
    		<RealTimeDuration>PT${duration}S</RealTimeDuration>
    		<Spectrum id="ForegroundMeasure${int((syncindex + 111111) * 1E6 + measindex)}Gamma"
                      radDetectorInformationReference="DetectorInfoGamma"
                      energyCalibrationReference="ECalGamma-190004"
                      FWHMCalibrationReference="RCalGamma-190004">
    			<LiveTimeDuration>PT${duration}S</LiveTimeDuration>
    			<ChannelData compressionCode="None">
                    ${' '.join([str(int(bin)) for bin in bins])}
                </ChannelData>
    			<sym:RealTimeDuration>${duration}</sym:RealTimeDuration>
    		</Spectrum>
    		<OccupancyIndicator>false</OccupancyIndicator>
    	</RadMeasurement>
    </%def>

Following these definitions, the template takes on a structure similar to templates used with Static RASE: the overarching "RadInstrumentData" element is in place, and various sub-elements such as "EnergyCalibration" and the "RadMeasurement" for the onboard background measurement are populated using the python tags noted in the table above.

This template specifically requires a single "sync" block before the dynamic data begins. This is noted by:

.. code-block:: XML

    ${sync(1,now - datetime.timedelta(seconds=1))}

After this first "sync" block, there is a block of code that marks the start of the dynamic measurement section. Following this there is a loop defined using Mako's syntax that populates the template with repeated "sync" and "measurement" blocks:

.. code-block:: XML

    % for i,period in enumerate(sample_periods):
        <%
        time = scenario.sampletimes[i]
        duration = scenario.sampletimes[i+1]-time
        %>
        ${sync(1+i,now+datetime.timedelta(seconds=time))}
        ${measurement(1+i,i,now+datetime.timedelta(seconds=time),period,duration)}
    % endfor

This block is populated with the "sync" and "measurement" blocks defined towards the top of the file, which are themselves populated from data generated in the Dynamic RASE simulation. The template finishes by a final "sync" block and a block that marks the end of the dynamic data.

.. _Mako: http://www.makotemplates.org/
