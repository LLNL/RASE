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

from dynamic import dynamic_templating as dt
from dynamic import dynamic_plotting


def run_tests(tests, config):
    for tname, test in tests.items():
        test.do_all()

        rebinned_spectra = dt.integral_rebin(test.spectra, 1024)
        rebinned_bg = dt.integral_rebin(test.bg_spectrum, 1024, axis=0)
        dt.write_files(config, tname, test.scenario.output_times, rebinned_spectra, rebinned_bg)


def run_scores(tests, scorers):
    scores = {}
    for sname, scorer in scorers.items():
        print(sname)
        scores[sname] = {}
        if ('test' in scorer.score_def.keys()):
            tests_to_score = scorer.score_def['test']
            if not tests_to_score:
                tests_to_score = list(tests.keys())
            for tname in tests_to_score:
                if tname in tests.keys():
                    scores[sname][tname] = {}
                    for source in tests[tname].scenario.sources.keys():
                        # if not tests[tname].models[source] or not list(tests[tname].models[source].values())[0].built:
                        if not tests[tname].models or not tests[tname].models[source].built:
                            tests[tname].make_models()
                        scores[sname][tname][source] = scorer.score(tests[tname].models[source])
                else:
                    scores[sname][tname] = {}
                    scores[sname][tname][source] = None
                    print("Tests specified in the config file for the {} scorer don't exist.".format(sname))

        scorestring = ';\n'.join([f'{tname} {source}: {score}' for tname in scores[sname].keys() for source, score
                                  in scores[sname][tname].items()])
        print(f'{sname}:\n{scorestring}\n')


def run_plots(tests, config):
    runplots = config.get('run', {}).get('plots')
    if runplots:
        it = zip(runplots, [config['plots'][pname] for pname in runplots])
    else:
        it = config['plots'].items()
    for pname, plot_def in it:

        # by default, same bin for all tests
        bin_plot = None
        if 'bin' in plot_def.keys():
            bin_plot = plot_def['bin']
        if not bin_plot:
            bin_plot = [int(len(model.GPs) / 2)]

        # by default, plot the GP (i.e.: take out R^2 dependence
        plot_type = None
        if 'plot_type' in plot_def.keys():
            plot_type = plot_def['plot_type']
        if not plot_type:
            plot_type = 'model'

        # defaults to 3D plots
        if 'dimensions' in plot_def.keys() and plot_def['dimensions'] == 2:
            dimensionality = 2
            class_keys = dynamic_plotting.Plot2D().func_dict.keys()
        else:
            dimensionality = 3
            class_keys = dynamic_plotting.Plot3D().func_dict.keys()

        plot_methods = [mth for mth in class_keys if mth in plot_def['plotter']]
        if not plot_methods:
            print("Plot method defined by user does not exist")
            continue

        # defaults to not plotting error bars
        if 'plot_error' in plot_def.keys() and plot_def['plot_error'] is True:
            plot_error = True
        else:
            plot_error = False

        tests_to_plot = []
        if ('test' in plot_def.keys()) and plot_def['test']:
            for find_test in plot_def['test']:
                if find_test in tests.keys():
                    tests_to_plot.append(tests[find_test])
        else:
            for ntest_to_plot in tests.keys():
                tests_to_plot.append(tests[ntest_to_plot])
        if not tests_to_plot:
            print("Tests specified in the config file don't exist.")
            continue

        for test_to_plot in tests_to_plot:
            if not test_to_plot.models or list(test_to_plot.models.values())[0].built:
                test_to_plot.make_models()

            tests_to_plot_models = list(test_to_plot.models.values())

            for bin in bin_plot:
                if dimensionality == 2:
                    plotter = dynamic_plotting.Plot2D()
                else:
                    plotter = dynamic_plotting.Plot3D()

                plotter.init_plot(plot_def)  # initialize the plotter figure;
                for plot_method in plot_methods:

                    if dimensionality == 2:
                        for model in tests_to_plot_models:
                            assert hasattr(model, 'GPs')

                            train_xyz = [[spec.x, spec.y, spec.z] for spec in model.train_spectra]
                            plotter.func_dict[plot_method](model.spectra, train_xyz, plot_def['position'], plot_type,
                                                           bin, model.GPs[bin], plot_error)


                    else:
                        if plot_method == 'plot_3D_model':
                            for model in tests_to_plot_models:
                                assert hasattr(model, 'GPs')  # will there be a case where we have a different model
                                                              # called something differently that we would like to
                                                              # plot in this way?
                                plotter.func_dict[plot_method](model.GPs[bin], plot_type)

                        if plot_method == 'plot_3D_train':
                            for model in tests_to_plot_models:
                                assert hasattr(model, 'train_spectra')
                                assert hasattr(model, 'GPs')  # necessary for error and model plotting

                                plotter.func_dict[plot_method](model.train_spectra, plot_type, bin, model.GPs[bin],
                                                               plot_error)

                        elif plot_method == 'plot_3D_train_colored_by_model':
                            for model in tests_to_plot_models:
                                assert hasattr(model, 'train_spectra')
                                assert hasattr(model, 'GPs')

                                plotter.func_dict[plot_method](model.train_spectra, plot_type, bin, model.GPs[bin],
                                                               plot_error)

                        elif plot_method == 'plot_3D_test':
                            for model in tests_to_plot_models:
                                assert 'scorer' in plot_def.keys()
                                assert plot_def['scorer'] in config['scores'].keys()

                                if (('test_points' in config['scores'][plot_def['scorer']].keys()) and
                                        config['scores'][plot_def['scorer']]['test_points']):
                                    test_xyzs = config['scores'][plot_def['scorer']]['test_points']
                                else:
                                    test_xyzs = [[spec.x, spec.y, spec.z] for spec in model.spectra]

                                plotter.func_dict[plot_method](model.getSpectra(test_xyzs), plot_type, bin,
                                                               model.GPs[bin], plot_error)

                        elif plot_method == 'plot_3D_test_colored_by_model':
                            for model in tests_to_plot_models:
                                assert 'scores' in config.keys()
                                assert 'scorer' in plot_def.keys()
                                assert plot_def['scorer'] in config['scores'].keys()
                                assert hasattr(model, 'GPs')

                                if (('test_points' in config['scores'][plot_def['scorer']].keys()) and
                                        config['scores'][plot_def['scorer']]['test_points']):
                                    test_xyzs = config['scores'][plot_def['scorer']]['test_points']
                                else:
                                    test_xyzs = [[spec.x, spec.y, spec.z] for spec in model.spectra]

                                assert test_xyzs

                                plotter.func_dict[plot_method](model.getSpectra(test_xyzs), plot_type, bin,
                                                               model.GPs[bin], plot_error)

    dynamic_plotting.plt.show()
