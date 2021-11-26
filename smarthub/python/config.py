#!/usr/bin/env python3
"""
Configuration Parameters
"""

__author__ = "Nick Schiffer"
__version__ = "1.0.0"


from enum import Enum, EnumMeta
import logging
import os

LOG_LEVEL = logging.DEBUG

PERSISTENT_DATA_FILENAME = (
    str(os.path.dirname(os.path.abspath(__file__)))
    + "/"
    + "homegrid_persistent_data.bin"
)

BACKUP_INTERVAL_SECONDS = 30

LOGGING_FORMAT = "[%(filename)s:%(lineno)s - %(funcName)28s() ] %(message)s"

MQTT_LOOP_TIME_SECONDS = 2

NODE_POWER_AVERAGING_INTERVAL_SECONDS = 1

KILOWATT_COST_DOLLARS = 0.15


class MyEnumMeta(EnumMeta):
    def __contains__(cls, item):
        return item in [v.value for v in cls.__members__.values()]


class VIRTUAL_CHANNEL(Enum, metaclass=MyEnumMeta):
    POWER_TOGGLE = 1
    POWER_STATE = 2
    POWER_DRAW = 3
    VOLTAGE = 4
    CUMULATIVE_POWER_CONSUMPTION_KWH = 5
    CUMULATIVE_POWER_COST_DOLLARS = 6
    POWER_INDICATOR = 10
