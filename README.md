# KI4RoboFleet

#### A Simulation Environment based on SUMO to analyze Scenarios for autonomous driving vehicles in Cities

### Link to the Overview-Page: [KI4RoboFleet](https://keim-hs-esslingen.github.io/ki4robofleet/)

### Video Tutorial 

##### [Setup a new SUMO Model from scratch using OsmWebWizard](https://youtu.be/Dh_0A-wOk84)

### Reqirements to run the Simulation:

- ubuntu 20.04
- Python 3.8.5 or higher
- Eclipse SUMO Version 1.9.0 or higher (Download from https://www.eclipse.org/sumo/)

### Some Python Packages need to be installed:

```bash
pip install osmapi
pip install PyQt5
pip install PyQtChart
```

### The latest SUMO Tools Version has to be installed otherwise routing errors could arise:

```bash
sudo apt-get dist-upgrade
```

### Test the Setup with the provided Scipt to see if SUMO is working properly
```bash
./testRun.sh
```

### Getting Started:

```bash
python KI4RoboFleetUI.py
```

or

```bash
python3 KI4RoboFleetUI.py
```

### During the Simulation the Status is displayed on the Web Interface 
http://localhost:8080/index.html




