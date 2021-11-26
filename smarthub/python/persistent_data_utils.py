#!/usr/bin/env python3
"""
Persistent Data Utilities
"""

__author__ = "Nick Schiffer"
__version__ = "1.0.0"



from typing import List
import config
import logging
import pickle

import smartswitch


def dump(switches, logger: logging.Logger):
    if logger is not None:
        logger.debug(f"Saving to filename: {config.PERSISTENT_DATA_FILENAME}")
    with open(config.PERSISTENT_DATA_FILENAME, "wb") as fh:
        pickler = pickle.Pickler(fh)
        pickler.dump(switches)


def load(logger: logging.Logger) -> List[smartswitch.SmartSwitch]:
    if logger is not None:
        logger.debug(f"Opening from filename: {config.PERSISTENT_DATA_FILENAME}")
    switches: List[smartswitch.SmartSwitch] = []
    try:
        with open(config.PERSISTENT_DATA_FILENAME, "rb") as fh:
            switches = pickle.load(fh)
    except Exception as e:
        if logger is not None:
            logger.warn(f"Unable to load persistent data: {e}")
    return switches
