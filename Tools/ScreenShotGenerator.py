#!/usr/bin/env python3

# =============================================================================
# Created at Hochschule Esslingen - University of Applied Sciences
# Department: Anwendungszentrum KEIM
# Contact: emanuel.reichsoellner@hs-esslingen.de
# Date: March 2021
# License: MIT License
# =============================================================================
# The class ScreenShotGenerator can be used to create SUMO Screenshots 
# at certain time intervals
# usage: create an instance with the directory name, the interval at which a screenshot should be taken, and the zoom level
# e.g.: screenShotGenerator = ScreenShotGenerator(traci, f"epoch_{dateStr}_{strategy}_{nv:02d}v",100,500)
# call the step() Method in the Simulation- loop: screenShotGenerator.step(sumo_time)
# =============================================================================


import os

class ScreenShotGenerator:
    def __init__(self, traci, directoryName, intervalTime, zoom):
        self.traci = traci
        self.directoryName = directoryName
        self.intervalTime = int(intervalTime)
        self.zoom = zoom
        cwd = os.getcwd()

        try:
            os.makedirs(cwd+'/'+directoryName)
        except OSError:
            print ("The directory ",cwd,"/",directoryName,"couldn't be created")

    def step(self, currentStep):
        if int(currentStep) % self.intervalTime == 0:
            self.traci.gui.setZoom(self.traci.gui.DEFAULT_VIEW,float(self.zoom))
            self.traci.gui.screenshot(self.traci.gui.DEFAULT_VIEW , "./"+self.directoryName+"/sumo_time_"+str(currentStep)+".png", width=600, height=600)  


