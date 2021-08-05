#!/usr/bin/env python3

# =============================================================================
# Created at Hochschule Esslingen - University of Applied Sciences
# Department: Anwendungszentrum KEIM
# Author: Andreas Rößler
# Contact: emanuel.reichsoellner@hs-esslingen.de
# Date: February 2021
# License: MIT License
# =============================================================================
# Reload/Update Module
# =============================================================================

import os
import threading
import time


def onChange(file, callback):
    print(file, time.strftime("%H:%M:%S", time.gmtime(os.path.getmtime(file))))
    worker = threading.Thread(target=waitOnChange, args=(file, callback))
    worker.setDaemon(True)
    worker.start()


def waitOnChange(file, callback):
    mtime = os.stat(file).st_mtime
    while mtime == os.stat(file).st_mtime:
        time.sleep(1)
    print(
        file, time.strftime("%H:%M:%S", time.gmtime(os.path.getmtime(file))), "changed"
    )
    try:
        callback(file)
    except Exception as e:
        print("Error in callback for", file)
