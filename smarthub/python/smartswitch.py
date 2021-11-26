#!/usr/bin/env python3
"""
SmartSwitch Module
"""

__author__ = "Nick Schiffer"
__version__ = "1.0.0"


from typing_extensions import final
import cayenne.client
import config
from contextlib import contextmanager
import threading
import time
from xbee_message_parser import Xbee_coordinator_message


class SmartSwitch:
    def __init__(
        self,
        MAC: str,
        GUID: str,
        last_time_seen: float = time.time(),
        current_power_state: bool = False,
        cumulative_power_consumption_kwh: float = 0.0,
        cumulative_power_cost_dollars: float = 0.0,
    ):
        self.MAC = MAC
        self.GUID = GUID
        self.client = cayenne.client.CayenneMQTTClient()
        self.last_time_seen = last_time_seen
        self.lock = threading.Lock()
        self.current_power_state = current_power_state
        self.cumulative_power_consumption_kwh = cumulative_power_consumption_kwh
        self.cumulative_power_cost_dollars = cumulative_power_cost_dollars

    @contextmanager
    def acquire_lock(self):
        ret = self.lock.acquire(blocking=True, timeout=threading.TIMEOUT_MAX)
        print(f"ACQUIRED LOCK: {ret} {self}")
        yield
        print(f"RELEASING LOCK: {self}")
        self.lock.release()
        print(f"RELEASED LOCK: {self}")

    def handle_serial_message(self, message: Xbee_coordinator_message):
        with self.acquire_lock():
            try:
                self.current_power_state = message.power_state
                self.last_time_seen = time.time()
                kilowatt_hours_gained = self.___calculate_watts_to_kwh(message.power_draw)
                self.cumulative_power_consumption_kwh += kilowatt_hours_gained
                self.cumulative_power_cost_dollars += self.___calculate_kwh_to_dollars(
                    kilowatt_hours_gained
                )

                self.client.virtualWrite(
                    config.VIRTUAL_CHANNEL.POWER_DRAW.value,
                    message.power_draw,
                    dataType="pow",
                    dataUnit="w",
                )

                self.client.virtualWrite(
                    config.VIRTUAL_CHANNEL.POWER_TOGGLE.value,
                    1 if (message.power_state) else 0,
                    dataType="digital_sensor",
                    dataUnit="d",
                )

                self.client.virtualWrite(
                    config.VIRTUAL_CHANNEL.POWER_INDICATOR.value,
                    1 if (message.power_state) else 0,
                    dataType="digital_sensor",
                    dataUnit="d",
                )

                self.client.virtualWrite(
                    config.VIRTUAL_CHANNEL.VOLTAGE.value,
                    message.voltage,
                    dataType="voltage",
                    dataUnit="v",
                )

                self.client.virtualWrite(
                    config.VIRTUAL_CHANNEL.POWER_STATE.value,
                    1.0 if (message.power_state) else 0.0,
                    dataType="analog_sensor",
                    dataUnit="null",
                )

                self.client.virtualWrite(
                    config.VIRTUAL_CHANNEL.CUMULATIVE_POWER_CONSUMPTION_KWH.value,
                    self.cumulative_power_consumption_kwh,
                    dataType="energy",
                    dataUnit="kwh",
                )

                self.client.virtualWrite(
                    config.VIRTUAL_CHANNEL.CUMULATIVE_POWER_COST_DOLLARS.value,
                    self.cumulative_power_cost_dollars,
                    dataType="analog_sensor",
                    dataUnit="null",
                )
            except Exception as e:
                print(f"exception: {e}")

    @staticmethod
    def ___calculate_watts_to_kwh(watts: float) -> float:
        # E(kWh) = P(W) × t(hr) / 1000
        return float(
            float(watts)
            * float(1.0 / 60.0)
            * float(config.NODE_POWER_AVERAGING_INTERVAL_SECONDS)
            / float(1000.0)
        )

    @staticmethod
    def ___calculate_kwh_to_dollars(kwh: float) -> float:
        # $ = E(kWh) * kilowatt cost
        return kwh * float(config.KILOWATT_COST_DOLLARS)


class SmartSwitchSerializable:
    def __init__(self, switch: SmartSwitch):
        self.MAC = switch.MAC
        self.GUID = switch.GUID
        self.last_time_seen = switch.last_time_seen
        self.current_power_state = switch.current_power_state
        self.cumulative_power_consumption_kwh = switch.cumulative_power_consumption_kwh
        self.cumulative_power_cost_dollars = switch.cumulative_power_cost_dollars


def smart_switch_serializable_to_switch(switch: SmartSwitchSerializable) -> SmartSwitch:
    return SmartSwitch(
        switch.MAC,
        switch.GUID,
        switch.last_time_seen,
        switch.current_power_state,
        switch.cumulative_power_consumption_kwh,
        switch.cumulative_power_cost_dollars,
    )
