#!/usr/bin/env python3

# =============================================================================
# Created at Hochschule Esslingen - University of Applied Sciences
# Department: Anwendungszentrum KEIM
# Contact: emanuel.reichsoellner@hs-esslingen.de
# Date: April 2021
# License: MIT License
# =============================================================================
# This Script is the Entrypoint for the KI4RoboFleet SUMO Simulation to analyze
# customized Scenarios for cities with autonomous driving cars
# =============================================================================

import sys
import os

sys.path.append("SumoOsmPoiTools")

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from SumoOsmPoiTools.SumoOsmPoiTools import PoiToolMainWindow
from SumoOsmPoiTools.ScenarioBuilder import ScenarioBuilderWindow
from SimulationToolsUI.SimulationInputUI import SimulationInputWindow
from SimulationToolsUI.ResultsViewerUI import ResultsViewerWindow


class KI4RoboFleetUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("KI4ROBOFLEET User Interface v0.1")
        self.setGeometry(100, 100, 500, 370)
        self.uiInit()
        self.show()

    def uiInit(self):

        self.buttonCreateList = QPushButton("SUMO Model Tools", self)
        self.buttonCreateList.resize(300, 40)
        self.buttonCreateList.move(100, 50)
        self.buttonCreateList.clicked.connect(self.osmPoiTools)

        self.buttonCreateList = QPushButton("Scenario Builder", self)
        self.buttonCreateList.resize(300, 40)
        self.buttonCreateList.move(100, 120)
        self.buttonCreateList.clicked.connect(self.scenarioBuilder)

        self.buttonCreateList = QPushButton("Simulation Settings", self)
        self.buttonCreateList.resize(300, 40)
        self.buttonCreateList.move(100, 190)
        self.buttonCreateList.clicked.connect(self.simulation)

        self.buttonCreateList = QPushButton("Results Viewer", self)
        self.buttonCreateList.resize(300, 40)
        self.buttonCreateList.move(100, 260)
        self.buttonCreateList.clicked.connect(self.results)

    def osmPoiTools(self):
        print("SUMO Model Tools")
        if "SumoOsmPoiTools" not in os.getcwd():
            os.chdir("./SumoOsmPoiTools")
        self.poiToolMainWindow = PoiToolMainWindow()
        self.poiToolMainWindow.show()

    def scenarioBuilder(self):
        print("Scenario Builder")
        if "SumoOsmPoiTools" not in os.getcwd():
            os.chdir("./SumoOsmPoiTools")
        self.scenarioBuilder = ScenarioBuilderWindow()
        self.scenarioBuilder.show()

    def simulation(self):
        print("Simulation Settings")
        if "SumoOsmPoiTools" in os.getcwd():
            os.chdir("../")
        self.simulationInputWindow = SimulationInputWindow()
        self.simulationInputWindow.show()

    def results(self):
        print("Results Viewer")
        self.resultsViewerWindow = ResultsViewerWindow()
        self.resultsViewerWindow.show()


if __name__ == "__main__":
    print(
        " __  __      ______      __ __       ____                __                   ___   ___                       __      "
    )
    print(
        "/\\ \\/\\ \\    /\\__  _\\    /\\ \\\\ \\     /\\  _`\\             /\\ \\                /'___\\ /\\_ \\                     /\\ \\__   "
    )
    print(
        "\\ \\ \\/'/'   \\/_/\\ \\/    \\ \\ \\\\ \\    \\ \\ \\L\\ \\     ___   \\ \\ \\____    ___   /\\ \\__/ \\//\\ \\       __      __   \\ \\ ,_\\  "
    )
    print(
        " \\ \\ , <       \\ \\ \\     \\ \\ \\\\ \\_   \\ \\ ,  /    / __`\\  \\ \\ '__`\\  / __`\\ \\ \\ ,__\\  \\ \\ \\    /'__`\\  /'__`\\  \\ \\ \\/  "
    )
    print(
        "  \\ \\ \\\\`\\      \\_\\ \\__   \\ \\__ ,__\\  \\ \\ \\\\ \\  /\\ \\L\\ \\  \\ \\ \\L\\ \\/\\ \\L\\ \\ \\ \\ \\_/   \\_\\ \\_ /\\  __/ /\\  __/   \\ \\ \\_ "
    )
    print(
        "   \\ \\_\\ \\_\\    /\\_____\\   \\/_/\\_\\_/   \\ \\_\\ \\_\\\\ \\____/   \\ \\_,__/\\ \\____/  \\ \\_\\    /\\____\\\\ \\____\\\\ \\____\\   \\ \\__\\"
    )
    print(
        "    \\/_/\\/_/    \\/_____/      \\/_/      \\/_/\\/ / \\/___/     \\/___/  \\/___/    \\/_/    \\/____/ \\/____/ \\/____/    \\/__/"
    )

    app = QApplication(sys.argv)
    kI4RoboFleetUI = KI4RoboFleetUI()
    kI4RoboFleetUI.show()
    sys.exit(app.exec_())
