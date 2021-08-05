#!/usr/bin/env python3

# =============================================================================
# Created at Hochschule Esslingen - University of Applied Sciences
# Department: Anwendungszentrum KEIM
# Author: Andreas Rößler
# Contact: emanuel.reichsoellner@hs-esslingen.de
# Date: April 2021
# License: MIT License
# =============================================================================
# The Script is used to read and write JSON- Files
# =============================================================================

import sys
import os
import json
import traceback
import sys


def read_JSON(filename: str, default_value=None):
    r = default_value
    if os.path.exists(filename):
        try:
            with open(filename) as json_data:
                r = json.load(json_data)
        except json.JSONDecodeError as e:
            print(
                "msg: {}\ndoc: {}\npos: {}\nline: {}/{}\n ".format(
                    e.msg, e.doc, e.pos, e.lineno, e.colno
                )
            )
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
            print(__file__, lines, e, filename)
    return r


def write_JSON(filename: str, obj):
    try:
        with open(filename, "w") as fp:
            json.dump(obj, fp, indent=4, sort_keys=True)
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        print(__file__, lines, e)
