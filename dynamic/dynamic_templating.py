###############################################################################
# Copyright (c) 2018-2022 Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory
#
# Written by J. Brodsky, S. Czyz
# RASE-support@llnl.gov.
#
# LLNL-CODE-829509
#
# All rights reserved.
#
# This file is part of RASE.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED,INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
###############################################################################

from mako.template import Template
from mako import exceptions
import datetime
import declxml as xml
import numpy as np
from src.rase_functions import create_n42_file_from_template, secondary_type
from dynamic import dynamic_scenarios
import copy
from pathlib import Path
from src.table_def import BackgroundSpectrum

def add_sync_template(spec_index=0, datetime_obj=datetime.datetime.now(), runtime=1, append_str=''):

    sync_processor = xml.dictionary('RadMeasurement', [
                       xml.string('.', attribute='id'),
                       xml.string('MeasurementClassCode'),
                       xml.string('StartDateTime'),
                       xml.string('RealTimeDuration'),
                       xml.integer('sym_namespace_MessageID')
                    ])

    sync_measure = {
        'id': 'SyncMeasure{}'.format(spec_index + 111111),
        'MeasurementClassCode': 'NotSpecified',
        'StartDateTime': '{}-{}-{}T{}:{}:{}.{}-00:00'.format(datetime_obj.year, datetime_obj.month, datetime_obj.day,
                                                             datetime_obj.hour, datetime_obj.minute,
                                                             datetime_obj.second, int(datetime_obj.microsecond/1000)),
        'RealTimeDuration': 'PT{}S'.format(runtime),
        'sym_namespace_MessageID': int(str(int((spec_index + 111111) * 1E6)), 16)
    }

    if append_str:
        # combine with previous and remove the <?xml version="1.0" encoding="utf-8"?> line from the serialization
        return append_str + xml.serialize_to_string(sync_processor, sync_measure, indent='   ').replace(
            '_namespace_', ':').split('\n', 1)[1]
    return xml.serialize_to_string(sync_processor, sync_measure, indent='   ').replace('_namespace_',':').split('\n', 1)[1]

def add_measurement_template(spec_index=0, meas_it=1, datetime_obj=datetime.datetime.now(), runtime=1, livetime=1,
                             ch_data='1 0 1023', realtime=1, append_str=''):

    rad_processor = xml.dictionary('RadMeasurement', [
                       xml.string('.', attribute='id'),
                       xml.string('MeasurementClassCode'),
                       xml.string('StartDateTime'),
                       xml.string('RealTimeDuration'),
                       xml.dictionary('Spectrum', [
                           xml.string('.', attribute='id'),
                           xml.string('.', attribute='radDetectorInformationReference'),
                           xml.string('.', attribute='energyCalibrationReference'),
                           xml.string('.', attribute='FWHMCalibrationReference'),
                           xml.string('LiveTimeDuration'),
                           xml.string('ChannelData'),
                           xml.string('ChannelData', attribute='compressionCode'),
                           xml.floating_point('sym_namespace_RealTimeDuration')]),
                       xml.string('OccupancyIndicator')
                    ])

    rad_measure = {
        'id': 'ForegroundMeasure{}'.format(int((spec_index + 111111) * 1E6 + meas_it)),
        'MeasurementClassCode': 'Foreground',
        'StartDateTime': '{}-{}-{}T{}:{}:{}.{}-00:00'.format(datetime_obj.year, datetime_obj.month, datetime_obj.day,
                                                             datetime_obj.hour, datetime_obj.minute,
                                                             datetime_obj.second, int(datetime_obj.microsecond/1000)),
        'RealTimeDuration': 'PT{}S'.format(runtime),
        'Spectrum':
            {'id': 'ForegroundMeasure{}Gamma'.format(int((spec_index + 111111) * 1E6 + meas_it)),
            'radDetectorInformationReference': 'DetectorInfoGamma',
            'energyCalibrationReference': 'ECalGamma-190004',
            'FWHMCalibrationReference': 'RCalGamma-190004',
            'LiveTimeDuration': 'PT{}S'.format(livetime),
            'ChannelData': ch_data,
            'compressionCode': 'None',
            'sym_namespace_RealTimeDuration': realtime},
        'OccupancyIndicator': 'false'
    }

    if append_str:
        # combine with previous and remove the <?xml version="1.0" encoding="utf-8"?> line from the serialization
        return append_str + xml.serialize_to_string(rad_processor, rad_measure, indent='   ').replace(
            '_namespace_', ':').split('\n', 1)[1]
    return xml.serialize_to_string(rad_processor, rad_measure, indent='   ').replace('_namespace_',':').split('\n', 1)[1]




def to_file(filename, transient_string):

    with open(filename, 'w') as out_file:
        out_file.write(transient_string)

import os
def write_files(config:dict,name, times, spectra_reps, bg):
    for i in range(spectra_reps.shape[0]):
        outfilename = "{dir}/SampleSpectra/{name}/{name}_{rep:08d}.n42".format(dir=config['output_folder'],rep=i,name=name)
        os.makedirs(os.path.dirname(outfilename),exist_ok=True)
        scen_name = config['tests'][name]['scenario']
        write_file(config,times, spectra_reps[i,:,:],bg,scen_name,outfilename)

import scipy.interpolate
def integral_rebin(a, newbins, axis=2): #axis=2 is good for (reps, times, energies), but choose as reasonable
    pad = np.zeros((len(a.shape),2),dtype=int)
    pad[axis,0]=1
    a_padded = np.pad(a,pad)
    a_integral = np.cumsum(a_padded,axis=axis)
    a_points = np.arange(start=0, stop=a.shape[axis]+1)
    out_points = np.linspace(start=0, stop=a_points[-1], num= newbins+ 1, endpoint=True)
    interp = scipy.interpolate.interp1d(x=a_points,y=a_integral,axis=axis)
    return np.rint(np.diff(interp(out_points))).astype(int)



def write_file(config:dict, times, spectra, bg, scen_name=None, outfilename = None):
    template_path = config['template_path']
    if not outfilename:
        outfilename = config['output_path']

    n42_template = Template(filename=template_path, input_encoding='utf-8')

    now = datetime.datetime.now()
    transient_string = ''
    sync_period = 1 #second
    n_syncs = 0
    last_sync = -9999
    assert (times[0]>last_sync), "First time in scenario should be 0, not negative."
    assert (times[0] < sync_period), "First time in scenario should be 0, not >1"
    if len(times)>1: measurement_period = times[1]-times[0]
    else: measurement_period = config['scenarios'][scen_name]['acquisition_time']

    bg_data_string = ' '.join('{:d}'.format(int(x)) for x in (bg))  # TODO: Might cause rounding errors
    for i_time, time in enumerate(times):
        if time >= last_sync+sync_period: #need a new sync measurement
            last_sync+=sync_period
            transient_string = add_sync_template(spec_index=n_syncs, datetime_obj=now + datetime.timedelta(seconds=last_sync),
                                                 runtime=last_sync, append_str=transient_string)
            n_syncs+=1
        ch_data_string = ' '.join('{:d}'.format(x) for x in (spectra[i_time, :]))

        transient_string = add_measurement_template(spec_index=n_syncs-1, meas_it=i_time,
                                                        datetime_obj=now + datetime.timedelta(seconds=float(time)),
                                                        runtime=time, livetime=measurement_period, ch_data=ch_data_string,
                                                        realtime=measurement_period, append_str=transient_string)

    try:

        template_data = dict(
            calibration_coefficients=' '.join([str(list(config['detectors'].values())[0]['ecal0']), str(list(config['detectors'].values())[0]['ecal1']), str(list(config['detectors'].values())[0]['ecal2'])]),
            start_datetime=now - datetime.timedelta(seconds=1),
            background_data=bg_data_string,
            transient_measurements=transient_string
        )
        templated_content = n42_template.render(**template_data)
        to_file(outfilename, templated_content)
    except:
        err_msg = exceptions.text_error_template().render()
        print(err_msg)
        raise

def make_static_templates():
    #make one static file per output period
    pass

def write_templates(config, test:dynamic_scenarios.DynamicIDSet):
    outdir = Path(config['output_folder'])/ 'SampleSpectra' / test.name
    outdir.mkdir(exist_ok=True, parents=True)
    detector = test.detector
    n42_mako_template = Template(filename=config['template_path'], input_encoding='utf-8')
    if detector.secondary_type == secondary_type['scenario']:
        secondary_spectrum = BackgroundSpectrum(livetime=test.shortest_bg_time, realtime=test.shortest_bg_time)
        secondary_spectrum.counts = test.bg_spectrum
    else:
        secondary_spectrum = None
        pass #can try to grab and pass on internal calibration spectra, but not doing this yet.

    reps, periods, bins = np.nested_iters(test.spectra, axes=[[0], [1], [2]])

    static = not config.get('dynamic_replay')
    if static:
        acq_time = test.scenario.output_period  # one output period = one file in this mode
        scenario = copy.copy(test.scenario)
        scenario.acq_time = acq_time
        for rep in reps:
            for period in periods:
                sample_counts = list(bins)
                filename = outdir / f'{test.name}_r{reps.iterindex:06}_p{periods.iterindex}.n42'
                create_n42_file_from_template(n42_mako_template, filename, scenario, detector, sample_counts,
                                      secondary_spectrum=secondary_spectrum)
    else: #dynamic template
        scenario=test.scenario
        for rep in reps:
            filename = outdir / f'{test.name}_r{reps.iterindex:06}.n42'
            sample_counts = test.spectra[reps.iterindex]
            create_n42_file_from_template(n42_mako_template, filename, scenario, detector, sample_counts,
                                          secondary_spectrum=secondary_spectrum)



def write_dynamic_templates(config, test:dynamic_scenarios.DynamicIDSet):
    testnamedir = Path(config['output_folder'])/ 'SampleSpectra' / test.name
    detector = test.detector
    n42_mako_template = Template(filename=config['template_path'], input_encoding='utf-8')