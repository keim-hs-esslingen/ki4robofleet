#!/usr/bin/env python3

# =============================================================================
# Created at Hochschule Esslingen - University of Applied Sciences
# Department: Anwendungszentrum KEIM
# Contact: emanuel.reichsoellner@hs-esslingen.de
# Date: February 2021
# License: MIT License
# =============================================================================
# This Script creates a User Interface to simple generate Scenarios for
# autonomous driving vehicles. The Pickup POIs and Target POIs can be
# either specific POIs (e.g. school, restaurant) or a whole POI Group (e.g. sport).
# The algorithm picks random POIs from the selected POIs or Groups.
# Also the option RoundTrip can be set with a certain StayTime.
# For Details concering usage please read ./README/ScenarioBuilder.pdf
# =============================================================================

import sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import lxml.etree as ET
from PoiModules.PoiTypes import PoiTypeList
from PoiModules.RequestListGenerator import Scenario, Request, RequestListGenerator
from PIL import ImageColor, Image, ImageDraw, ImageFont
import random
import os
import webbrowser


class ScenarioSetting:
    def __init__(
        self,
        pickupPoiGroup,
        pickupAnySubGroup,
        pickupPoiSubGroup,
        targetPoiGroup,
        targetAnySubGroup,
        targetPoiSubGroup,
        numberOfRequests,
        roundTrip,
        stayTime,
        normalDistributed,
        standardDeviation,
    ):
        self.pickupPoiGroup = pickupPoiGroup
        self.pickupAnySubGroup = pickupAnySubGroup
        self.pickupPoiSubGroup = pickupPoiSubGroup
        self.targetPoiGroup = targetPoiGroup
        self.targetAnySubGroup = targetAnySubGroup
        self.targetPoiSubGroup = targetPoiSubGroup
        self.numberOfRequests = numberOfRequests
        self.roundTrip = roundTrip
        self.stayTime = stayTime
        self.normalDistributed = normalDistributed
        self.standardDeviation = standardDeviation


class WidgetRow(QWidget):
    def __init__(self, poiGroup, scenarioSetting=None, parent=None):
        super(WidgetRow, self).__init__(parent)
        customRow = QHBoxLayout()

        self.poiGroup = poiGroup
        self.row = customRow

        self.label1 = QLabel("Pickup:")
        self.label1.setFixedWidth(50)
        self.label1.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.row.addWidget(self.label1)

        self.pickupPoiGroup = QComboBox(self)
        self.pickupPoiGroup.addItems(sorted(poiGroup.keys()))
        if scenarioSetting:
            self.pickupPoiGroup.setCurrentText(scenarioSetting.pickupPoiGroup)
        self.pickupPoiGroup.setFixedWidth(150)
        self.pickupPoiGroup.currentIndexChanged.connect(self.fromIndexChanged)
        self.row.addWidget(self.pickupPoiGroup)

        self.pickupAnySubGroup = QCheckBox("Any")
        self.pickupAnySubGroup.setFixedWidth(50)
        self.pickupAnySubGroup.setChecked(False)
        if scenarioSetting:
            if scenarioSetting.pickupAnySubGroup == "True":
                self.pickupAnySubGroup.setChecked(True)
        self.pickupAnySubGroup.stateChanged.connect(self.fromAnyStateChanged)
        self.row.addWidget(self.pickupAnySubGroup)

        self.pickupPoiSubGroup = QComboBox(self)
        self.pickupPoiSubGroup.addItems(
            sorted(poiGroup[self.pickupPoiGroup.currentText()])
        )
        if scenarioSetting:
            self.pickupPoiSubGroup.setCurrentText(scenarioSetting.pickupPoiSubGroup)
        self.pickupPoiSubGroup.setFixedWidth(150)
        self.row.addWidget(self.pickupPoiSubGroup)

        self.label2 = QLabel("Target:")
        self.label2.setFixedWidth(80)
        self.label2.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.row.addWidget(self.label2)

        self.targetPoiGroup = QComboBox(self)
        self.targetPoiGroup.addItems(sorted(poiGroup.keys()))
        if scenarioSetting:
            self.targetPoiGroup.setCurrentText(scenarioSetting.targetPoiGroup)
        self.targetPoiGroup.setFixedWidth(150)
        self.targetPoiGroup.currentIndexChanged.connect(self.toIndexChanged)
        self.row.addWidget(self.targetPoiGroup)

        self.targetAnySubGroup = QCheckBox("Any")
        self.targetAnySubGroup.setFixedWidth(50)
        self.targetAnySubGroup.setChecked(False)
        if scenarioSetting:
            if scenarioSetting.targetAnySubGroup == "True":
                self.targetAnySubGroup.setChecked(True)
        self.targetAnySubGroup.stateChanged.connect(self.toAnyStateChanged)
        self.row.addWidget(self.targetAnySubGroup)

        self.targetPoiSubGroup = QComboBox(self)
        self.targetPoiSubGroup.addItems(
            sorted(poiGroup[self.targetPoiGroup.currentText()])
        )
        if scenarioSetting:
            self.targetPoiSubGroup.setCurrentText(scenarioSetting.targetPoiSubGroup)
        self.targetPoiSubGroup.setFixedWidth(150)
        self.row.addWidget(self.targetPoiSubGroup)

        self.label3 = QLabel("Number of Requests:")
        self.label3.setFixedWidth(140)
        self.label3.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.row.addWidget(self.label3)

        inputValidator = QIntValidator()
        inputValidator.setRange(0, 9999)

        self.numberOfRequests = QLineEdit("10")
        self.numberOfRequests.setFixedWidth(20)
        self.numberOfRequests.setValidator(inputValidator)
        if scenarioSetting:
            self.numberOfRequests.setText(scenarioSetting.numberOfRequests)
        self.row.addWidget(self.numberOfRequests)

        self.roundTrip = QCheckBox("RoundTrip")
        self.roundTrip.setFixedWidth(80)
        self.roundTrip.setChecked(True)
        if scenarioSetting:
            if scenarioSetting.roundTrip == "False":
                self.roundTrip.setChecked(False)
        self.roundTrip.stateChanged.connect(self.roundTripStateChanged)
        self.row.addWidget(self.roundTrip)

        self.label4 = QLabel("stayTime [s]:")
        self.label4.setFixedWidth(85)
        self.label4.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.row.addWidget(self.label4)

        self.stayTime = QLineEdit("1800")
        self.stayTime.setFixedWidth(40)
        if scenarioSetting:
            self.stayTime.setText(scenarioSetting.stayTime)
        self.stayTime.setValidator(inputValidator)
        self.row.addWidget(self.stayTime)

        self.normalDistributed = QCheckBox("normal distributed")
        self.normalDistributed.setFixedWidth(140)
        self.normalDistributed.setChecked(True)
        if scenarioSetting:
            if scenarioSetting.normalDistributed == "False":
                self.normalDistributed.setChecked(False)
        self.normalDistributed.stateChanged.connect(self.normalDistributedStateChanged)
        self.row.addWidget(self.normalDistributed)

        self.label5 = QLabel("standardDeviation [s]:")
        self.label5.setFixedWidth(140)
        self.label5.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.row.addWidget(self.label5)

        self.standardDeviation = QLineEdit("600")
        self.standardDeviation.setFixedWidth(40)
        if scenarioSetting:
            self.standardDeviation.setText(scenarioSetting.standardDeviation)
        self.standardDeviation.setValidator(inputValidator)
        self.row.addWidget(self.standardDeviation)

        self.setLayout(self.row)

    def fromIndexChanged(self, index):
        self.pickupPoiSubGroup.clear()
        pGroup = self.pickupPoiGroup.currentText()
        if pGroup is not None:
            self.pickupPoiSubGroup.addItems(sorted(self.poiGroup[pGroup]))

    def toIndexChanged(self, index):
        self.targetPoiSubGroup.clear()
        pGroup = self.targetPoiGroup.currentText()
        if pGroup is not None:
            self.targetPoiSubGroup.addItems(sorted(self.poiGroup[pGroup]))

    def fromAnyStateChanged(self, int):
        if self.pickupAnySubGroup.isChecked():
            self.pickupPoiSubGroup.setEnabled(False)
        else:
            self.pickupPoiSubGroup.setEnabled(True)

    def toAnyStateChanged(self, int):
        if self.targetAnySubGroup.isChecked():
            self.targetPoiSubGroup.setEnabled(False)
        else:
            self.targetPoiSubGroup.setEnabled(True)

    def normalDistributedStateChanged(self, int):
        if self.normalDistributed.isChecked():
            self.label5.setEnabled(True)
            self.standardDeviation.setEnabled(True)
        else:
            self.label5.setEnabled(False)
            self.standardDeviation.setEnabled(False)

    def roundTripStateChanged(self, int):
        if self.roundTrip.isChecked():
            self.label4.setEnabled(True)
            self.stayTime.setEnabled(True)
            self.normalDistributed.setEnabled(True)
            if self.normalDistributed.isChecked():
                self.label5.setEnabled(True)
                self.standardDeviation.setEnabled(True)
            else:
                self.label5.setEnabled(False)
                self.standardDeviation.setEnabled(False)
        else:
            self.label4.setEnabled(False)
            self.stayTime.setEnabled(False)
            self.normalDistributed.setEnabled(False)
            self.label5.setEnabled(False)
            self.standardDeviation.setEnabled(False)


class ScenarioBuilderWindow(QWidget):

    bList = []

    def __init__(self):
        super().__init__()
        osmPolyFile, _ = QFileDialog.getOpenFileName(
            None, "select OSM Poly File in your SUMO Model Directory", "..", "(*.xml)"
        )
        self.workingDirectory = os.path.dirname(osmPolyFile)    
        self.requestListGenerator = RequestListGenerator()
        self.poiGroup = PoiTypeList(osmPolyFile).getGroups()

        self.setWindowTitle(
            "Anwendungszentrum KEIM Hochschule Esslingen - KI4ROBOFLEET Scenario Builder v1.1"
        )
        self.setGeometry(100, 100, 1970, 850)
        self.uiInit()
        self.show()

    def uiInit(self):
        self.listWidget = QListWidget(self)
        self.listWidget.setGeometry(60, 55, 1660, 600)
        self.listWidget.setStyleSheet("background-color:rgb(64,64,64);")

        scroll_bar = QScrollBar(self)
        # scroll_bar.setStyleSheet("background : lightgreen;")
        self.listWidget.setVerticalScrollBar(scroll_bar)

        # add first Row:
        self.addRow()

        self.label = QLabel("Total Simulationtime [s]:", self)
        self.label.setFont(QFont("Arial", 15))
        self.label.move(680, 15)
        self.label.setFixedWidth(300)
        self.label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        inputValidator = QIntValidator()
        inputValidator.setRange(0, 999999)
        self.simTime = QLineEdit("3600", self)
        self.simTime.setFont(QFont("Arial", 15))
        self.simTime.move(990, 15)
        self.simTime.setFixedWidth(60)
        self.simTime.setValidator(inputValidator)

        self.buttonLoad = QPushButton("Load Settings", self)
        self.buttonLoad.resize(120, 40)
        self.buttonLoad.move(60, 670)
        self.buttonLoad.clicked.connect(self.loadSettings)

        self.buttonWrite = QPushButton("Save Settings", self)
        self.buttonWrite.resize(120, 40)
        self.buttonWrite.move(190, 670)
        self.buttonWrite.clicked.connect(self.writeSettings)

        self.buttonNewScenario = QPushButton("Add new SubScenario", self)
        self.buttonNewScenario.resize(180, 40)
        self.buttonNewScenario.move(320, 670)
        self.buttonNewScenario.clicked.connect(self.addRow)

        self.buttonCreateList = QPushButton("Create List of Requests", self)
        self.buttonCreateList.resize(180, 40)
        self.buttonCreateList.move(510, 670)
        self.buttonCreateList.clicked.connect(self.createListOfRequests)

        self.buttonCreateList = QPushButton("Help / Manual", self)
        self.buttonCreateList.resize(160, 40)
        self.buttonCreateList.move(840, 670)
        self.buttonCreateList.clicked.connect(self.showManual)

    def loadSettings(self):
        scenarioSettingsFile, _ = QFileDialog.getOpenFileName(
            None, "select Scenario Settings File", ".", "(*.xml)"
        )
        if len(scenarioSettingsFile) > 0:
            print("loading Scenario Settings from ", scenarioSettingsFile)
            self.listWidget.clear()
            settingsTree = ET.parse(scenarioSettingsFile)

            settingsRoot = settingsTree.getroot()

            for setting in settingsRoot.findall("scenario"):
                scenarioSetting = ScenarioSetting(
                    setting.attrib.get("pickupPoiGroup"),
                    setting.attrib.get("pickupAnySubGroup"),
                    setting.attrib.get("pickupPoiSubGroup"),
                    setting.attrib.get("targetPoiGroup"),
                    setting.attrib.get("targetAnySubGroup"),
                    setting.attrib.get("targetPoiSubGroup"),
                    setting.attrib.get("numberOfRequests"),
                    setting.attrib.get("roundTrip"),
                    setting.attrib.get("stayTime"),
                    setting.attrib.get("normalDistributed"),
                    setting.attrib.get("standardDeviation"),
                )
                self.item = QListWidgetItem(self.listWidget)
                self.listWidget.addItem(self.item)
                self.row = WidgetRow(self.poiGroup, scenarioSetting)
                self.item.setSizeHint(self.row.minimumSizeHint())
                self.listWidget.setItemWidget(self.item, self.row)

    def writeSettings(self):
        scenarioSettingsFile, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Scenario Settings", ".", "*.xml"
        )
        if len(scenarioSettingsFile) > 0:
            print("writing Scenario Settings to ", scenarioSettingsFile)
            xml_output = ET.Element("scenariosetting")
            for index in range(self.listWidget.count()):
                item = self.listWidget.item(index)
                widgetRow = self.listWidget.itemWidget(item)
                ET.SubElement(
                    xml_output,
                    "scenario",
                    pickupPoiGroup=widgetRow.pickupPoiGroup.currentText(),
                    pickupAnySubGroup=str(widgetRow.pickupAnySubGroup.isChecked()),
                    pickupPoiSubGroup=widgetRow.pickupPoiSubGroup.currentText(),
                    targetPoiGroup=widgetRow.targetPoiGroup.currentText(),
                    targetAnySubGroup=str(widgetRow.targetAnySubGroup.isChecked()),
                    targetPoiSubGroup=widgetRow.targetPoiSubGroup.currentText(),
                    numberOfRequests=widgetRow.numberOfRequests.text(),
                    roundTrip=str(widgetRow.roundTrip.isChecked()),
                    stayTime=widgetRow.stayTime.text(),
                    normalDistributed=str(widgetRow.normalDistributed.isChecked()),
                    standardDeviation=widgetRow.standardDeviation.text(),
                )

            tree = ET.ElementTree(xml_output)
            tree.write(
                scenarioSettingsFile,
                encoding="UTF-8",
                xml_declaration=True,
                pretty_print=True,
            )

    def addRow(self):
        self.item = QListWidgetItem(self.listWidget)
        self.listWidget.addItem(self.item)
        self.row = WidgetRow(self.poiGroup)
        self.item.setSizeHint(self.row.minimumSizeHint())
        self.listWidget.setItemWidget(self.item, self.row)

    def createListOfRequests(self):
        scenarioList = []

        for index in range(self.listWidget.count()):
            item = self.listWidget.item(index)
            widgetRow = self.listWidget.itemWidget(item)
            scenario = Scenario(
                widgetRow.pickupPoiGroup.currentText(),
                widgetRow.pickupAnySubGroup.isChecked(),
                widgetRow.pickupPoiSubGroup.currentText(),
                widgetRow.targetPoiGroup.currentText(),
                widgetRow.targetAnySubGroup.isChecked(),
                widgetRow.targetPoiSubGroup.currentText(),
                widgetRow.numberOfRequests.text(),
                widgetRow.roundTrip.isChecked(),
                widgetRow.stayTime.text(),
                widgetRow.normalDistributed.isChecked(),
                widgetRow.standardDeviation.text(),
            )
            scenarioList.append(scenario)

        totalSimulationTime = self.simTime.text()
        self.requestListGenerator.writeRequestList(scenarioList, totalSimulationTime, self.workingDirectory)

    def showManual(self):
        cwd = os.getcwd()
        pathToManual = "file://" + cwd + "/README/ScenarioBuilder.pdf"
        print(pathToManual)
        webbrowser.open(pathToManual)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    scenarioBuilderWindow = ScenarioBuilderWindow()
    scenarioBuilderWindow.show()
    sys.exit(app.exec_())
