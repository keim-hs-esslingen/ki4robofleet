#!/usr/bin/env python3

# =============================================================================
# Created at Hochschule Esslingen - University of Applied Sciences
# Department: Anwendungszentrum KEIM
# Author: Andreas Rößler
# Contact: emanuel.reichsoellner@hs-esslingen.de
# Date: April 2021
# License: MIT License
# =============================================================================
# The Script is used to define Console- Logs 
# Different Colors for different Log- Levels are used
# Simulation Time performance
# =============================================================================

from inspect import currentframe, getfile
from termcolor import colored
from pathlib import Path


def factory(fg, bg):
    def log(txt):
        cf = currentframe()
        back_frame = cf.f_back
        file = getfile(back_frame)
        stem = Path(file).stem
        msg = f"{stem}#{back_frame.f_lineno}: {txt}"
        print(colored(msg, fg, bg))

    return log


glog = factory("white", "on_green")
elog = factory("white", "on_red")
log = factory("white", "on_grey")
ylog = factory("yellow", "on_blue")
dlog = factory("white", "on_blue")

if __name__ == "__main__":
    log("Hello World")
    dlog("EOF")
    glog("test")
    elog("error")
    ylog("info")
