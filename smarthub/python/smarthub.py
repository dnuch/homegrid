#!/usr/bin/env python3
"""
SmartHub Module
"""

__author__ = "Nick Schiffer"
__version__ = "1.0.0"


from active_switch_list import Active_switch_list
from cayenne.client import CayenneMessage
import cayenne_message_parser
import config
import threading
import logging
import queue
import serial
import signal
from smartswitch import SmartSwitch
import time
from typing import List
from xbee_message_parser import xbee_message_to_object, Xbee_coordinator_message


class SmartHub:

    cloud_message_queue = queue.Queue()
    zigbee_message_queue = queue.Queue()
    cloud_job_queue = queue.Queue()
    zigbee_job_queue = queue.Queue()

    active_switch_list: Active_switch_list = Active_switch_list()

    serial_port = serial.Serial("/dev/ttyUSB0", baudrate=115200, timeout=2)

    global_shutdown_requested = False

    logger = logging.getLogger(__name__)

    def __run_initialization(self):
        self.__init_logger()
        self.__initialize_active_switch_list()
        self.__attach_signal_handlers()

    def __initialize_active_switch_list(self):
        self.active_switch_list.load_persistent_data()
        self.active_switch_list.initialize_clients(self.__cloud_receiver_callback)

    def __init_logger(self):
        logging.basicConfig(format=config.LOGGING_FORMAT)
        self.logger.setLevel(config.LOG_LEVEL)

    def __attach_signal_handlers(self):
        signal.signal(signal.SIGTERM, self.__shutdown_handler)
        signal.signal(signal.SIGINT, self.__shutdown_handler)

    def __shutdown_handler(self, signum, frame):
        self.logger.info(f"Received Shutdown Signal {signum}")
        self.global_shutdown_requested = True

    def __persistent_backup_thread(self):
        last_backup_time = time.time()
        while not self.global_shutdown_requested:
            time.sleep(1)
            current_time = time.time()
            if current_time > (last_backup_time + config.BACKUP_INTERVAL_SECONDS):
                self.active_switch_list.save_persistent_data()
                last_backup_time = current_time

    def __cloud_receiver_callback(self, message: CayenneMessage):
        parsed_message = cayenne_message_parser.cayenne_message_to_object(message)
        if parsed_message:
            cayenne_message_parser.print_message(parsed_message)
            self.cloud_job_queue.put(parsed_message)
        else:
            self.logger.warn(f"Unable to Parse Cayenne Message: {str(message)}")

    def __mqtt_loop_thread(self):
        while not self.global_shutdown_requested:
            if self.active_switch_list.ready:
                self.active_switch_list.loop()
            time.sleep(config.MQTT_LOOP_TIME_SECONDS)

    def __zigbee_receiver_thread(self):
        while not self.global_shutdown_requested:
            try:
                serial_message = self.serial_port.readline().strip()
                decoded_serial_message = serial_message.decode()
                if 0 == len(decoded_serial_message):
                    print("Got nothing")
                    continue
                self.logger.debug(f"Serial Message Received: {decoded_serial_message}")
                parsed_message = xbee_message_to_object(str(decoded_serial_message))
                if parsed_message is not None:
                    self.zigbee_job_queue.put(parsed_message)
                else:
                    self.logger.error(
                        f"Failed to Parse Coordinator Message: '{str(decoded_serial_message)}'"
                    )

            except Exception as e:
                self.logger.error(f"Exception while Parsing Coordinator Message: {e}")

    def __zigbee_job_processor_thread(self):
        while not self.global_shutdown_requested:
            try:
                item: Xbee_coordinator_message = self.zigbee_job_queue.get(timeout=1)
                self.logger.debug(f"Popped: {item}")
                switch: SmartSwitch = self.active_switch_list.get_switch_from_MAC(
                    item.MAC
                )
                if switch is not None:
                    switch.handle_serial_message(item)
                else:
                    self.logger.error(f"Could not Find Switch with MAC: {item.MAC}")

            except queue.Empty:
                pass

    def __cloud_job_processor_thread(self):
        while not self.global_shutdown_requested:
            item: cayenne_message_parser.Cayenne_switch_message = None
            try:
                item = self.cloud_job_queue.get(timeout=1)
                self.logger.debug(f"Popped: {item}")
            except queue.Empty:
                continue
            if item is not None:
                self.logger.debug(f"Getting Switch from {item.GUID}")
                switch: SmartSwitch = self.active_switch_list.get_switch_from_GUID(
                    GUID=item.GUID
                )
                if switch is not None:
                    with switch.acquire_lock():
                        self.logger.debug("Got Switch: ")
                        self.logger.debug(f"MAC: {switch.MAC}")
                        self.logger.debug(f"GUID: {switch.GUID}")
                        serial_message: str = (
                            switch.MAC + "," + ("on" if (item.power_state) else "off")
                        )
                        self.logger.info(
                            "Sending Message to Coordinator: " + serial_message
                        )
                        try:
                            self.serial_port.write(bytes(serial_message, "utf-8"))
                        except Exception as e:
                            self.logger.critical(
                                f"Failed to Write to Serial Device: '{e}'"
                            )
                else:
                    self.logger.error(f"Unable to Find Switch with GUID: '{item.GUID}'")

    def __tester_thread(self):
        count = 0
        sample_messages = [
            "1234,1,15.169,122.5637",
            "1234,1,15.169,122.5637",
            "1234,1,13.002,122.2096",
            "1234,1,13.2187,122.1879",
            "1234,1,13.2187,122.1807",
            "1234,1,13.2187,122.2241",
            "1234,1,13.2187,122.2385",
            "1234,1,13.4354,122.2313",
            "1234,1,13.4354,122.2313",
            "1234,1,13.6521,122.0939",
            "1234,1,13.6521,122.0145",
            "1234,1,13.6521,122.1084",
            "1234,1,13.6521,122.2385",
            "1234,1,13.8688,122.2457",
            "1234,1,2.6004,122.3614",
            "1234,1,0.0,122.4264",
            "1234,1,0.0,122.4192",
            "1234,1,0.0,122.4481",
            "1234,1,0.0,122.4336",
            "1234,1,0.0,122.477",
            "1234,1,0.0,122.5132",
            "1234,1,0.0,122.5132",
            "1234,1,0.0,122.5348",
            "1234,1,0.0,122.5132",
            "1234,1,4.334,122.4553",
            "1234,1,7.5845,122.4264",
            "1234,0,7.3678,122.4336",
            "1234,0,7.5845,122.3975",
            "1234,0,7.5845,121.8771",
            "1234,0,7.5845,121.8771",
            "1234,0,7.5845,122.4481",
            "1234,0,7.5845,122.4336",
            "1234,0,7.5845,122.4336",
            "1234,0,7.5845,122.3975",
            "1234,0,7.5845,122.4192",
            "1234,0,7.5845,122.4409",
            "1234,0,7.5845,122.4481",
            "1234,0,7.5845,122.4192",
            "1234,0,7.5845,122.4192",
            "1234,0,7.5845,122.3975",
            "1234,0,7.5845,122.3831",
            "1234,0,7.5845,122.3975",
            "1234,0,7.5845,122.3686",
            "1234,0,7.5845,122.3686",
            "1234,0,7.5845,122.3397",
            "1234,0,7.5845,122.3035",
            "1234,0,7.5845,122.2891",
            "1234,0,7.5845,122.318",
            "1234,0,7.5845,122.2891",
            "1234,0,7.8012,122.2891",
            "1234,0,7.8012,122.253",
            "1234,0,7.5845,122.3686",
            "1234,0,7.8012,122.4047",
            "1234,0,7.5845,122.3831",
        ]
        index = 0
        while not self.global_shutdown_requested:
            self.logger.debug("Pushing to zigbee message queue")
            self.zigbee_message_queue.put(sample_messages[index])
            count += 1
            index = (index + 1) % len(sample_messages)
            time.sleep(10)

    def run(self):
        self.__run_initialization()
        thread_functions = [
            self.__zigbee_receiver_thread,
            self.__cloud_job_processor_thread,
            self.__zigbee_job_processor_thread,
            self.__persistent_backup_thread,
            self.__mqtt_loop_thread,
            # self.__tester_thread,
        ]
        threads: List[threading.Thread] = []
        for thread_function in thread_functions:
            thread = threading.Thread(target=thread_function)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()
        self.active_switch_list.save_persistent_data()
        self.logger.info("Bye :)")


def main():
    """Main entry point of the app"""
    SmartHub().run()


if __name__ == "__main__":
    """This is executed when run from the command line"""
    main()
