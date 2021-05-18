#!/usr/bin/env python3

# =============================================================================
# Created at Hochschule Esslingen - University of Applied Sciences
# Department: Anwendungszentrum KEIM
# Contact: emanuel.reichsoellner@hs-esslingen.de
# Date: May 2021
# License: MIT License
# =============================================================================
# This Script creates a User Interface to read the Simulationresults from the
# session_{timestamp}.json Files and to display them in a well-arranged way.
# As a nice feature the color theme of the chart can be changed :)
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
from PyQt5.QtChart import (
    QChart,
    QChartView,
    QBarSet,
    QPercentBarSeries,
    QBarCategoryAxis,
    QValueAxis,
    QStackedBarSeries,
)
from PyQt5.QtGui import QPainter, QIcon, QPixmap
from PyQt5.QtCore import Qt


import os
import json

from PyQt5.QtWidgets import *
from PyQt5.QtChart import *


class Result:
    def __init__(
        self,
        emptyKm,
        passengerKm,
        fullfilledRequests,
        roboTaxis,
        strategy,
        pRidingTime,
        pWaitingTime,
        lookAheadTime,
        latenessFactor,
        realisticTime,
    ):
        self.emptyKm = emptyKm
        self.passengerKm = passengerKm
        self.fullfilledRequests = fullfilledRequests
        self.roboTaxis = roboTaxis
        self.strategy = strategy
        self.pRidingTime = pRidingTime
        self.pWaitingTime = pWaitingTime
        self.lookAheadTime = lookAheadTime
        self.latenessFactor = latenessFactor
        self.realisticTime = realisticTime


class ResultManager:
    def __init__(self):
        self.resultList = []
        self.resultIndex = 0
        self.numberOfResults = 0

    def addResult(self, result):
        self.resultList.append(result)
        self.numberOfResults += 1

    def getFirstResult(self):
        if self.numberOfResults > 0:
            return self.resultList[0]
        else:
            return None

    def getNextResult(self):
        if self.numberOfResults > 0:
            if self.resultIndex < self.numberOfResults - 1:
                self.resultIndex += 1
            else:
                self.resultIndex = 0
            return self.resultList[self.resultIndex]
        else:
            return None

    def getPreviousResult(self):
        if self.numberOfResults > 0:
            if self.resultIndex > 0:
                self.resultIndex -= 1
            else:
                self.resultIndex = self.numberOfResults - 1
            return self.resultList[self.resultIndex]
        else:
            return None


class ResultsViewerWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("KI4ROBOFLEET Results Viewer v0.3")
        self.setGeometry(100, 100, 1800, 1200)
        self.uiInit()
        self.show()

    def uiInit(self):

        self.resultManager = ResultManager()

        self.gridLayout = QGridLayout(self)
        ctrlElements = QVBoxLayout()

        self.sessionFileLabel = QLabel("List of Session Files")
        self.sessionFileLabel.move(95, 20)
        ctrlElements.addWidget(self.sessionFileLabel)

        self.sessionFileList = QListWidget()
        self.sessionFileList.move(50, 40)
        ctrlElements.addWidget(self.sessionFileList)

        ctrlElements1 = QVBoxLayout()

        buttonReadFile = QPushButton("Read File - Overview", self)
        buttonReadFile.clicked.connect(self.readFile)
        ctrlElements1.addWidget(buttonReadFile)
        nextRunResults = QPushButton("view Details: next Run", self)
        nextRunResults.clicked.connect(self.nextResult)
        ctrlElements1.addWidget(nextRunResults)
        previousRunResults = QPushButton("view Details: previous Run", self)
        previousRunResults.clicked.connect(self.previousResult)
        ctrlElements1.addWidget(previousRunResults)

        self.styleComboBox = QComboBox(self)
        self.styleComboBox.addItem("Style: Bright Theme")
        self.styleComboBox.addItem("Style: Blueprint Theme")
        self.styleComboBox.addItem("Style: Dark Theme")
        self.styleComboBox.addItem("Style: Sandy Theme")
        self.styleComboBox.addItem("Style: Blue Theme")
        self.styleComboBox.addItem("Style: Contrast Theme")
        self.styleComboBox.addItem("Style: Icy Theme")

        self.styleComboBox.setCurrentText("Style: Dark Theme")

        self.styleComboBox.currentIndexChanged.connect(self.changeStyle)
        ctrlElements1.addWidget(self.styleComboBox)

        # self.gridLayout.addLayout(ctrlElements, 0, 0, 1, 3)
        self.gridLayout.addLayout(ctrlElements, 0, 0)
        self.gridLayout.addLayout(ctrlElements1, 1, 0)

        self.chart1 = QChart()
        self.chartView1 = QChartView(self.chart1)
        self.chart1.setTheme(QChart.ChartThemeDark)
        self.gridLayout.addWidget(self.chartView1, 0, 1)

        self.chart2 = QChart()
        self.chartView2 = QChartView(self.chart2)
        self.chart2.setTheme(QChart.ChartThemeDark)
        self.gridLayout.addWidget(self.chartView2, 0, 2)

        textResultsLeft = QVBoxLayout()

        textResultsRight = QVBoxLayout()

        self.leafIcon = QLabel("")
        self.leafIcon.setFixedSize(60, 60)

        self.coinIcon = QLabel("")
        self.coinIcon.setFixedSize(60, 60)

        self.simulationRunLabel = QLabel("")
        self.simulationRunLabel.setFont(QFont("Arial", 18))

        self.numberOfRoboTaxis = QLabel("")
        self.numberOfRoboTaxis.setFont(QFont("Arial", 18))

        self.numberOfRequests = QLabel("")
        self.numberOfRequests.setFont(QFont("Arial", 18))

        self.simulationStrategyLabel = QLabel("")
        self.simulationStrategyLabel.setFont(QFont("Arial", 18))

        self.totalDistance = QLabel("")
        self.totalDistance.setFont(QFont("Arial", 18))

        self.distanceWithPassenger = QLabel("")
        self.distanceWithPassenger.setFont(QFont("Arial", 18))

        self.powerConsumption = QLabel("")
        self.powerConsumption.setFont(QFont("Arial", 18))

        self.energyCost = QLabel("")
        self.energyCost.setFont(QFont("Arial", 18))

        self.fleetCost = QLabel("")
        self.fleetCost.setFont(QFont("Arial", 18))

        self.totalCost = QLabel("")
        self.totalCost.setFont(QFont("Arial", 18))

        self.costPerPassengerKm = QLabel("")
        self.costPerPassengerKm.setFont(QFont("Arial", 18))

        self.emissions = QLabel("")
        self.emissions.setFont(QFont("Arial", 18))

        self.customerWaitingTime = QLabel("")
        self.customerWaitingTime.setFont(QFont("Arial", 18))

        textResultsLeft.setAlignment(Qt.AlignCenter)
        textResultsLeft.addWidget(self.simulationRunLabel)
        textResultsLeft.addWidget(self.numberOfRoboTaxis)
        textResultsLeft.addWidget(self.numberOfRequests)
        textResultsLeft.addWidget(self.simulationStrategyLabel)
        textResultsLeft.addWidget(self.leafIcon)
        textResultsLeft.addWidget(self.powerConsumption)
        textResultsLeft.addWidget(self.emissions)

        textResultsRight.setAlignment(Qt.AlignCenter)
        textResultsRight.addWidget(self.totalDistance)
        textResultsRight.addWidget(self.distanceWithPassenger)
        textResultsRight.addWidget(self.customerWaitingTime)
        textResultsRight.addWidget(self.coinIcon)
        textResultsRight.addWidget(self.energyCost)
        textResultsRight.addWidget(self.fleetCost)
        textResultsRight.addWidget(self.totalCost)
        textResultsRight.addWidget(self.costPerPassengerKm)

        self.gridLayout.addLayout(textResultsLeft, 1, 1)
        self.gridLayout.addLayout(textResultsRight, 1, 2)

        self.gridLayout.setColumnStretch(0, 1)
        self.gridLayout.setColumnStretch(1, 2)
        self.gridLayout.setColumnStretch(2, 2)
        self.gridLayout.setRowStretch(0, 1)
        self.gridLayout.setRowStretch(1, 1)

        for r, d, f in os.walk("./"):
            for file in f:
                if (".json" in file) and ("session" in file):
                    self.sessionFileList.addItem(file)

    def createChart(self, results):

        self.gridLayout.removeWidget(self.chartView1)
        self.gridLayout.removeWidget(self.chartView2)

        self.chart1 = QChart()
        self.chartView1 = QChartView(self.chart1)
        self.gridLayout.addWidget(self.chartView1, 0, 1)

        self.chart2 = QChart()
        self.chartView2 = QChartView(self.chart2)
        self.gridLayout.addWidget(self.chartView2, 0, 2)

        set1 = []
        set1.append(QBarSet("empty"))
        set1.append(QBarSet("with passenger"))

        set2 = []
        set2.append(QBarSet("RidingTime"))
        set2.append(QBarSet("WaitingTime"))

        numberOfRoboTaxis = []

        maxKm = 0
        maxTime = 0

        for result in results:
            numberOfRoboTaxis.append(str(result.roboTaxis))

            emptyKm = float(result.emptyKm / result.fullfilledRequests)
            passengerKm = float(result.passengerKm / result.fullfilledRequests)
            if emptyKm > maxKm:
                maxKm = emptyKm
            if passengerKm > maxKm:
                maxKm = passengerKm

            set1[0].append(emptyKm)
            set1[1].append(passengerKm)

            pRidingTime = int(result.pRidingTime / result.fullfilledRequests) // 60
            pWaitingTime = int(result.pWaitingTime / result.fullfilledRequests) // 60
            if pRidingTime > maxTime:
                maxTime = pRidingTime
            if pWaitingTime > maxTime:
                maxTime = pWaitingTime

            set2[0].append(pRidingTime)
            set2[1].append(pWaitingTime)

        series1 = QBarSeries()
        series2 = QBarSeries()

        for i in range(len(set1)):
            series1.append(set1[i])

        for i in range(len(set2)):
            series2.append(set2[i])

        axisX1 = QBarCategoryAxis()
        axisX1.setTitleText("Number of RoboTaxis")
        axisY1 = QValueAxis()
        axisY1.setTitleText("Distance [km]")
        axisY1.setRange(0, maxKm)
        axisX1.append(numberOfRoboTaxis)

        axisX2 = QBarCategoryAxis()
        axisX2.setTitleText("Number of RoboTaxis")
        axisY2 = QValueAxis()
        axisY2.setTitleText("Time [min]")
        axisY2.setRange(0, maxTime)
        axisX2.append(numberOfRoboTaxis)

        self.chart1.addSeries(series1)
        self.chart1.setTitle("Driving Distance per Passenger")
        self.chart1.setAnimationOptions(QChart.SeriesAnimations)
        self.chart1.addAxis(axisX1, Qt.AlignBottom)
        self.chart1.addAxis(axisY1, Qt.AlignLeft)
        self.chartView1.chart().legend().setAlignment(Qt.AlignBottom)

        self.chart2.addSeries(series2)
        self.chart2.setTitle("Time per Passenger")
        self.chart2.setAnimationOptions(QChart.SeriesAnimations)
        self.chart2.addAxis(axisX2, Qt.AlignBottom)
        self.chart2.addAxis(axisY2, Qt.AlignLeft)
        self.chartView2.chart().legend().setAlignment(Qt.AlignBottom)

        self.changeStyle()

    def changeStyle(self):
        if self.styleComboBox.currentIndex() == 0:
            self.chart1.setTheme(QChart.ChartThemeLight)
            self.chart2.setTheme(QChart.ChartThemeLight)
        if self.styleComboBox.currentIndex() == 1:
            self.chart1.setTheme(QChart.ChartThemeBlueCerulean)
            self.chart2.setTheme(QChart.ChartThemeBlueCerulean)
        if self.styleComboBox.currentIndex() == 2:
            self.chart1.setTheme(QChart.ChartThemeDark)
            self.chart2.setTheme(QChart.ChartThemeDark)
        if self.styleComboBox.currentIndex() == 3:
            self.chart1.setTheme(QChart.ChartThemeBrownSand)
            self.chart2.setTheme(QChart.ChartThemeBrownSand)
        if self.styleComboBox.currentIndex() == 4:
            self.chart1.setTheme(QChart.ChartThemeBlueNcs)
            self.chart2.setTheme(QChart.ChartThemeBlueNcs)
        if self.styleComboBox.currentIndex() == 5:
            self.chart1.setTheme(QChart.ChartThemeHighContrast)
            self.chart2.setTheme(QChart.ChartThemeHighContrast)
        if self.styleComboBox.currentIndex() == 6:
            self.chart1.setTheme(QChart.ChartThemeBlueIcy)
            self.chart2.setTheme(QChart.ChartThemeBlueIcy)

        self.chart1.setAnimationOptions(QChart.NoAnimation)
        self.chart1.setAnimationOptions(QChart.GridAxisAnimations)
        # self.chart1.setAnimationOptions(QChart.SeriesAnimations)

        self.chart2.setAnimationOptions(QChart.NoAnimation)
        self.chart2.setAnimationOptions(QChart.GridAxisAnimations)

    def readFile(self):
        try:
            selectedFile = self.sessionFileList.currentItem().text()
            print("View Results for", selectedFile)
            try:
                self.resultManager = ResultManager()

                # find path to file
                pathToFile = ""
                for r, d, f in os.walk("./"):
                    for file in f:
                        if selectedFile in file:
                            pathToFile = r + "/" + file

                with open(pathToFile) as sessionFile:
                    data = json.load(sessionFile)
                    # sort Results by num_of_vehicles
                    sortedResults = sorted(
                        data["results"],
                        key=lambda x: x["num_of_vehicles"],
                        reverse=False,
                    )

                    for result in sortedResults:

                        lookAheadTime = ""
                        if "look_ahead_time" in result:
                            lookAheadTime = str(result["look_ahead_time"])

                        latenessFactor = ""
                        if "lateness_factor" in result:
                            latenessFactor = str(result["lateness_factor"])

                        realisticTime = ""
                        if "realistic_time" in result:
                            realisticTime = str(result["realistic_time"])

                        self.resultManager.addResult(
                            Result(
                                float(result["d_empty (km)"]),
                                float(result["d_pass (km)"]),
                                int(result["fullfilled requests"]),
                                int(result["num_of_vehicles"]),
                                result["strategy"],
                                int(result["t_drive (sec)"]),
                                int(result["t_wait (sec)"]),
                                lookAheadTime,
                                latenessFactor,
                                realisticTime,
                            )
                        )

                self.clearFields()
                self.createChart(self.resultManager.resultList)

                self.resultManager.resultIndex = self.resultManager.numberOfResults - 1

            except:
                print("Problems by creating Graph")

        except:
            print("Please select a Session File!")

    def nextResult(self):
        self.viewResults(self.resultManager.getNextResult())

    def previousResult(self):
        self.viewResults(self.resultManager.getPreviousResult())

    def clearFields(self):
        self.simulationRunLabel.setText("")
        self.numberOfRoboTaxis.setText("")
        self.simulationStrategyLabel.setText("")
        self.totalDistance.setText("")
        self.powerConsumption.setText("")
        self.emissions.setText("")
        self.energyCost.setText("")
        self.customerWaitingTime.setText("")
        self.leafIcon.clear()
        self.coinIcon.clear()
        self.numberOfRequests.setText("")
        self.distanceWithPassenger.setText("")
        self.fleetCost.setText("")
        self.totalCost.setText("")
        self.costPerPassengerKm.setText("")

    def viewResults(self, result):

        self.leafIcon.setPixmap(
            QPixmap("./SimulationToolsUI/icons/leaf.png").scaledToWidth(60)
        )
        self.coinIcon.setPixmap(
            QPixmap("./SimulationToolsUI/icons/coin.png").scaledToWidth(60)
        )

        numberOfRoboTaxis = int(result.roboTaxis)
        numberOfRequests = int(result.fullfilledRequests)
        emptyKm = float(result.emptyKm) / numberOfRequests
        passengerKm = float(result.passengerKm) / numberOfRequests

        self.simulationRunLabel.setText(
            "Run "
            + str(self.resultManager.resultIndex + 1)
            + " of "
            + str(self.resultManager.numberOfResults)
        )
        self.numberOfRoboTaxis.setText("RoboTaxis : " + str(numberOfRoboTaxis))
        self.numberOfRequests.setText("Requests : " + str(numberOfRequests))

        strategy = "Strategy: " + result.strategy
        if "look_ahead" in result.strategy:
            strategy += "  " + result.lookAheadTime + "s"
        if "shared" in result.strategy:
            strategy += "  LF=" + result.latenessFactor + "  RT=" + result.realisticTime

        self.simulationStrategyLabel.setText(strategy)

        totalDistance = emptyKm + passengerKm

        # we assume 15kWh/100km to calculate the power consumption
        powerConsumption = totalDistance * 0.15

        # we assume 401 gram / kWh (German Energymix 2019) to calculate the emissions
        emissions = powerConsumption * 401

        # we assume 32 cent / kWh (German Energy price) to calculate the energy cost
        energyCost = powerConsumption * 0.32

        # the usual factor to calculate the monthly fleet Cost is carPrize / 1000 *40
        # we assume 22500€ / 1000 * 40 = 900€ / Month
        # with a daily usage of 10h we assumed the fleetCost to 3€ / h
        fleetCost = (
            (int(result.pWaitingTime) + int(result.pRidingTime))
            / numberOfRequests
            / 3600
            * 3
        )

        totalCost = energyCost + fleetCost

        costPerPassengerKm = totalCost / passengerKm

        self.totalDistance.setText(
            "Total Driving Distance: "
            + str(float("{:.2f}".format(totalDistance)))
            + " km"
        )
        self.distanceWithPassenger.setText(
            "Distance With Passenger: "
            + str(float("{:.2f}".format(passengerKm)))
            + " km"
        )
        self.powerConsumption.setText(
            "Power Consumption: "
            + str(float("{:.2f}".format(powerConsumption)))
            + " kWh"
        )
        self.emissions.setText(
            "Emissions: " + str(float("{:.2f}".format(emissions))) + " g CO2"
        )
        self.energyCost.setText(
            "Energy Cost: " + str(float("{:.2f}".format(energyCost))) + " €"
        )
        self.fleetCost.setText(
            "Fleet Cost: " + str(float("{:.2f}".format(fleetCost))) + " €"
        )
        self.totalCost.setText(
            "Total Cost: " + str(float("{:.2f}".format(totalCost))) + " €"
        )
        self.costPerPassengerKm.setText(
            "Cost per km: " + str(float("{:.2f}".format(costPerPassengerKm))) + " €"
        )
        self.customerWaitingTime.setText(
            "Waiting Time: "
            + str(int(result.pWaitingTime) // int(result.fullfilledRequests) // 60)
            + " minutes"
        )

        results = []
        results.append(result)
        self.createChart(results)
