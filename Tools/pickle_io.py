#!/usr/bin/env python3

# =============================================================================
# Created at Hochschule Esslingen - University of Applied Sciences
# Department: Anwendungszentrum KEIM
# Author: Andreas Rößler
# Contact: emanuel.reichsoellner@hs-esslingen.de
# Date: April 2021
# License: MIT License
# =============================================================================
# The Script is used to read and write pickle files to conserve projet files
# that the initialization can be skipped at the next run which speeds up the
# Simulation Time performance
# =============================================================================


import sys
import os
import traceback
import sys
import pickle


def read_pickle(filename: str, default_value=None):
    r = default_value
    if os.path.exists(filename):
        try:
            with open(filename, "rb") as handle:
                r = pickle.load(handle)
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
            print(__file__, lines, e, filename)
    return r


def write_pickle(filename: str, obj):
    try:
        with open(filename, "wb") as handle:
            pickle.dump(obj, handle, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        print(__file__, lines, e)
