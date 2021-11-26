#!/usr/bin/env python3
"""
XBee Message Utilities
"""

__author__ = "Nick Schiffer"
__version__ = "1.0.0"


import time
from typing import Optional


class Xbee_coordinator_message:
    def __init__(self, MAC: str, power_state: bool, power_draw: float, voltage: float):
        self.MAC = MAC
        self.power_state = power_state
        self.power_draw = power_draw
        self.voltage = voltage
        self.timestamp = time.time()


def xbee_message_to_object(message: str) -> Optional[Xbee_coordinator_message]:
    try:
        components = message.split(",")
        MAC = str(components[0])
        power_state = True if (0 == int(components[1])) else False
        power_draw = float(components[2])
        voltage = float(components[3])
        return Xbee_coordinator_message(
            MAC=MAC, power_state=power_state, power_draw=power_draw, voltage=voltage
        )
    except Exception as e:
        return None


if __name__ == "__main__":
    sample_message_good = "0013a20041cc5773,1,15.169,122.5637"
    sample_message_bad = "0013a20041cc5773,Config Success"

    parsed_message = xbee_message_to_object(message=sample_message_good)
    if parsed_message is None:
        print("Received None")
        exit(1)

    print(f"MAC: {parsed_message.MAC}")
    print(f"Power state: {parsed_message.power_state}")
    print(f"Power Draw: {parsed_message.power_draw}")
    print(f"Voltage: {parsed_message.voltage}")
    print(f"Timestamp: {parsed_message.timestamp}")
    exit(0)
