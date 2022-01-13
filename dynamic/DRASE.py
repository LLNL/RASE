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

import os, sys

currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

import importlib
from dynamic import dynamic_data_handling as dfs
from dynamic import dynamic_scenarios
from dynamic import dynamic_templating as dt
from dynamic import dynamic_scoring
import argparse
from pathlib import Path
from src.rase_functions import readTranslatedResultFile
from beautifultable import BeautifulTable
from dynamic.dynamic_run_functions import run_plots
import subprocess
import warnings

def load_configs(path_or_list ):
    try:
        return load_config(path_or_list)
    except AttributeError: #list of config files
        config = {}
        for path in path_or_list:
            config.update(load_config(path))
    return config


def load_config(yaml_path):
    import yaml
    config = yaml.safe_load(yaml_path)
    return config

def clear_directory(dir):
    import shutil
    if os.path.isdir(dir):
        shutil.rmtree(dir)
    while os.path.isdir(dir):  # necessary to deal with asynchronous behavior in windows
        import time
        time.sleep(1)
    os.makedirs(dir)

def run_translator(path,inputdir, outputdir):
    tpath = Path(path)

    popen_startupinfo = None
    if sys.platform.startswith("win"):
        popen_startupinfo = subprocess.STARTUPINFO()
        popen_startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        popen_startupinfo.wShowWindow = subprocess.SW_HIDE
    try:
        translator = importlib.import_module(f'translators.{tpath.name}', 'translators')
    except ImportError:
        try:
            spec = importlib.util.spec_from_file_location("translator", tpath)
            translator = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(translator)
        except AttributeError:
            translator=None
    if translator is not None:
        translator.main(inputdir, outputdir)
    else: #path is an executable
        command = [tpath,inputdir,outputdir]
        try:
            # see rase.py runTranslator() for rationale
            p = subprocess.run(command, stdout=subprocess.PIPE, stdin=subprocess.PIPE,
                               stderr=subprocess.STDOUT, encoding='utf-8', check=True,
                               startupinfo=popen_startupinfo)
        except subprocess.CalledProcessError as e:
            raise subprocess.CalledProcessError('Translator exe error: '+e)





def main(args):
    # print(__doc__)

    config = load_configs(args.config)
    dfs.DynamicData(config) #initialize data. Required.
    tests = dynamic_scenarios.make_tests(config)
    operations = config['operations']
    outdir = Path(config['output_folder'])

    columns = ['Test Name','Test Sources','Test Replications']
    if operations.get('evaluate_detection'):
        columns += ['Prob. of Detection']
    if operations.get('print_scores'):
        scorers = dynamic_scoring.make_scores(config)
        all_sources = set([s for test in tests.values() for s in test.scenario.sources.keys()])
        score_columns = [f'{sname}\n{source}' for sname in scorers.keys() for source in all_sources]
        columns += score_columns

    def run_all():
        for tname, test in tests.items():
            namedir = Path(tname)
            row = [tname, test.scenario.sources, test.scenario.config['replications']]
            test.make_models(force=operations.get('force_rebuild_models'))

            if operations.get('output_files'):
                sample_out_dir = outdir / 'SampleSpectra' / namedir
                clear_directory(sample_out_dir)
                test.get_spectra()
                dt.write_templates(config, test)

            if operations.get('replay_files'):
                # make output directory for replay output
                replay_out_dir = outdir / 'Replay' / namedir
                os.makedirs(replay_out_dir, exist_ok=True)
                clear_directory(replay_out_dir)
                runcmd = config['replay_command'].format(INPUTDIR=sample_out_dir, OUTPUTDIR=replay_out_dir)
                if config.get('replay_verbose'):
                    subprocess.run(runcmd, shell=True)
                else:
                    subprocess.run(runcmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

            translator_output_dir = outdir / 'Translated' / namedir
            if operations.get('translate_replay'):
                translator_input_dir = outdir / 'Replay'/ namedir
                clear_directory(translator_output_dir)
                run_translator(config["translator"],translator_input_dir,translator_output_dir)

            if operations.get('evaluate_detection'):
                replay_successes = 0
                dynamic_output = config.get('dynamic_replay')
                if dynamic_output:
                    found = [ 1 if test.scenario.config['replay_name'] in readTranslatedResultFile(file) else 0 for file in translator_output_dir.glob('*.n42')]
                    if not len(list(translator_output_dir.glob('*.n42'))) == test.scenario.replication:
                        warnings.warn(f'During "evaluate detection" step, not all results files found ({len(list(translator_output_dir.glob("*.n42")))} found, {test.scenario.replication} expected ). Ensure previous steps are running correctly.')
                else: #static case
                    found = [any([ test.scenario.config['replay_name'] in readTranslatedResultFile(file) for file in translator_output_dir.glob(f'{test.name}_r{rep:06}_p*.n42')])
                             for rep in range(test.scenario.replication) ]
                    missing = [rep for rep in range(test.scenario.replication) if not len(list(translator_output_dir.glob(f'{test.name}_r{rep:06}_p*.n42')))]
                    if any(missing):
                        warnings.warn(f'During "evaluate detection" step, expected at least one result file for every replication but didn\'t find one for each replication. Ensure previous steps are running correctly. Replications missing files are: {missing}')

                replay_successes = sum(found)
                detection_rate = replay_successes / test.scenario.replication
                row += [detection_rate]

            if operations.get('print_scores'):
                row += [scorer.score(test.models[source])  if source in test.scenario.sources.keys() else ''
                        for sname,scorer in scorers.items() for source in all_sources ]

            test.clear()#forget about spectra to save memory
            yield row


    table = BeautifulTable(maxwidth=200)
    table.columns.header= columns
    for line in table.stream(run_all(), append=True):
        print(line)
    if config.get('csv_output'):
        table.to_csv(config['csv_output'])
    if operations.get('show_plots'):
        run_plots(tests,config)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Dynamic RASE Command Line Interface")
    parser.add_argument('-c','--config',type=argparse.FileType('r'),nargs='+')
    args = parser.parse_args()
    main(args)
