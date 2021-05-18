#!/usr/bin/env python3

# =============================================================================
# Created at Hochschule Esslingen - University of Applied Sciences
# Department: Anwendungszentrum KEIM
# Contact: emanuel.reichsoellner@hs-esslingen.de
# Date: May 2021
# License: MIT License
# =============================================================================
# This Script creates a user-friendly Interface to set the parameters for the
# KI4RoboFleet SUMO Simulation and starts the Simulation
# =============================================================================

import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QFileDialog,
    QTextEdit,
    QPushButton,
    QLabel,
    QVBoxLayout,
)
import os


class SimulationInputWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("KI4ROBOFLEET Simulation Input UI v0.4")
        self.setGeometry(100, 100, 500, 820)
        self.uiInit()
        self.show()

    def uiInit(self):
        self.sumoConfigFile = ""
        self.requestList = ""
        self.buttonSelectConfigFile = QPushButton("select SUMO Config File", self)
        self.buttonSelectConfigFile.resize(200, 30)
        self.buttonSelectConfigFile.move(160, 30)
        self.buttonSelectConfigFile.clicked.connect(self.chooseConfigFile)

        self.sumoConfigFileLabel = QLabel("No SUMO Config File specified", self)
        self.sumoConfigFileLabel.setStyleSheet(
            "background-color: red; text-align: center;"
        )
        self.sumoConfigFileLabel.setFixedWidth(450)
        self.sumoConfigFileLabel.move(20, 70)

        self.buttonSelectRequestList = QPushButton(
            "select List of Customer Requests", self
        )
        self.buttonSelectRequestList.resize(300, 30)
        self.buttonSelectRequestList.move(100, 110)
        self.buttonSelectRequestList.clicked.connect(self.chooseRequestList)

        self.requestlistLabel = QLabel("No List of Customer Requests specified", self)
        self.requestlistLabel.setStyleSheet(
            "background-color: red; text-align: center;"
        )
        self.requestlistLabel.setFixedWidth(450)
        self.requestlistLabel.move(20, 150)

        self.fixedFleetSizeStrategy = QGroupBox("Fixed Fleet Size Strategies", self)
        self.fixedFleetSizeStrategy.setCheckable(True)
        self.fixedFleetSizeStrategy.move(130, 190)

        vboxFixedFleet = QVBoxLayout(self)
        self.fixedFleetSizeStrategy.setLayout(vboxFixedFleet)

        self.numberOfVehiclesLabel = QLabel(
            "Number of vehicles in the Simulation", self
        )
        vboxFixedFleet.addWidget(self.numberOfVehiclesLabel)
        self.numberOfVehiclesInput = QLineEdit("10,15,20", self)
        self.numberOfVehiclesInput.setFixedWidth(200)

        vboxFixedFleet.addWidget(self.numberOfVehiclesInput)

        self.simpleStrategy = QCheckBox("simple Strategy", self)
        self.simpleStrategy.setChecked(True)
        vboxFixedFleet.addWidget(self.simpleStrategy)

        self.lookAheadStrategy = QGroupBox("look ahead Strategy")
        self.lookAheadStrategy.setCheckable(True)
        vboxFixedFleet.addWidget(self.lookAheadStrategy)

        vboxLookAhead = QVBoxLayout(self)
        self.lookAheadStrategy.setLayout(vboxLookAhead)

        self.lookAheadTimeLabel = QLabel("look ahead time [s]", self)
        vboxLookAhead.addWidget(self.lookAheadTimeLabel)
        self.lookAheadTimeInput = QLineEdit("900", self)
        self.lookAheadTimeInput.setFixedWidth(200)
        vboxLookAhead.addWidget(self.lookAheadTimeInput)

        self.sharingStrategy = QGroupBox("sharing Strategy", self)
        self.sharingStrategy.setCheckable(True)
        self.sharingStrategy.move(130, 420)
        vboxSharing = QVBoxLayout(self)
        self.sharingStrategy.setLayout(vboxSharing)

        self.realisticTimeFactorLabel = QLabel("realistic_time", self)
        vboxSharing.addWidget(self.realisticTimeFactorLabel)
        self.realisticTimeFactorInput = QLineEdit("1.0, 2.0, 3.0, 4.0", self)
        self.realisticTimeFactorInput.setFixedWidth(200)
        vboxSharing.addWidget(self.realisticTimeFactorInput)

        self.latenessFactorLabel = QLabel("lateness factor", self)
        vboxSharing.addWidget(self.latenessFactorLabel)
        self.latenessFactorInput = QLineEdit("1.0, 1.1, 1.2, 1.4, 1.5", self)
        self.latenessFactorInput.setFixedWidth(200)
        vboxSharing.addWidget(self.latenessFactorInput)

        self.simulationTimeLabel = QLabel("Simulation Time [s]", self)
        self.simulationTimeLabel.move(148, 595)

        self.simulationTimeInput = QLineEdit("3600", self)
        self.simulationTimeInput.setFixedWidth(100)
        self.simulationTimeInput.move(270, 590)

        self.cleanEdgeLabel = QLabel("ID of an arbitrary (ideally central) Edge", self)
        self.cleanEdgeLabel.move(25, 645)

        self.cleanEdgeInput = QLineEdit("45085545", self)
        self.cleanEdgeInput.setFixedWidth(100)
        self.cleanEdgeInput.move(270, 640)

        self.startSimulationButton = QPushButton("start Simulation", self)
        self.startSimulationButton.resize(200, 30)
        self.startSimulationButton.move(160, 690)
        self.startSimulationButton.clicked.connect(self.startSimulation)

    def chooseConfigFile(self):
        self.sumoConfigFile, _ = QFileDialog.getOpenFileName(
            None, "select SUMO Config File", ".", "(*.sumocfg)"
        )
        self.sumoConfigFileLabel.setText(self.sumoConfigFile)
        self.sumoConfigFileLabel.setStyleSheet(
            "background-color: green; text-align: center;"
        )

    def chooseRequestList(self):
        self.requestList, _ = QFileDialog.getOpenFileName(
            None, "select List of Customer Requests", ".", "(*.xml)"
        )
        self.requestlistLabel.setText(self.requestList)
        self.requestlistLabel.setStyleSheet(
            "background-color: green; text-align: center;"
        )

    def startSimulation(self):
        additionalParams = ""
        strategies = []
        numberOfVehiclesParam = ""
        lookAheadTimeParam = ""
        realisticTimeFactorParam = ""
        latenessFactorParam = ""

        if self.fixedFleetSizeStrategy.isChecked():
            if len(self.numberOfVehiclesInput.text()) > 0:
                numberOfVehiclesParam = (
                    ' -n "' + self.numberOfVehiclesInput.text() + '"'
                )
            if self.simpleStrategy.isChecked():
                strategies.append("simple")
            if self.lookAheadStrategy.isChecked():
                strategies.append("look_ahead")
                if len(self.lookAheadTimeInput.text()) > 0:
                    lookAheadTimeParam = " -a " + self.lookAheadTimeInput.text()

        if self.sharingStrategy.isChecked():
            strategies.append("shared")
            if len(self.realisticTimeFactorInput.text()) > 0:
                realisticTimeFactorParam = (
                    ' -r "' + self.realisticTimeFactorInput.text() + '"'
                )
            if len(self.latenessFactorInput.text()) > 0:
                latenessFactorParam = ' -l "' + self.latenessFactorInput.text() + '"'

        if len(strategies) > 0:
            additionalParams += (
                ' -s "'
                + ", ".join(strategies)
                + '"'
                + numberOfVehiclesParam
                + lookAheadTimeParam
                + realisticTimeFactorParam
                + latenessFactorParam
            )

        if len(self.requestList) > 0 and len(self.sumoConfigFile) > 0:
            cmd = (
                "python3 ./web_taxi_runner.py -f "
                + self.requestList
                + " -c "
                + self.sumoConfigFile
                + " -t "
                + self.simulationTimeInput.text()
                + " -e "
                + self.cleanEdgeInput.text()
                + additionalParams
            )
            print("executing: ", cmd)
            os.system(cmd)
        else:
            print("Please specify SUMO Config File  AND  List of Customer Requests!")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    simulationInputWindow = SimulationInputWindow()
    simulationInputWindow.show()
    sys.exit(app.exec_())
