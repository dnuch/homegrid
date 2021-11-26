#!/usr/bin/env python3
"""
Active Switch List Module
"""

__author__ = "Nick Schiffer"
__version__ = "1.0.0"


from contextlib import contextmanager
from cayenne.client import CayenneMQTTClient
import cayenne_credentials
import config
import logging
import persistent_data_utils
import threading
from typing import List, Optional
from smartswitch import (
    SmartSwitch,
    SmartSwitchSerializable,
    smart_switch_serializable_to_switch,
)


class Active_switch_list:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(format=config.LOGGING_FORMAT)
        self.logger.setLevel(config.LOG_LEVEL)

    active_switches: List[SmartSwitch] = []
    logger = logging.getLogger(__name__)
    ready = False

    def get_switch_from_GUID(self, GUID: str) -> Optional[SmartSwitch]:
        for switch in self.active_switches:
            if GUID == switch.GUID:
                return switch
        return None

    def get_switch_from_MAC(self, MAC: str) -> Optional[SmartSwitch]:
        for switch in self.active_switches:
            if MAC == switch.MAC:
                return switch
        return None

    def load_persistent_data(self):
        serializable_switch_list: List[
            SmartSwitchSerializable
        ] = persistent_data_utils.load(self.logger)
        for switch in serializable_switch_list:
            self.active_switches.append(smart_switch_serializable_to_switch(switch))

    @contextmanager
    def acquire_lock(self):
        for switch in self.active_switches:
            switch.lock.acquire(blocking=True, timeout=threading.TIMEOUT_MAX)
        yield
        for switch in self.active_switches:
            switch.lock.release()

    def save_persistent_data(self):
        serializable_switch_list: List[SmartSwitchSerializable] = []
        with self.acquire_lock():
            for switch in self.active_switches:
                serializable_switch_list.append(SmartSwitchSerializable(switch))
            try:
                persistent_data_utils.dump(serializable_switch_list, self.logger)
            except Exception as e:
                self.logger.error(f"{e}")

    def initialize_clients(self, callback):
        for switch in self.active_switches:
            switch.client = CayenneMQTTClient()
            switch.client.on_message = callback
            self.logger.debug("Connecting Device:")
            self.logger.debug(f"Username: {str(cayenne_credentials.MQTT_USERNAME)}")
            self.logger.debug(f"Password: {str(cayenne_credentials.MQTT_PASSWORD)}")
            self.logger.debug(f"GUID: {switch.GUID}")
            self.logger.debug(f"Port: {int(cayenne_credentials.MQTT_PORT)}")
            switch.client.begin(
                str(cayenne_credentials.MQTT_USERNAME),
                str(cayenne_credentials.MQTT_PASSWORD),
                switch.GUID,
                port=int(cayenne_credentials.MQTT_PORT),
            )
            self.logger.debug(f"Finished Connecting")
            self.ready = True

    def loop(self):
        self.logger.debug("Attempting to start loop")
        for switch in self.active_switches:
            with switch.acquire_lock():
                try:
                    switch.client.loop()
                except Exception as e:
                    self.logger.error(f"Error: {e}")
                

    def __test_populate(self):
        for i in range(10):
            print(f"{i}")
            switch = SmartSwitch(f"MAC: {i}", f"GUID: {i}")
            self.active_switches.append(switch)
            print(
                f"MAC: {switch.MAC}, GUID: {switch.GUID},\n client: {switch.client}, last_time_seen {switch.last_time_seen}"
            )


if __name__ == "__main__":
    sl = Active_switch_list()
    sl.__test_populate()

    for i in range(10):
        switch = sl.get_switch_from_GUID(sl.active_switches[i].GUID)
        switch.GUID = f"GUID: {i + 10}"
        switch.MAC = f"MAC: {i + 10}"
    print("After:")
    for i in range(10):
        switch = sl.get_switch_from_GUID(sl.active_switches[i].GUID)
        print(
            f"MAC: {switch.MAC}, GUID: {switch.GUID},\n client: {switch.client}, last_time_seen {switch.last_time_seen}"
        )
