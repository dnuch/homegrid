#!/usr/bin/env python3
"""
Logger Module
"""

__author__ = "Nick Schiffer"
__version__ = "1.0.0"


import config
import logging


class Logger:
    LOGGING_FORMAT = "[%(filename)s:%(lineno)s - %(funcName)28s() ] %(message)s"

    def __init__(self, name):
        self.logger = logging.getLogger(name)
        logging.basicConfig(format=self.LOGGING_FORMAT)
        self.logger.setLevel(config.LOG_LEVEL)
