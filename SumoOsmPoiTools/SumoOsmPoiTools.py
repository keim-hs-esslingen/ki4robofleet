#!/usr/bin/env python3

# =============================================================================
# Created at Hochschule Esslingen - University of Applied Sciences
# Department: Anwendungszentrum KEIM
# Contact: emanuel.reichsoellner@hs-esslingen.de
# Date: March 2021
# License: MIT License
# =============================================================================
# This Script creates a User Interface to process Points Of Interest (POIs)
# Therefore different functions were implemented:
#    * customize the colors of the POIs
#    * generate a Map-Legend according to the current color settings
#    * convert POI - GeoCoordinates to SUMO (OSM) Edge IDs and Positions
#    * convert Parking POIs to Parking Lots which can be utilized by SUMO
#    * create a CSV File with all POI Type to make statistics
# For Details concering usage please read ./README/SUMO_OSM_Tools_Manual.pdf
# =============================================================================

import sys
import os
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import lxml.etree as ET
from PIL import ImageColor, Image, ImageDraw, ImageFont
from PoiModules.PoiTypes import PoiTypeList
from PoiModules.RandomColorGenerator import RandomColorGenerator
from PoiModules.Poi2EdgeConverter import Poi2EdgeConverter
from PoiModules.ParkingAreaConverter import ParkingAreaConverter

import random

import webbrowser


class PoiSetting:
    def __init__(self, type, name, rgb, fill, layer):
        self.type = type
        self.name = name
        self.rgb = rgb
        self.fill = fill
        self.layer = layer


class WidgetRow(QWidget):
    def __init__(self, poiSetting, parent=None):
        super(WidgetRow, self).__init__(parent)
        customRow = QHBoxLayout()

        self.row = customRow

        self.poiName = QLabel(poiSetting.name.ljust(30))
        self.poiName.setFixedWidth(180)

        self.row.addWidget(self.poiName)
        self.check = QCheckBox(" isVisible")
        self.check.setChecked(True)

        self.row.addWidget(self.check)

        inputValidator = QIntValidator()
        inputValidator.setRange(0, 255)

        self.r = QLineEdit(poiSetting.rgb.split(",")[0])
        self.r.setFixedWidth(30)
        self.r.setValidator(inputValidator)
        self.row.addWidget(self.r)
        self.g = QLineEdit(poiSetting.rgb.split(",")[1])
        self.g.setFixedWidth(30)
        self.g.setValidator(inputValidator)
        self.row.addWidget(self.g)
        self.b = QLineEdit(poiSetting.rgb.split(",")[2])
        self.b.setFixedWidth(30)
        self.b.setValidator(inputValidator)
        self.row.addWidget(self.b)

        self.styleString = "background-color : rgb(" + poiSetting.rgb + ");"
        self.colorButton = QPushButton(" ")
        self.colorButton.setFixedWidth(25)
        self.colorButton.setStyleSheet(self.styleString)
        self.row.addWidget(self.colorButton)
        self.setLayout(self.row)

        self.fill = QLineEdit(poiSetting.fill)
        self.fill.setFixedWidth(15)
        self.row.addWidget(self.fill)

        self.layer = QLineEdit(poiSetting.layer)
        self.layer.setFixedWidth(35)
        self.row.addWidget(self.layer)


class PoiToolMainWindow(QWidget):

    bList = []

    def __init__(self):
        super().__init__()
        self.poiTypeList = None
        self.poi2EdgeConverter = Poi2EdgeConverter()
        self.parkingAreaConverter = ParkingAreaConverter()
        self.setWindowTitle(
            "Anwendungszentrum KEIM Hochschule Esslingen - SUMO OSM POI-Tools v0.3"
        )
        self.setGeometry(100, 100, 600, 870)
        self.uiInit()
        self.viewSettingFile = ""
        self.osmPolyFile = ""
        self.workingDirectory = ""
        self.show()

    def uiInit(self):
        self.listWidget = QListWidget(self)
        self.listWidget.setGeometry(60, 60, 500, 600)
        self.listWidget.setStyleSheet("background-color:rgb(64,64,64);")

        scroll_bar = QScrollBar(self)
        self.listWidget.setVerticalScrollBar(scroll_bar)

        self.buttonCreate = QPushButton("Create Settings from osm.poly", self)
        self.buttonCreate.resize(220, 40)
        self.buttonCreate.move(60, 10)
        self.buttonCreate.clicked.connect(self.createSettings)

        self.buttonLoad = QPushButton("Load Settings", self)
        self.buttonLoad.resize(120, 40)
        self.buttonLoad.move(300, 10)
        self.buttonLoad.clicked.connect(self.loadSettings)

        self.buttonWrite = QPushButton("Save Settings", self)
        self.buttonWrite.resize(120, 40)
        self.buttonWrite.move(440, 10)
        self.buttonWrite.clicked.connect(self.writeSettings)

        self.buttonColorRefresh = QPushButton("ColorRefresh", self)
        self.buttonColorRefresh.resize(160, 40)
        self.buttonColorRefresh.move(60, 670)
        self.buttonColorRefresh.clicked.connect(self.colorRefresh)

        self.buttonUnCheckAll = QPushButton("unCheck all", self)
        self.buttonUnCheckAll.resize(160, 40)
        self.buttonUnCheckAll.move(230, 670)
        self.buttonUnCheckAll.clicked.connect(self.unCheckAll)

        self.buttonCheckAll = QPushButton("check all", self)
        self.buttonCheckAll.resize(160, 40)
        self.buttonCheckAll.move(400, 670)
        self.buttonCheckAll.clicked.connect(self.checkAll)

        self.buttonLegend = QPushButton("Create Map Legend", self)
        self.buttonLegend.resize(160, 40)
        self.buttonLegend.move(60, 720)
        self.buttonLegend.clicked.connect(self.createMapLegend)

        self.buttonEdgePos = QPushButton("Create Edge Positions", self)
        self.buttonEdgePos.resize(160, 40)
        self.buttonEdgePos.move(230, 720)
        self.buttonEdgePos.clicked.connect(self.convertPOIs2Edges)

        self.buttonParkingAreas = QPushButton("Convert Parking Areas", self)
        self.buttonParkingAreas.resize(160, 40)
        self.buttonParkingAreas.move(400, 720)
        self.buttonParkingAreas.clicked.connect(self.convertParkingAreas)

        self.buttonStatistics = QPushButton("Create POI Statistics", self)
        self.buttonStatistics.resize(160, 40)
        self.buttonStatistics.move(60, 770)
        self.buttonStatistics.clicked.connect(self.writeStatistics)

        self.buttonApply = QPushButton("Apply View Settings", self)
        self.buttonApply.resize(160, 40)
        self.buttonApply.move(230, 770)
        self.buttonApply.clicked.connect(self.applyViewSettings)

        self.buttonApply = QPushButton("Help / Manual", self)
        self.buttonApply.resize(160, 30)
        self.buttonApply.move(230, 820)
        self.buttonApply.clicked.connect(self.showManual)

        self.keepOriginalPolys = QCheckBox(" keep original Polys", self)
        self.keepOriginalPolys.setChecked(True)
        self.keepOriginalPolys.resize(160, 40)
        self.keepOriginalPolys.move(400, 760)

        self.keepOriginalPOIs = QCheckBox(" keep original POIs", self)
        self.keepOriginalPOIs.setChecked(True)
        self.keepOriginalPOIs.resize(160, 40)
        self.keepOriginalPOIs.move(400, 780)

    def colorRefresh(self):
        for index in range(self.listWidget.count()):
            item = self.listWidget.item(index)
            widgetRow = self.listWidget.itemWidget(item)
            rgb = (
                widgetRow.r.text() + "," + widgetRow.g.text() + "," + widgetRow.b.text()
            )
            widgetRow.colorButton.setStyleSheet("background-color : rgb(" + rgb + ");")
        print("All colors in the List were refreshed...")

    def checkAll(self):
        for index in range(self.listWidget.count()):
            item = self.listWidget.item(index)
            widgetRow = self.listWidget.itemWidget(item)
            widgetRow.check.setChecked(True)

    def unCheckAll(self):
        for index in range(self.listWidget.count()):
            item = self.listWidget.item(index)
            widgetRow = self.listWidget.itemWidget(item)
            widgetRow.check.setChecked(False)

    def createSettings(self):
        #remove existing Elements (if this method is called more than once)
        self.listWidget.clear()
        
        # open file dialog
        osmPolyFile, _ = QFileDialog.getOpenFileName(
            None, "select OSM Poly File", "..", "(*.xml)"
        )
        self.workingDirectory = os.path.dirname(osmPolyFile)       
        self.osmPolyFile = osmPolyFile
        self.poiTypeList = PoiTypeList(osmPolyFile)
        
        randomColorGenerator = RandomColorGenerator()
        pois = self.poiTypeList.getSortedList()

        for poi in pois:
            rgb = randomColorGenerator.getColor()
            poiSetting = PoiSetting("POI", poi, rgb, "1", "1.00")

            self.item = QListWidgetItem(self.listWidget)
            self.listWidget.addItem(self.item)
            self.row = WidgetRow(poiSetting)
            self.item.setSizeHint(self.row.minimumSizeHint())
            self.listWidget.setItemWidget(self.item, self.row)

    def loadSettings(self):
        poiViewSettingsFile, _ = QFileDialog.getOpenFileName(
            None, "select POI View Settings File", ".", "(*.xml)"
        )
        if len(poiViewSettingsFile) > 0:
            print("loading POI View Settings from ", poiViewSettingsFile)
            settingsTree = ET.parse(poiViewSettingsFile)
            settingsRoot = settingsTree.getroot()

            # read poly- Settings
            for setting in settingsRoot.findall("poly"):
                poiSetting = PoiSetting(
                    "POLY",
                    "POLY: " + setting.attrib.get("type"),
                    setting.attrib.get("color"),
                    setting.attrib.get("fill"),
                    setting.attrib.get("layer"),
                )
                self.item = QListWidgetItem(self.listWidget)
                self.listWidget.addItem(self.item)
                self.row = WidgetRow(poiSetting)
                self.item.setSizeHint(self.row.minimumSizeHint())
                self.listWidget.setItemWidget(self.item, self.row)

            # read poi- Settings
            for setting in settingsRoot.findall("poi"):
                poiSetting = PoiSetting(
                    "POI",
                    "POI: " + setting.attrib.get("type"),
                    setting.attrib.get("color"),
                    "",
                    setting.attrib.get("layer"),
                )
                self.item = QListWidgetItem(self.listWidget)
                self.listWidget.addItem(self.item)
                self.row = WidgetRow(poiSetting)
                self.item.setSizeHint(self.row.minimumSizeHint())
                self.listWidget.setItemWidget(self.item, self.row)

    def writeSettings(self, workingDirectory = ""):
        poiViewSettingsFile = ""
        if len(workingDirectory) > 0:
            poiViewSettingsFile = workingDirectory + "/POI_View_Settings.xml"
            self.viewSettingFile = poiViewSettingsFile    
        else:
            poiViewSettingsFile, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save POI View Settings", ".", "*.xml")
            if len(poiViewSettingsFile) > 0:
                poiViewSettingsFile+=".xml"
            else:
                print("Filename for View Settings was not specified!")
                return     
        print("Writing POI View Settings to ", poiViewSettingsFile)
        
        xml_output = ET.Element("poisetting")
        for index in range(self.listWidget.count()):
            item = self.listWidget.item(index)
            widgetRow = self.listWidget.itemWidget(item)
            if widgetRow.check.isChecked():
                if "POLY" in widgetRow.poiName.text():
                    ET.SubElement(
                        xml_output,
                        "poly",
                        type=widgetRow.poiName.text()[6:].strip(),
                        color=widgetRow.r.text()
                        + ","
                        + widgetRow.g.text()
                        + ","
                        + widgetRow.b.text(),
                        fill=widgetRow.fill.text(),
                        layer=widgetRow.layer.text(),
                    )

                if "POI" in widgetRow.poiName.text():
                    ET.SubElement(
                        xml_output,
                        "poi",
                        type=widgetRow.poiName.text()[5:].strip(),
                        color=widgetRow.r.text()
                        + ","
                        + widgetRow.g.text()
                        + ","
                        + widgetRow.b.text(),
                        layer=widgetRow.layer.text(),
                    )
        tree = ET.ElementTree(xml_output)
        tree.write(
            poiViewSettingsFile,
            encoding="UTF-8",
            xml_declaration=True,
            pretty_print=True,
        )

    def createMapLegend(self):
        fnt = ImageFont.truetype("Pillow/Tests/fonts/FreeMono.ttf", 30)
        # first we calculate the size of the image:
        numberOfCheckedPois = 0
        for index in range(self.listWidget.count()):
            item = self.listWidget.item(index)
            widgetRow = self.listWidget.itemWidget(item)
            if widgetRow.check.isChecked():
                numberOfCheckedPois += 1

        im = Image.new("RGB", (500, numberOfCheckedPois * 40 + 20), (64, 64, 64))
        draw = ImageDraw.Draw(im)
        print("Writing POI_Legend.png ...")
        lineCounter = 0
        for index in range(self.listWidget.count()):
            item = self.listWidget.item(index)
            widgetRow = self.listWidget.itemWidget(item)
            if widgetRow.check.isChecked():
                if "POLY" in widgetRow.poiName.text():
                    type = widgetRow.poiName.text()[6:].strip()
                    rgb = (
                        widgetRow.r.text()
                        + ","
                        + widgetRow.g.text()
                        + ","
                        + widgetRow.b.text()
                    ).split(",")
                    draw.rectangle(
                        (10, 10 + lineCounter * 40, 30, 30 + lineCounter * 40),
                        fill=(int(rgb[0]), int(rgb[1]), int(rgb[2])),
                        outline=(0, 0, 0),
                    )
                    draw.text(
                        (40, 5 + lineCounter * 40),
                        type,
                        font=fnt,
                        fill=(255, 255, 255, 128),
                    )
                    lineCounter += 1

                if "POI" in widgetRow.poiName.text():
                    type = widgetRow.poiName.text()[5:].strip()
                    rgb = (
                        widgetRow.r.text()
                        + ","
                        + widgetRow.g.text()
                        + ","
                        + widgetRow.b.text()
                    ).split(",")
                    draw.ellipse(
                        (10, 10 + lineCounter * 40, 30, 30 + lineCounter * 40),
                        fill=(int(rgb[0]), int(rgb[1]), int(rgb[2])),
                        outline=(0, 0, 0),
                    )
                    draw.text(
                        (40, 5 + lineCounter * 40),
                        type,
                        font=fnt,
                        fill=(255, 255, 255, 128),
                    )
                    lineCounter += 1
        im.save(self.workingDirectory+"/POI_Legend.png", quality=95)
        print("READY!!!")

    def writeStatistics(self):
        print("Writing PoiStatistics.csv ...")
        self.poiTypeList.writeStatistics(self.workingDirectory)
        print("READY!!!")

    def applyViewSettings(self):
        self.writeSettings(self.workingDirectory)
        self.poiTypeList.applyViewSettings(
            self.keepOriginalPolys.isChecked(), self.keepOriginalPOIs.isChecked(), self.osmPolyFile, self.viewSettingFile
        )

    def convertPOIs2Edges(self):
        self.writeSettings(self.workingDirectory)
        self.poi2EdgeConverter.convertPois2Edges([], self.workingDirectory)

    def convertParkingAreas(self):
        self.parkingAreaConverter.convertParkingAreas(self.workingDirectory)

    def showManual(self):
        cwd = os.getcwd()
        pathToManual = "file://" + cwd + "/README/SUMO_OSM_Tools_Manual.pdf"
        print(pathToManual)
        webbrowser.open(pathToManual)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    poiToolMainWindow = PoiToolMainWindow()
    poiToolMainWindow.show()
    sys.exit(app.exec_())
