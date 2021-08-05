#!/usr/bin/env python3

# =============================================================================
# Created at Hochschule Esslingen - University of Applied Sciences
# Department: Anwendungszentrum KEIM
# Author: Andreas Rößler
# Contact: emanuel.reichsoellner@hs-esslingen.de
# Date: January 2021
# License: MIT License
# =============================================================================
# This Script checks if SUMO is available on the System
# =============================================================================

import sys
import os


def sumo_available(dbg=False):
    if "SUMO_HOME" in os.environ:
        tools = os.path.join(os.environ["SUMO_HOME"], "tools")
        if tools not in sys.path:
            sys.path.append(tools)
            if dbg:
                print("Sys.Path", sys.path)
    else:
        print("please declare environment variable 'SUMO_HOME'")
        exit(-1)
