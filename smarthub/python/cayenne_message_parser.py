#!/usr/bin/env python3
"""
Cayenne Message Parser
"""

__author__ = "Nick Schiffer"
__version__ = "1.0.0"


from cayenne.client import CayenneMessage
from config import VIRTUAL_CHANNEL, LOGGING_FORMAT, LOG_LEVEL
import logging
from typing import Optional


class Cayenne_switch_message:
    def __init__(
        self,
        GUID: str,
        topic: str,
        channel: VIRTUAL_CHANNEL,
        message_id: str,
        power_state: bool,
    ):
        self.GUID = GUID
        self.topic = topic
        self.channel = channel
        self.message_id = message_id
        self.power_state = power_state


def cayenne_message_to_object(
    message: CayenneMessage,
) -> Optional[Cayenne_switch_message]:
    try:
        GUID: str = message.client_id
        topic: str = message.topic
        channel_raw: int = message.channel
        power_state_raw = int(message.value)
        message_id = message.msg_id

        if channel_raw not in VIRTUAL_CHANNEL:
            raise Exception(f"Invalid Channel {channel_raw}")
        if power_state_raw not in [0, 1]:
            raise Exception("Invalid Power State")

        return Cayenne_switch_message(
            GUID,
            topic,
            VIRTUAL_CHANNEL(channel_raw),
            message_id,
            True if (1 == power_state_raw) else False,
        )

    except Exception as e:
        return None


def print_message(message: Cayenne_switch_message):
    logger = logging.getLogger(__name__)
    logging.basicConfig(format=LOGGING_FORMAT)
    logger.setLevel(LOG_LEVEL)
    logger.debug(f"TEST: GUID: {message.GUID}")
    logger.debug(f"TEST: topic: {message.topic}")
    logger.debug(f"TEST: channel: {message.channel}")
    logger.debug(f"TEST: message_id: {message.message_id}")
    logger.debug(f"TEST: Power State: {message.power_state}")


def __test(message: CayenneMessage):
    parsed_message = cayenne_message_to_object(message)

    if parsed_message:
        print(f"TEST: GUID: {parsed_message.GUID}")
        print(f"TEST: topic: {parsed_message.topic}")
        print(f"TEST: channel: {parsed_message.channel}")
        print(f"TEST: message_id: {parsed_message.message_id}")
        print(f"TEST: Power State: {parsed_message.power_state}")
    else:
        print("TEST: RECEIVED NONE")


if __name__ == "__main__":
    exit(0)
