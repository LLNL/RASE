from time import sleep

import pytest
from PyQt5.QtCore import Qt, QTimer, QObject, pyqtSignal
from PyQt5.QtGui import QContextMenuEvent
from PyQt5.QtWidgets import QDialogButtonBox, QMenu, QApplication

from src.correspondence_table_dialog import CorrespondenceTableDialog as ctd
from src.detector_dialog import DetectorDialog
from src.rase import Rase
from src.rase_functions import *
from src.rase_settings import RaseSettings
from src.scenario_group_dialog import GroupSettings as gsd
from src.table_def import ScenarioGroup, Replay

pytest.main(['-s'])


@pytest.fixture(scope="class", autouse=True)
def reboot_database():
    """Delete and recreate the database between test classes"""
    settings = RaseSettings()
    if os.path.isdir(settings.getSampleDirectory()):
        shutil.rmtree(settings.getSampleDirectory())
    if os.path.isfile(settings.getDatabaseFilepath()):
        os.remove(settings.getDatabaseFilepath())
        initializeDatabase(settings.getDatabaseFilepath())


@pytest.fixture(scope='session', autouse=True)
def complete_tests():
    """Make sure no sample spectra are left after the final test is run"""
    settings = RaseSettings()
    original_data_dir = settings.getDataDirectory()
    settings.setDataDirectory(os.path.join(os.getcwd(),'__temp_test_rase'))
    yield None  # anything before this line will be run prior to the tests
    print('CLEANING UP')  # run after the last test
    settings = RaseSettings()
    if os.path.isdir(settings.getSampleDirectory()):
        shutil.rmtree(settings.getSampleDirectory())
    if os.path.isfile(settings.getDatabaseFilepath()):
        os.remove(settings.getDatabaseFilepath())
    settings.setDataDirectory(original_data_dir)
    print('CLEANUP COMPLETE')


class Helper(QObject):
    finished = pyqtSignal()


class HelpObjectCreation:

    def get_default_detector_name(self):
        return 'test_detector'

    def get_default_replay_name(self):
        return 'dummy_replay'

    def get_default_channel_count(self):
        return 1024

    def get_default_scen_pars(self):
        acq_times = self.get_default_acq_times()
        replications = self.get_default_replications()
        fd_mode, fd_mode_back = self.get_default_fd_modes()
        mat_names, back_names = self.get_default_mat_names()
        doses, doses_back = self.get_default_doses()

        return acq_times, replications, fd_mode, fd_mode_back, mat_names, back_names, doses, doses_back

    def get_default_acq_times(self):
        return [60, 20]

    def get_default_replications(self):
        return [3, 3]

    def get_default_fd_modes(self):
        return [['DOSE'], ['FLUX', 'DOSE']], [['DOSE'], ['DOSE']]

    def get_default_mat_names(self):
        return [['dummy_mat_1'], ['dummy_mat_2', 'dummy_mat_3']], [['dummy_back_1'], ['dummy_back_2']]

    def get_default_doses(self):
        return [[.31], [2.3, 1.1]], [[.08], [.077]]

    def get_default_rt_lt(self):
        return [[[1200.0, 1189.2]], [[1200.0, 1164.2], [1200.0, 1199.2]]], [[[3600.0, 3598.2]], [[3600.0, 3573.1]]]

    def get_default_sensitivities(self):
        return [[10000], [300, 400]], [[2300], [2100]]

    def get_default_base_counts(self):
        n_ch = self.get_default_channel_count()
        templist = []
        for n in [2367, 469, 381, 1213, 1107]:
            temparr = np.array([n] * n_ch)
            tempcounts = [str(a) for a in temparr[:-1]] + [str(temparr[-1])]
            templist.append(', '.join(tempcounts))
        return [[templist[0]], [templist[1], templist[2]]], [[templist[3]], [templist[4]]]

    def get_scengroups(self, session):
        group_name = 'group_name'
        if session.query(ScenarioGroup).filter_by(name=group_name).first():
            return [session.query(ScenarioGroup).filter_by(name=group_name).first()]

        gsd.add_groups(session, group_name)
        assert session.query(ScenarioGroup).filter_by(name=group_name).first()
        return [session.query(ScenarioGroup).filter_by(name=group_name).first()]

    def create_base_materials(self, fd_mode, fd_mode_back, mat_names, back_names, doses, doses_back):
        session = Session()

        for a, f in zip([mat_names, back_names], [get_or_create_material, get_or_create_material]):
            for s in a:
                for m in s:
                    assert f(session, m)

        mat_dose_arr = [[m, d, f] for m, d, f in zip(fd_mode, mat_names, doses)]
        back_dose_arr = [[m, d, f] for m, d, f in zip(fd_mode_back, back_names, doses_back)]

        scens = []
        bscens = []
        for scenlists, m_arr, func in zip([scens, bscens],
                                          [mat_dose_arr, back_dose_arr],
                                          [get_or_create_material, get_or_create_material]):
            for m in m_arr:
                slist = []
                for a, b, c in zip(*m):
                    slist.append((a, func(session, b), c))
                scenlists.append(slist)

        scenMaterials = []
        bcgkScenMaterials = []
        for scen in scens:
            scenMaterials.append([ScenarioMaterial(material=m, dose=float(d), fd_mode=u) for u, m, d in scen])
        for bscen in bscens:
            bcgkScenMaterials.append([ScenarioBackgroundMaterial(material=m, dose=float(d), fd_mode=u)
                                      for u, m, d in bscen])

        return scenMaterials, bcgkScenMaterials

    def add_default_scens(self):
        acq_times, replications, fd_mode, fd_mode_back, mat_names, back_names, doses, doses_back = self.get_default_scen_pars()
        session = Session()

        scenMaterials, bcgkScenMaterials = self.create_base_materials(fd_mode, fd_mode_back, mat_names, back_names,
                                                                    doses, doses_back)

        for acqTime, replication, baseSpectrum, backSpectrum in zip(acq_times, replications, scenMaterials, bcgkScenMaterials):
            scen_hash = Scenario.scenario_hash(float(acqTime), baseSpectrum, backSpectrum, [])
            scen_exists = session.query(Scenario).filter_by(id=scen_hash).first()
            if scen_exists:
                root_folder = '.'
                delete_scenario(scen_hash, root_folder)
                assert session.query(Scenario).filter_by(id=scen_hash).first() is None
            Scenario(float(acqTime), replication, baseSpectrum, backSpectrum, [], self.get_scengroups(session))

    def create_empty_detector(self):
        detector_name = self.get_default_detector_name()
        session = Session()
        d_dialog = DetectorDialog(None)
        if session.query(Detector).filter_by(name=detector_name).first():
            delete_instrument(session, detector_name)
        d_dialog._set_detector_name(session, detector_name)

    def add_default_base_spectra(self):
        session = Session()
        baseSpectra = []
        mat_names, back_names = self.get_default_mat_names()
        fg_rt_lt, bg_rt_lt = self.get_default_rt_lt()
        fg_fds, bg_fds = self.get_default_fd_modes()
        fg_sens, bg_sens = self.get_default_sensitivities()
        fg_bscounts, bg_bscounts = self.get_default_base_counts()


        for mats, real_live_times, fd_modes, sensitivities, bscounts in zip(mat_names + back_names,
                                                                        fg_rt_lt + bg_rt_lt, fg_fds + bg_fds,
                                                                        fg_sens + bg_sens, fg_bscounts + bg_bscounts):
            for m, r_l_t, fd, sens, cnts in zip(mats, real_live_times, fd_modes, sensitivities, bscounts):
                if fd == 'DOSE':
                    rase_sensitivity = sens
                    flux_sensitivity = None
                else:
                    rase_sensitivity = None
                    flux_sensitivity = sens

                baseSpectra.append(BaseSpectrum(material=get_or_create_material(session, m),
                                                filename='.', realtime=r_l_t[0], livetime=r_l_t[1],
                                                rase_sensitivity=rase_sensitivity, flux_sensitivity=flux_sensitivity,
                                                baseCounts=cnts))

        return baseSpectra

    def get_default_detector_params(self):
        chan_count = self.get_default_channel_count()
        ecal0 = 0.1
        ecal1 = 1
        ecal2 = 0.0000001
        ecal3 = 0

        manufacturer = 'manufacturer'
        instr_id = 'instr_id'
        class_code = 'class_code'
        hardware_version = 'hardware_version'
        replay = None
        resultsTranslator = None
        txtDetectorDescription = 'txtDetectorDescription'

        spec_properties = [chan_count, ecal0, ecal1, ecal2, ecal3]
        params = [manufacturer, instr_id, class_code, hardware_version, replay, resultsTranslator, txtDetectorDescription]


        return spec_properties, params

    def set_default_detector_params(self):
        spec_properties, params = self.get_default_detector_params()
        d_dialog = DetectorDialog(None, self.get_default_detector_name())
        d_dialog._set_ch_counts_ecal(*spec_properties)
        d_dialog._set_detector_params(*params)

    def create_default_replay(self):
        session = Session()
        name = self.get_default_replay_name()
        exe_path = os.path.join(os.pardir, 'tests/fixed_replay.py')
        is_cmd_line = True
        settings = 'INPUTDIR OUTPUTDIR'
        n42_template_path = None
        input_filename_suffix = '.n42'

        if session.query(Replay).filter_by(name=name).first():
            return

        replay = Replay()
        replay.name = name
        replay.exe_path = exe_path
        replay.is_cmd_line = is_cmd_line
        replay.settings = settings
        replay.n42_template_path = n42_template_path
        replay.input_filename_suffix = input_filename_suffix
        session.add(replay)

    def add_default_replay(self):
        session = Session()
        detector = session.query(Detector).filter_by(name=self.get_default_detector_name()).first()

        detector.replay_name = self.get_default_replay_name()
        detector.replay = session.query(Replay).filter_by(name=self.get_default_replay_name()).first()

    def create_default_detector_scen(self):
        session = Session()

        self.add_default_scens()
        self.create_empty_detector()
        baseSpectra = self.add_default_base_spectra()

        detector = session.query(Detector).filter_by(name=self.get_default_detector_name()).first()
        for bs in baseSpectra:
            detector.base_spectra.append(bs)
        self.set_default_detector_params()
        self.create_default_replay()
        self.add_default_replay()
        session.commit()

    def create_default_corr_table(self):
        session = Session()
        table_name = 'default_table'
        iso = 'dummy_bgnd'

        table = ctd.create_corr_table(session, table_name)
        ctd.add_corr_table_entry(table, iso)

        session.commit()

    def create_default_workflow(self):
        self.create_default_detector_scen()
        self.create_default_corr_table()

    def get_default_workflow(self):
        session = Session()
        det_names = [d.name for d in session.query(Detector).filter_by(name=self.get_default_detector_name()).all()]
        assert det_names
        scen_ids = [scen.id for scen in session.query(Scenario).all()]
        assert scen_ids
        return det_names, scen_ids

# Database testing
class Test_Database:
    def test_set_db_loc(self):
        """
        Verifies that the database location can be set
        """
        import os
        data_dir = os.getcwd()
        settings = RaseSettings()
        settings.setDataDirectory(data_dir)
        assert data_dir == settings.getDataDirectory()


    def test_database(self):
        """
        Make sure Database exists
        """
        session = Session()
        assert session


# GUI testing
class Test_GUI:
    def test_gui(self, qtbot):
        """
        Verifies the GUI is visible and key buttons are enabled
        """
        w = Rase([])
        w.show()
        qtbot.addWidget(w)
        qtbot.waitExposed(w)
        sleep(.25)

        def close_d_dialog():
            qtbot.mouseClick(w.d_dialog.buttonBox.button(QDialogButtonBox.Cancel), Qt.LeftButton)

        QTimer.singleShot(500, close_d_dialog)
        qtbot.mouseClick(w.btnAddDetector, Qt.LeftButton)

        assert w.isVisible()
        assert w.btnAddDetector.isEnabled()
        assert w.btnAddScenario.isEnabled()
        assert w.menuFile.isEnabled()
        assert w.menuTools.isEnabled()
        assert w.menuTools_2.isEnabled()
        assert w.menuHelp.isEnabled()


    def test_detector_dialog_opens(self, qtbot):
        """
        Can we open and close the detector dialog?
        """
        w = Rase([])
        w.show()
        qtbot.addWidget(w)

        def close_d_dialog():
            assert w.d_dialog
            qtbot.mouseClick(w.d_dialog.buttonBox.button(QDialogButtonBox.Cancel), Qt.LeftButton)

        QTimer.singleShot(500, close_d_dialog)
        qtbot.mouseClick(w.btnAddDetector, Qt.LeftButton)

        assert not w.d_dialog


    def test_db_gui_agreement(self, qtbot):
        """
        Assures all scenarios/tests are appearing
        """
        session = Session()
        w = Rase([])
        qtbot.addWidget(w)

        assert w.tblScenario.rowCount() == len(session.query(Scenario).all())
        assert w.tblDetectorReplay.rowCount() == len(session.query(Detector).all())


# Instrument creation and deletion testing
class Test_Inst_Create_Delete:
    def test_detector_create_delete(self):
        """
        Verifies that we can create and delete detectors
        """
        hoc = HelpObjectCreation()
        detector_name = hoc.get_default_detector_name()
        hoc.create_empty_detector()
        session = Session()

        assert session.query(Detector).filter_by(name=detector_name).first()
        delete_instrument(session, detector_name)
        assert not session.query(Detector).filter_by(name=detector_name).first()

    def test_create_delete_with_bspec_and_params(self):
        """
        Verifies that we can create and delete detectors with base spectra and various parameters set
        """
        hoc = HelpObjectCreation()
        detector_name = hoc.get_default_detector_name()
        hoc.create_empty_detector()
        session = Session()

        assert len(session.query(BaseSpectrum).all()) == 0
        baseSpectra = hoc.add_default_base_spectra()
        assert len(baseSpectra)

        detector = session.query(Detector).filter_by(name=detector_name).first()
        for bs in baseSpectra:
            detector.base_spectra.append(bs)
        assert len(session.query(BaseSpectrum).all()) == len(baseSpectra)

        hoc.set_default_detector_params()

        assert session.query(Detector).filter_by(name=detector_name).first()
        delete_instrument(session, detector_name)
        assert not session.query(Detector).filter_by(name=detector_name).first()
        assert len(session.query(BaseSpectrum).all()) == 0

    def test_replay_create_delete(self):
        hoc = HelpObjectCreation()
        hoc.create_default_replay()

        session = Session()
        assert session.query(Replay).filter_by(name=hoc.get_default_replay_name()).first()
        replay_delete = session.query(Replay).filter_by(name=hoc.get_default_replay_name())
        replay_delete.delete()
        assert session.query(Replay).filter_by(name=hoc.get_default_replay_name()).first() is None

    def test_detector_create_delete_gui(self, qtbot):
        detector_name = 'test_detector'
        w = Rase([])
        qtbot.addWidget(w)
        w.show()
        qtbot.waitForWindowShown(w)

        def add_detector():
            qtbot.keyClicks(w.d_dialog.txtDetector, detector_name)
            qtbot.mouseClick(w.d_dialog.buttonBox.button(QDialogButtonBox.Ok), Qt.LeftButton)

        QTimer.singleShot(100, add_detector)
        qtbot.mouseClick(w.btnAddDetector, Qt.LeftButton)

        helper = Helper()

        def handle_timeout():
            menu = None
            for tl in QApplication.topLevelWidgets():
                if isinstance(tl, QMenu) and len(tl.actions()) > 0 and tl.actions()[0].text() == "Delete Instrument":
                    menu = tl
                    break

            assert menu is not None
            delete_action = None

            for action in menu.actions():
                if action.text() == 'Delete Instrument':
                    delete_action = action
                    break
            assert delete_action is not None
            rect = menu.actionGeometry(delete_action)
            QTimer.singleShot(100, helper.finished.emit)
            qtbot.mouseClick(menu, Qt.LeftButton, pos=rect.center())

        with qtbot.waitSignal(helper.finished, timeout=5 * 1000):
            QTimer.singleShot(1000, handle_timeout)
            item = None
            for row in range(w.tblDetectorReplay.rowCount()):
                if w.tblDetectorReplay.item(row, 0).text() == detector_name:
                    item = w.tblDetectorReplay.item(row, 0)
                    break
            assert item is not None
            rect = w.tblDetectorReplay.visualItemRect(item)
            event = QContextMenuEvent(QContextMenuEvent.Mouse, rect.center())
            QApplication.postEvent(w.tblDetectorReplay.viewport(), event)

        # make sure the detector is not in the database or the instrument table
        assert w.tblDetectorReplay.rowCount() == 0
        session = Session()
        assert not session.query(Detector).filter_by(name=detector_name).first()


# Scenario group creation testing
class Test_ScenGroup_Create_Delete:
    def test_create_scengroup(self):
        group_name = 'group_name'
        session = Session()
        if session.query(ScenarioGroup).filter_by(name=group_name).first():
            gsd.delete_groups(session, group_name)
        gsd.add_groups(session, group_name)
        assert session.query(ScenarioGroup).filter_by(name=group_name).first()

    def test_delete_default_scengroup(self):
        group_name = 'group_name'
        session = Session()
        gsd.delete_groups(session, group_name)
        assert session.query(ScenarioGroup).filter_by(name=group_name).first() is None


# Material and base spectra creation testing
class Test_Material_BaseSpec_Create_Delete:
    def test_create_material(self):
        session = Session()
        matname = 'dummy_mat'
        assert get_or_create_material(session, matname)

    def test_build_background_spectrum(self):
        for mat_name, bin_counts in zip(['dummy_mat_1', 'dummy_mat_2'], [4093, 4621]):
            session = Session()
            baseSpectraFilepath = 'dummy_path.n42'
            realtime = 2887.0
            livetime = 2879.0
            counts_arr = np.array([bin_counts] * 1024)
            counts = [str(a) for a in counts_arr[:-1]] + [str(counts_arr[-1])]
            counts = ', '.join(counts)
            assert BackgroundSpectrum(material=get_or_create_material(session, mat_name),
                                      filename=baseSpectraFilepath,
                                      realtime=realtime, livetime=livetime, baseCounts=counts)

    def test_build_base_spectrum(self):
        session = Session()
        for mat_name, bin_counts in zip(['dummy_mat_1', 'dummy_mat_2'], [4093, 4621]):
            baseSpectraFilepath = 'dummy_path.n42'
            realtime = 2887.0
            livetime = 2879.0
            rase_sensitivity = 12799.1
            flux_sensitivity = 59.2
            counts_arr = np.array([bin_counts] * 1024)
            counts = [str(a) for a in counts_arr[:-1]] + [str(counts_arr[-1])]
            counts = ', '.join(counts)
            assert BaseSpectrum(material=get_or_create_material(session, mat_name),
                                filename=baseSpectraFilepath,
                                realtime=realtime, livetime=livetime,
                                rase_sensitivity=rase_sensitivity, flux_sensitivity=flux_sensitivity,
                                baseCounts=counts)


# Scenario creation testing
class Test_Scen_Create_Delete:
    def test_create_scen(self):

        hoc = HelpObjectCreation()
        session = Session()

        acq_times, replications, fd_mode, fd_mode_back, mat_names, back_names, doses, doses_back = hoc.get_default_scen_pars()
        scenMaterials, bcgkScenMaterials = hoc.create_base_materials(fd_mode, fd_mode_back, mat_names, back_names, doses, doses_back)

        for acqTime, replication, baseSpectrum, backSpectrum in zip(acq_times, replications, scenMaterials, bcgkScenMaterials):
            scen_hash = Scenario.scenario_hash(float(acqTime), baseSpectrum, backSpectrum, [])
            scen_exists = session.query(Scenario).filter_by(id=scen_hash).first()
            if scen_exists:
                root_folder = '.'
                delete_scenario([scen_hash], root_folder)
                assert session.query(Scenario).filter_by(id=scen_hash).first() is None
            assert Scenario(float(acqTime), replication, baseSpectrum, backSpectrum, [], hoc.get_scengroups(session))
        assert len(session.query(Scenario).all()) == 2

    def test_scen_delete(self):
        root_folder = '.'
        session = Session()
        scens = session.query(Scenario).all()
        assert len(scens) == 2
        scen_ids = [scen.id for scen in scens]
        delete_scenario(scen_ids, root_folder)
        assert session.query(Scenario).first() is None


# Results Calculation testing
class Test_Workflow:

    # qtbot is necessary as an argument or errors will occur with trying to create a RASE widget
    def test_spec_gen(self, qtbot):
        hoc = HelpObjectCreation()
        w = Rase([])
        hoc.create_default_workflow()
        det_names, scen_ids = hoc.get_default_workflow()

        assert det_names
        assert scen_ids

        spec_status = w.genSpectra(scen_ids, det_names, dispProg=False)
        assert spec_status

    # Can we run the replay tools and get results?
    def test_run_replay(self, qtbot):
        """Dependent on test_spec_gen running"""
        hoc = HelpObjectCreation()
        w = Rase([])
        session = Session()
        det_names, scen_ids = hoc.get_default_workflow()
        replay = session.query(Replay).filter_by(name=hoc.get_default_replay_name()).first()

        assert det_names
        assert replay
        assert scen_ids

        replay_status = w.runReplay(scen_ids, det_names, dispProg=False)
        assert replay_status

    def test_results_calc(self, qtbot):
        """Dependent on test_spec_gen and test_run_replay running"""
        hoc = HelpObjectCreation()
        w = Rase([])

        det_names, scen_ids = hoc.get_default_workflow()

        assert det_names
        assert scen_ids

        w.calculateScenarioStats(1, scen_ids, det_names)
        assert len(w.scenario_stats_df) == 2
        assert w.scenario_stats_df['PID'][0] == 1.0
        assert w.scenario_stats_df['PID'][1] == 0.0


# Sampling testing
class Test_Sampling:
    def test_sampling_algos(self):
        from src.sampling_algos import generate_sample_counts_rejection as s_rejection
        from src.sampling_algos import generate_sample_counts_inversion as s_inversion
        from src.sampling_algos import generate_sample_counts_poisson as s_poisson

        class Scenario:
            pass
        class Detector:
            pass

        s = Scenario()
        d = Detector()

        s.acq_time = 120
        d.chan_count = 1024
        seed = 1
        counts = np.array([4093] * d.chan_count)
        dose = .13
        sensitivity = 17377
        c_d_s = [(counts, dose, sensitivity)]

        sample_counts_r = s_rejection(s, d, c_d_s, seed)
        sample_counts_i = s_inversion(s, d, c_d_s, seed)
        sample_counts_p = s_poisson(s, d, c_d_s, seed)
        rip = [sample_counts_r, sample_counts_i, sample_counts_p]
        sum_rip = [sum(r) for r in rip]
        min_sqrt_rip = min([np.sqrt(sc) for sc in sum_rip])

        for sc in rip:
            assert len(sc) == d.chan_count
        assert max(sum_rip) - min(sum_rip) < min_sqrt_rip

