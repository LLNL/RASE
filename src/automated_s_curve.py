###############################################################################
# Copyright (c) 2018-2022 Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory
#
# Written by J. Chavez, S. Czyz, G. Kosinovsky, V. Mozin, S. Sangiorgio
# RASE-support@llnl.gov.
#
# LLNL-CODE-841943, LLNL-CODE-829509
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

from PySide6.QtCore import QSize, Qt
from src.rase_functions import *
from PySide6.QtWidgets import QApplication, QMessageBox, QProgressDialog
from src.table_def import Scenario, Session, ScenarioMaterial, Material, \
    ScenarioBackgroundMaterial, ScenarioGroup, CorrespondenceTable
from src.correspondence_table_dialog import CorrespondenceTableDialog
from src.rase_settings import RaseSettings
from src.view_results_dialog import ViewResultsDialog


def generate_curve(r, input_data, advanced):
    """Primary function where the points that make up the S-curve are determined"""
    session = Session()
    if advanced['custom_name'] == '[Default]':
        group_name = ("AutoScurve_" + input_data['instrument'] + '_' + input_data['source'])
    else:
        suffix = 0
        while True:
            if session.query(ScenarioGroup).filter_by(name=advanced['custom_name']).first():
                if not session.query(ScenarioGroup).filter_by(name=advanced['custom_name']).first().scenarios:
                    group_name = (advanced['custom_name'])
                    break
                else:
                    suffix += 1
                    advanced['custom_name'] = advanced['custom_name'] + '_' + str(suffix)
            else:
                group_name = (advanced['custom_name'])
                break

    detName = [input_data['instrument']]
    detector = session.query(Detector).filter_by(name=detName[0]).first()
    condition = False
    already_done = False

    expand = 0
    first_run = True
    # All scenarios within the group that have the same source/backgrounds
    make_scen_group(session, group_name, input_data)
    scenIdall = make_scenIdall(session, input_data)
    # scenarios that will be rerun in this run
    scenIds_no_persist = []

    maxback = 0
    if input_data['background']:
        for bmat in input_data['background']:
            bmat = bmat[0]
            if bmat[0] == input_data['source_fd']:
                if maxback == 0:
                    maxback = float(bmat[2])
                else:
                    maxback = max(maxback, float(bmat[2]))
    if not maxback:
        maxback = 0.1

    while not condition:

        # newly generated scenIds, and all scenIds with source/backgrounds as defined in the auto s-curve gui
        scenIds, scenIds_no_persist, scenIdall = gen_scens(input_data, advanced, session, scenIdall,
                                                           scenIds_no_persist, group_name, advanced['repetitions'])
        abort = run_scenarios(r, scenIds, detector, input_data['replay'], condition, expand, first_run)
        first_run = False
        if abort:
            cleanup_scenarios(advanced['repetitions'], scenIds_no_persist)
            return

        r.calculateScenarioStats(1, scenIdall, detName)

        if input_data['results_type'] == 'C&C':
            results = r.scenario_stats_df['C&C']
        elif input_data['results_type'] == 'TP':
            results = r.scenario_stats_df['TP']
        elif input_data['results_type'] == 'Precision':
            results = r.scenario_stats_df['Precision']
        elif input_data['results_type'] == 'Recall':
            results = r.scenario_stats_df['Recall']
        elif input_data['results_type'] == 'Fscore':
            results = r.scenario_stats_df['F_Score']
        else:  # to add more later
            results = r.scenario_stats_df['PID']
        if not input_data['invert_curve']:
            results = results.sort_values()
        else:
            results = results.sort_values(ascending=False)

        if max(results) >= advanced['upper_bound'] and min(results) <= advanced['lower_bound']:
            """If there are values surrounding the rising edge"""
            # find scenarios in for cases
            ids_on_edge = []
            start_list = []
            end_list = []
            prev_point = False
            for index, result in enumerate(results):
                if (not input_data['invert_curve'] and result <= advanced['lower_bound']) or \
                        (input_data['invert_curve'] and result >= advanced['upper_bound']):
                    start_list.append(results.index[index].split('*')[0])
                    if prev_point:
                        ids_on_edge = []  # rose and then dropped back down (i.e.: fluctuations)
                        prev_point = False
                elif advanced['lower_bound'] <= result <= advanced['upper_bound']:
                    ids_on_edge.append(results.index[index].split('*')[0])
                    prev_point = True
                elif (not input_data['invert_curve'] and result >= advanced['upper_bound']) or \
                        (input_data['invert_curve'] and result <= advanced['lower_bound']):
                    end_list.append(results.index[index].split('*')[0])
            # Grab doses for scenarios on the edges of the S-curve. The first value in each list is
            # the value that is the second closest to the rising edge, and the second is the closest
            start_val = [-1, -1]
            end_val = [-1, -1]

            for scenid in scenIdall:
                scen = session.query(Scenario).filter_by(id=scenid).first()
                if scenid in start_list:
                    if start_val[1] == -1 or scen.scen_materials[0].dose >= start_val[1]:
                        start_val = set_bounds(start_val, scen.scen_materials[0].dose)
                if scen.id in end_list:
                    if end_val[1] == -1 or scen.scen_materials[0].dose < end_val[1]:
                        end_val = set_bounds(end_val, scen.scen_materials[0].dose)

            # check if there are enough points on the rising edge
            if len(ids_on_edge) >= advanced['rise_points']:
                condition = True
                # to avoid persistence errors by reusing a value with the same ID but different replications
                edge_count, bound_scens_start, bound_scens_end = check_edge_ids(session, input_data['input_reps'],
                                                                                start_list, end_list, ids_on_edge,
                                                                                detector)
                if edge_count < advanced['rise_points'] or bound_scens_start < 2 or bound_scens_end < 2:
                    advanced['min_guess'] = start_val[0] * 0.9
                    advanced['max_guess'] = end_val[0] * 1.1
                    advanced['num_points'] = advanced['rise_points'] + 4
                else:
                    already_done = True
            else:
                # avoid infinite loop due to being stuck on edge cases. Moves slightly inward to better populate edge
                if start_val[1] == advanced['min_guess']:
                    advanced['min_guess'] = start_val[1] + (end_val[1] - start_val[1]) * 0.01
                else:
                    advanced['min_guess'] = start_val[1]
                if end_val[1] == advanced['max_guess']:
                    advanced['max_guess'] = end_val[1] - (end_val[1] - start_val[1]) * 0.01
                else:
                    advanced['max_guess'] = end_val[1]
                advanced['num_points'] = advanced['rise_points']  # + 4

        elif min(results) >= advanced['lower_bound']:
            """If the quoted results aren't small enough yet"""
            expand += 1
            dose_list = []
            for scenId in scenIdall:
                scen = session.query(Scenario).filter_by(id=scenId).first()
                dose_list.append(scen.scen_materials[0].dose)
            dose_list.sort()

            if not input_data['invert_curve']:
                dose_bound = dose_list[0]
                if (0 < dose_bound <= 1E-9 * maxback and len(scenIdall) >= 9) or 0 < dose_bound <= 1E-12:
                    fail_never(r, scenIdall, [input_data['instrument']])
                    return
                if len(dose_list) > 1:
                    step_ratio = dose_list[0] / dose_list[1]
                else:
                    step_ratio = dose_list[0] * 0.9
                advanced['min_guess'] = advanced['min_guess'] * step_ratio
                advanced['max_guess'] = advanced['min_guess']
                advanced['num_points'] = 1
            else:
                dose_bound = dose_list[-1]
                if dose_bound >= 40 * maxback and len(scenIdall) >= 9:
                    fail_never(r, scenIdall, [input_data['instrument']])
                    return
                if len(dose_list) > 1:
                    step_ratio = dose_list[-1] / dose_list[-2]
                else:
                    step_ratio = dose_list[0] * 1.1
                advanced['min_guess'] = advanced['max_guess'] * step_ratio
                advanced['max_guess'] = advanced['min_guess']
                advanced['num_points'] = 1

        elif max(results) <= advanced['upper_bound']:
            """If the quoted results aren't large enough yet"""
            expand += 1
            dose_list = []
            for scenId in scenIdall:
                scen = session.query(Scenario).filter_by(id=scenId).first()
                # for scen in session.query(ScenarioGroup).filter_by(name=group_name).first().scenarios:
                dose_list.append(scen.scen_materials[0].dose)
            dose_list.sort()
            if not input_data['invert_curve']:
                dose_bound = dose_list[-1]
                if dose_bound >= 40 * maxback and len(scenIdall) >= 9:
                    fail_always(r, scenIdall, [input_data['instrument']])
                    return
                if len(dose_list) > 1:
                    step_ratio = dose_list[-1] / dose_list[-2]
                else:
                    step_ratio = dose_list[0] * 1.1
                advanced['min_guess'] = advanced['max_guess'] * step_ratio
                advanced['max_guess'] = advanced['min_guess']
                advanced['num_points'] = 1
            else:
                dose_bound = dose_list[0]
                if (0 < dose_bound <= 1E-9 * maxback and len(scenIdall) >= 9) or 0 < dose_bound <= 1E-12:
                    fail_always(r, scenIdall, [input_data['instrument']])
                    return
                if len(dose_list) > 1:
                    step_ratio = dose_list[0] / dose_list[1]
                else:
                    step_ratio = dose_list[0] * 0.9
                advanced['min_guess'] = advanced['min_guess'] * step_ratio
                advanced['max_guess'] = advanced['min_guess']
                advanced['num_points'] = 1

    if condition:
        if not already_done:
            scenIds, _, _ = gen_scens(input_data, advanced, session, scenIdall, scenIds_no_persist, group_name,
                                      input_data['input_reps'], condition)
            detector = session.query(Detector).filter_by(name=detName[0]).first()
            abort = run_scenarios(r, scenIds, detector, input_data['replay'], condition)
            if abort:
                cleanup_scenarios(advanced['repetitions'], scenIds_no_persist)
                cleanup_scenarios(input_data['input_reps'], scenIds)
                return

        if advanced['cleanup']:
            cleanup_scenarios(advanced['repetitions'], scenIds_no_persist)
            r.populateScenarios()

        msgbox = QMessageBox(QMessageBox.Question, 'S-Curve generation complete!',
                             'Would you like to view the results?')
        msgbox.addButton(QMessageBox.Yes)
        msgbox.addButton(QMessageBox.No)
        answer = msgbox.exec()
        if answer == QMessageBox.Yes:
            viewResults(r, scenIds, [input_data['instrument']])


def check_edge_ids(session, replications, start_list, end_list, edge_ids, detector):
    """Check if there are results ready for values on the rising edge of the S-curve"""
    settings = RaseSettings()
    counter = [0] * 3
    for i, ids_list in enumerate([edge_ids, start_list, end_list]):
        for id in ids_list:
            scen = session.query(Scenario).filter_by(id=id).first()
            results_dir = get_results_dir(settings.getSampleDirectory(), detector, id)
            if files_endswith_exists(results_dir, (".n42", ".res")) and scen.replication >= replications:
                counter[i] += 1

    return counter[0], counter[1], counter[2]


def fail_never(r, scenIdall, inst):
    msgbox = QMessageBox(QMessageBox.Question, 'Convergence Issue',
                         'There may be some issue; the isotope identifier is always identifying some of '
                         'the isotope of interest! Please take a close look at the results for trouble '
                         'shooting. Would you like to open the results table for this scenario group?')
    print('There may be some issue... the isotope identifier is always identifying some of the isotope of '
          'interest! Please take a close look at the results for trouble shooting')
    create_answer_box(msgbox, r, scenIdall, inst)
    return True


def fail_always(r, scenIdall, inst):
    msgbox = QMessageBox(QMessageBox.Question, 'Convergence Issue',
                         'There may be some issue; no isotopes are being identified at any attempted '
                         'intensity. You might want to check your correspondence table. Would you like to '
                         'open the results table for this scenario group?')
    print('There may be an issue... not IDing anything. You may want to check your correspondence table!')
    create_answer_box(msgbox, r, scenIdall, inst)
    return True


def create_answer_box(msgbox, r, scenIdall, inst):
    msgbox.addButton(QMessageBox.Yes)
    msgbox.addButton(QMessageBox.No)
    answer = msgbox.exec()
    if answer == QMessageBox.Yes:
        viewResults(r, scenIdall, inst)


def make_scen_group(session, group_name, input_data):
    scenGroup = session.query(ScenarioGroup).filter_by(name=group_name).first()

    if not scenGroup:
        scenGroup = ScenarioGroup(name=group_name, description='')
        session.add(scenGroup)
    else:
        scenGroup.description = ''


def make_scenIdall(session, input_data):
    settings = RaseSettings()
    detector = session.query(Detector).filter_by(name=input_data['instrument']).first()

    repeat_scens = []
    for bkgd_data in input_data['background']:
        bkgd = bkgd_data[0]
        repeat_scens = repeat_scens + session.query(Scenario).join(ScenarioMaterial).join(
            ScenarioBackgroundMaterial).filter(
            Scenario.acq_time == float(input_data['dwell_time'])).filter(
            ScenarioMaterial.fd_mode == input_data['source_fd'],
            ScenarioMaterial.material_name == input_data['source']).filter(
            ScenarioBackgroundMaterial.fd_mode == bkgd[0],
            ScenarioBackgroundMaterial.material_name == bkgd[1].name,
            ScenarioBackgroundMaterial.dose == bkgd[2]).all()

    common_scens = [x for x in set(repeat_scens) if repeat_scens.count(x) == len(input_data['background'])]

    scenIdall = []
    for scen in common_scens:
        results_dir = get_results_dir(settings.getSampleDirectory(), detector, scen.id)
        if files_endswith_exists(results_dir, (".n42", ".res")):
            scenIdall.append(scen.id)

    return scenIdall


def gen_scens(input_data, advanced, session, scenIdall, scenIds_no_persist, group_name, reps=1, condition=False):
    settings = RaseSettings()
    """Generate the scenarios, including source, background, dwell time, and replications"""

    scenGroup = session.query(ScenarioGroup).filter_by(name=group_name).first()

    test_points = logspace_gen(num_points=advanced['num_points'],
                               start_g=advanced['min_guess'], end_g=advanced['max_guess'])

    if advanced['add_points'] and condition:
        # high-stats run
        test_points += advanced['add_points']

    m = session.query(Material).filter_by(name=input_data['source']).first()

    scenIds = []  # scenarios that would be generated here regardless of persistence
    # to prevent accidental duplicates
    for d in set(test_points):
        sm = ScenarioMaterial(material=m, fd_mode=input_data['source_fd'], dose=d)
        sb = []
        for [(mode, mat, dose)] in input_data['background']:
            bm = session.query(Material).filter_by(name=mat.name).first()
            sb.append(ScenarioBackgroundMaterial(material=bm, fd_mode=mode, dose=float(dose)))

        persist = session.query(Scenario).filter_by(id=Scenario.scenario_hash(input_data['dwell_time'], [sm],
                                                                              sb)).first()
        if persist:
            if persist.replication < reps:
                scenDelete = session.query(Scenario).filter(Scenario.id == persist.id)
                matDelete = session.query(ScenarioMaterial).filter(ScenarioMaterial.scenario_id == persist.id)
                backgMatDelete = session.query(ScenarioBackgroundMaterial).filter(
                    ScenarioBackgroundMaterial.scenario_id == persist.id)
                matDelete.delete()
                backgMatDelete.delete()
                scenDelete.delete()

                folders = [fd for fd in glob.glob(os.path.join(settings.getSampleDirectory(), "*" + persist.id + "*"))]
                for folder in folders:
                    shutil.rmtree(folder)

                scens = Scenario(input_data['dwell_time'], reps, [sm], sb, [], [])
                scenIds.append(scens.id)
                scenIds_no_persist.append(scens.id)
            else:
                scenIds.append(persist.id)
        else:
            scens = Scenario(input_data['dwell_time'], reps, [sm], sb, [], [])
            scenIds.append(scens.id)
            scenIds_no_persist.append(scens.id)
            scenGroup.scenarios.append(scens)

    scenIdall = scenIdall + [s for s in scenIds if not s in scenIdall]

    session.commit()

    return scenIds, scenIds_no_persist, scenIdall


def run_scenarios(r, scenIds, detector, replay_name, condition=False, expand=0, first_run=False):
    settings = RaseSettings()

    if condition:
        len_prog = len(scenIds)
        progress = QProgressDialog('S-curve range found!\n Generating higher statistics scenarios...', 'Abort', 0,
                                   len(scenIds), r)
    else:
        if not len(scenIds):
            return
        elif len(scenIds) == 1:
            len_prog = 3
            progress = QProgressDialog('Expanding S-curve search...\n Steps taken = ' + str(expand - 1) +
                                       ', Scenario ID = ' + scenIds[0], 'Abort', 0, len_prog, r)
        else:
            if first_run:
                len_prog = len(scenIds)
                progress = QProgressDialog('Generating range-finding S-curve scenarios...', 'Abort', 0, len_prog, r)
            else:
                len_prog = len(scenIds)
                progress = QProgressDialog('Adding scenarios to rising edge...', 'Abort', 0, len_prog, r)

    progress.setMaximum(len_prog)
    count = 0
    progress.setMinimumDuration(0)
    progress.setValue(count)
    progress.resize(QSize(300, 50))
    progress.setWindowModality(Qt.WindowModal)
    for scenId in scenIds:
        if progress.wasCanceled():
            progress.close()
            return True
        results_dir = get_results_dir(settings.getSampleDirectory(), detector, scenId)
        # do not regenerate already existing results
        # using scenIds instead of scenIds_no_persist in case the scenario exists but with no results
        if not files_endswith_exists(results_dir, (".n42", ".res")):
            r.genSpectra([scenId], [detector.name], False)
            if len(scenIds) == 1:
                count += 1
                progress.setValue(count)
            r.runReplay([scenId], [detector.name], False)
            if len(scenIds) == 1:
                count += 1
                progress.setValue(count)
            r.runTranslator([scenId], [detector.name], [replay_name], False)
        count += 1
        progress.setValue(count)
    progress.setValue(len_prog)


def logspace_gen(num_points=6, start_g=1E-5, end_g=1):
    """Generates a uniformly spaced list of points"""
    end_g = 1E-10 if end_g < 1E-10 else end_g
    start_g = 1E-12 if start_g < 1E-12 else start_g
    test_points = np.geomspace(start_g, end_g, num_points)
    return [float('{:9.12f}'.format(i)) for i in test_points]


def set_bounds(val, dose):
    if val[0] == -1:
        val[0] = dose
    else:
        val[0] = val[1]
    val[1] = dose
    return val


def cleanup_scenarios(rangefind_rep, scenIds):
    """Remove scenarios from the database that were rangefinders, i.e.: low replication scenarios"""
    settings = RaseSettings()
    session = Session()

    scenarios = []
    for scen in scenIds:
        scenarios.append(session.query(Scenario).filter_by(id=scen).first())

    scens_to_delete = []
    for scen in scenarios:
        if scen.replication == rangefind_rep:
            scens_to_delete.append(scen.id)

    delete_scenario(scens_to_delete, settings.getSampleDirectory())

    session.commit()


def viewResults(r, scenIdall, detector):
    """
    Opens Results table
    """
    # need a correspondence table in order to display results!
    session = Session()
    settings = RaseSettings()
    default_corr_table = session.query(CorrespondenceTable).filter_by(is_default=True).one_or_none()
    if not default_corr_table:
        msgbox = QMessageBox(QMessageBox.Question, 'No Correspondence Table set!',
                             'No correspondence table set! Would you like to set a correspondence table now?')
        msgbox.addButton(QMessageBox.Yes)
        msgbox.addButton(QMessageBox.No)
        answer = msgbox.exec()
        if answer == QMessageBox.Yes:
            CorrespondenceTableDialog().exec_()
            settings.setIsAfterCorrespondenceTableCall(True)
        else:
            return

    selected_scenarios = scenIdall
    r.calculateScenarioStats(1, selected_scenarios, detector)
    ViewResultsDialog(r, selected_scenarios, detector).exec_()


if __name__ == "__main__":
    from src.rase import Rase

    app = QApplication(sys.argv)  # required to call RASE object
    r = Rase(args='')

    input_inst = 'dummy'
    input_replay = 'dummy_replay'
    input_source = 'Ba133'
    source_units = 'DOSE'
    static_background = [[('DOSE', 'Bgnd', 0.08)]]
    dwell_time = 30
    results_type = 'PID'
    input_repetitions = 5
    invert_curve = False

    min_init_g = 1E-8
    max_init_g = 1E-3
    points_on_edge = 5
    init_repetitions = 10
    add_points = ''
    custom_name = '[Default]'
    cleanup = False
    num_points = 6
    lower_bound = 0.1
    upper_bound = 0.9

    input_d = {"instrument": input_inst,
               "replay": input_replay,
               "source": input_source,
               "source_fd": source_units,
               "background": static_background,
               "dwell_time": dwell_time,
               "results_type": results_type,
               "input_reps": input_repetitions,
               "invert_curve": invert_curve
               }

    input_advanced = {"min_guess": min_init_g,
                      "max_guess": max_init_g,
                      "rise_points": points_on_edge,
                      "repetitions": init_repetitions,
                      "add_points": add_points,
                      "cleanup": cleanup,
                      "custom_name": custom_name,
                      "num_points": num_points,
                      "lower_bound": lower_bound,
                      "upper_bound": upper_bound
                      }

    generate_curve(r, input_d, input_advanced)
    print('complete!')
