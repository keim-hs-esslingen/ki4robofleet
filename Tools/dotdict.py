#!/usr/bin/env python3

# =============================================================================
# Created at Hochschule Esslingen - University of Applied Sciences
# Department: Anwendungszentrum KEIM
# Author: Andreas Rößler
# Contact: emanuel.reichsoellner@hs-esslingen.de
# Date: March 2021
# License: MIT License
# =============================================================================
# The class DotDict makes Python Dictionaries accessible with Dot- Notation
# =============================================================================

# Further Information see here:
# http://stackoverflow.com/questions/2352181/how-to-use-a-dot-to-access-members-of-dictionary


from datetime import datetime


def init(passed_para=0):
    """called automatically from updater"""
    now = datetime.now()
    print("init", __name__, __file__, str(now))
    return passed_para


class DotDict(dict):
    """
    dot.notation access to dictionary attributes
    """

    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, d):
        self.__dict__.update(d)
