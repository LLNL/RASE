import sys
from time import sleep

import pytest
from PySide6.QtCore import Qt, QTimer, QObject, Signal

from src.replay_dialog import ReplayDialog
from src.base_spectra_dialog import BaseSpectraDialog
from src.detector_dialog import DetectorDialog
from src.scenario_dialog import ScenarioDialog
from src.rase import Rase
from src.rase_functions import *
from src.rase_settings import RaseSettings
from src.scenario_group_dialog import GroupSettings as gsd
from sqlalchemy.orm import close_all_sessions
from dynamic.dynamic_table_def import *



@pytest.fixture(scope="class", autouse=True)
def db_and_output_folder():
    """Delete and recreate the database between test classes"""
    settings = RaseSettings()
    close_all_sessions()
    if os.path.isdir(settings.getSampleDirectory()):
        shutil.rmtree(settings.getSampleDirectory())
        print(f'Deleting sample dir at {settings.getSampleDirectory()}')
    if os.path.isfile(settings.getDatabaseFilepath()):
        os.remove(settings.getDatabaseFilepath())
        print(f'Deleting DB at {settings.getDatabaseFilepath()}')
    dataDir = settings.getDataDirectory()
    if not os.path.exists(dataDir):
        os.makedirs(dataDir, exist_ok=True)
    initializeDatabase(settings.getDatabaseFilepath())
    yield Session()
    close_all_sessions()





@pytest.fixture(scope='class')
def base_import_window():
    w = BaseSpectraDialog(Session())
    return w

@pytest.fixture(scope='session')
def main_window():
    w = Rase(None)
    return w


class Helper(QObject):
    finished = Signal()


# GUI testing
class Test_Load_spectra:
    def test_load_dir(self,qtbot, base_import_window ):
        w = base_import_window
        w.show()
        qtbot.addWidget(w)
        w.on_btnBrowse_clicked(False,
                              r"C:\Users\brodsky3\OneDrive - LLNL\Documents\RASE\testout\testout_multisec",
                               secType='Background Spectrum'
                              )
        w.accept()

    def test_detector_dialog(self,qtbot, base_import_window):
        session = Session()
        w = base_import_window

        dd = DetectorDialog(None)
        dd.show()
        qtbot.addWidget(dd)
        dd.txtDetector.setText('test_detector')
        dd.on_btnAddBaseSpectra_clicked(False,w)
        dd.secondaryIsBackgroundRadio.setChecked(True)
        dd.combo_typesecondary.setCurrentIndex(secondary_type['file'])
        dd.combo_basesecondary.setCurrentText('Background')
        qtbot.wait(30)

        replaydialog = ReplayDialog(dd)
        replaydialog.txtName.setText('testreplay')
        replaydialog.txtTemplatePath.setText(
            str(Path(__file__).parent/'../n42Templates/example_multisecondary_template.n42'))
        replaydialog.accept()
        dd.on_btnNewReplay_clicked(False, replaydialog)


        dd.accept()
        assert (dd.detector.replay)
        saved_det = session.query(Detector).filter_by(name='test_detector').one()
        assert len(saved_det.secondary_spectra)==2
        assert saved_det.bckg_spectra[0].livetime >300

        #TODO: test delete spectra

    def test_detector_reopen(self,qtbot,):
        session = Session()

        dd = DetectorDialog(None,'test_detector')
        dd.combo_typesecondary.setCurrentIndex(secondary_type['base_spec'])
        dd.accept()

        dd = DetectorDialog(None, 'test_detector')
        dd.combo_typesecondary.setCurrentIndex(secondary_type['file'])
        dd.accept()

    def test_scenario_creation(self, qtbot, main_window):
        w = ScenarioDialog(main_window)
        w.show()
        # comboSelectMaterial = w.tblMaterial.itemDelegate().createEditor()
        item = w.tblMaterial.item(0, 1)
        assert item is not None
        rect = w.tblMaterial.visualItemRect(item)
        qtbot.mouseClick(w.tblMaterial.viewport(), Qt.LeftButton, pos=rect.center())
        qtbot.mouseDClick(w.tblMaterial.viewport(), Qt.LeftButton, pos=rect.center())
        qtbot.mouseClick(w.tblMaterial.viewport(), Qt.LeftButton, pos=rect.center())
        cell = w.tblMaterial.cellWidget(0,1)
        qtbot.keyClicks(cell, 'Co60')
        qtbot.mouseClick(w.tblMaterial.viewport(), Qt.LeftButton, pos=rect.center())
        w.accept()
        main_window.populateScenarios()
        main_window.populateScenarioGroupCombo()
        testscen = Session.query(DynamicScenario).one_or_none()
    def test_run_generation(self,qtbot, main_window):
        w = main_window
        w.show()
        scenitem = w.tblScenario.item(0, 0)
        scenrect = w.tblScenario.visualItemRect(scenitem)
        detitem = w.tblDetectorReplay.item(0, 0)
        detrect = w.tblDetectorReplay.visualItemRect(detitem)

        qtbot.mouseClick(w.tblDetectorReplay.viewport(), Qt.LeftButton, pos=detrect.center())
        qtbot.mouseClick(w.tblScenario.viewport(), Qt.LeftButton, pos=scenrect.center())
        assert(main_window.btnGenerate.isEnabled())
        main_window.on_btnGenerate_clicked(False)
    #
    # def test_paths_dialog(self,qtbot):
    #     w = DynamicPathsDialog()
    #     w.addPath(name="testpath")
    #     w.displayPath(w.listmodel.index(0), None)
    #     w.enableModification()
    #     w.model.setData(w.model.index(1,0), 100, Qt.EditRole)
    #     w.model.setData(w.model.index(1, 3), 20, Qt.EditRole)
    #     w.savePathChanges()
    #
    # def test_scenario_creation(self,qtbot, main_window_dy):
    #     w = DynamicScenarioDialog(main_window_dy)
    #     w.show()
    #     # comboSelectMaterial = w.tblMaterial.itemDelegate().createEditor()
    #     item = w.tblMaterial.item(0, 1)
    #     assert item is not None
    #     rect = w.tblMaterial.visualItemRect(item)
    #     qtbot.mouseClick(w.tblMaterial.viewport(), Qt.LeftButton, pos=rect.center())
    #     qtbot.mouseDClick(w.tblMaterial.viewport(), Qt.LeftButton, pos=rect.center())
    #     qtbot.mouseClick(w.tblMaterial.viewport(), Qt.LeftButton, pos=rect.center())
    #     cell = w.tblMaterial.cellWidget(0,1)
    #     qtbot.keyClicks(cell, 'Cs137')
    #     qtbot.mouseClick(w.tblMaterial.viewport(), Qt.LeftButton, pos=rect.center())
    #     qtbot.keyClicks(w.txtSampleHz,'10')
    #     w.accept()
    #     main_window_dy.populateScenarios()
    #     main_window_dy.populateScenarioGroupCombo()
    #     testscen = Session.query(DynamicScenario).one_or_none()
    #
    # def test_run_generation(self,qtbot, main_window_dy):
    #     w = main_window_dy
    #     w.show()
    #     scenitem = w.tblScenario.item(0, 0)
    #     scenrect = w.tblScenario.visualItemRect(scenitem)
    #     detitem = w.tblDetectorReplay.item(0, 0)
    #     detrect = w.tblDetectorReplay.visualItemRect(detitem)
    #
    #     qtbot.mouseClick(w.tblDetectorReplay.viewport(), Qt.LeftButton, pos=detrect.center())
    #     qtbot.mouseClick(w.tblScenario.viewport(), Qt.LeftButton, pos=scenrect.center())
    #     assert(main_window_dy.btnGenerate_dy.isEnabled())
    #     main_window_dy.on_btnGenerate_dy_clicked(False)

