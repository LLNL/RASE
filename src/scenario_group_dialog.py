###############################################################################
# Copyright (c) 2018-2021 Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory
#
# Written by J. Chavez, S. Czyz, G. Kosinovsky, V. Mozin, S. Sangiorgio.
# RASE-support@llnl.gov.
#
# LLNL-CODE-819515
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
"""
This module allows user to adjust scenario groups
"""
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QWidget, QDialog, QLineEdit, QVBoxLayout, QCheckBox,QDialogButtonBox, QPushButton, \
                                    QInputDialog, QMessageBox, QLabel
from src.table_def import ScenarioGroup, Session


class GroupSettings(QDialog):
    """Simple Dialog to allow the user to select which groups a scenario is in.
    This information is stored in the scenario_groups table value for each scenario.

    :param parent: the parent dialog
    """
    def __init__(self, parent=None, groups=[], scens=None, del_groups=False):
        QDialog.__init__(self, parent)
        self.groups = groups
        self.scens = scens
        self.del_groups = del_groups
        self.session = Session()

        self.makeLayout()


    def makeLayout(self):
        cols_list = [grp.name for grp in self.session.query(ScenarioGroup)]
        cols_list.insert(0, cols_list.pop(cols_list.index('default_group')))
        cb_list = [QCheckBox(v.replace('&', '&&')) for v in cols_list]

        self.layout = QVBoxLayout()
        self.checklayout = QVBoxLayout()
        self.buttonlayout = QVBoxLayout()

        for cb in cb_list:
            self.checklayout.addWidget(cb)
            if cb.text() in self.groups:
                cb.setChecked(True)
            if cb.text() == 'default_group' and self.del_groups:
                cb.setEnabled(False)

        self.btn_newgroup = QPushButton('Add New Group')
        self.buttonlayout.addWidget(self.btn_newgroup)
        self.btn_newgroup.clicked.connect(self.addCheckbox)
        self.buttonBox = QDialogButtonBox(self)

        if self.del_groups:
            self.btn_deletegroup = QPushButton('Remove Group(s)')
            self.buttonlayout.addWidget(self.btn_deletegroup)
            self.btn_deletegroup.clicked.connect(self.delGroup)
            self.buttonBox.setStandardButtons(QDialogButtonBox.Close)
            self.buttonBox.rejected.connect(self.reject)
        else:
            self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
            self.buttonBox.accepted.connect(self.accept)
            self.buttonBox.rejected.connect(self.reject)
        self.buttonlayout.addWidget(self.buttonBox)

        self.layout.addLayout(self.checklayout)
        self.layout.addLayout(self.buttonlayout)
        if not self.del_groups and self.scens and len(self.scens) > 1:
            self.info = QLabel('NOTE: A group box is checked if\nany one of the selected scenarios\nis in that '
                               'group. Pressing OK will\nadd all selected scenarios to the\nselected groups.')
            self.layout.addWidget(self.info)
        self.setLayout(self.layout)

    def _cb_list(self):
        return [self.checklayout.itemAt(i).widget() for i in range(self.checklayout.count())]

    def addCheckbox(self):
        newgroup, okPressed = QInputDialog.getText(self, "Add New Scenario Group", "Scenario Group name:",
                                               QLineEdit.Normal, "")
        collist = [grp.name for grp in self.session.query(ScenarioGroup)]
        if okPressed and (newgroup != '' and newgroup not in collist):
            self.checklayout.addWidget(QCheckBox(newgroup))
            self.setLayout(self.layout)
            self.add_groups(self.session, newgroup)

    def delGroup(self):
        del_groups = [cb.text() for cb in self._cb_list() if cb.isChecked()]
        if len(del_groups) > 1:
            answer = QMessageBox(QMessageBox.Question, 'Delete Scenario Groups',
                                                       'Are you sure you want to delete these scenario groups? '
                                                       'Scenarios in these groups will not be deleted')
        else:
            answer = QMessageBox(QMessageBox.Question, 'Delete Scenario Group',
                                                       'Are you sure you want to delete this scenario group? '
                                                       'Scenarios in this group will not be deleted')
        answer.addButton(QMessageBox.Yes)
        answer.addButton(QMessageBox.No)
        ans_hold = answer.exec()
        if ans_hold == QMessageBox.Yes:
            for group in del_groups:
                self.delete_groups(self.session, group)
            for cb in self._cb_list():
                if cb.text() in del_groups:
                    self.checklayout.removeWidget(cb)
                    cb.deleteLater()

    @staticmethod
    def delete_groups(session, group):
        group_delete = session.query(ScenarioGroup).filter(ScenarioGroup.name == group)
        group_delete.delete()
        session.commit()

    @staticmethod
    def add_groups(session, group):
        session.add(ScenarioGroup(name=group))
        session.commit()


    @pyqtSlot()
    def accept(self):
        """
        Adds the scenario to the checked groups
        """
        self.n_groups = [cb.text() for cb in self._cb_list() if cb.isChecked()]
        if self.scens:
            for scen in self.scens:
                scen.scenario_groups.clear()
                for groupname in self.n_groups:
                    scen.scenario_groups.append(self.session.query(ScenarioGroup).filter_by(name=groupname).first())
            self.session.commit()
        return QDialog.accept(self)
