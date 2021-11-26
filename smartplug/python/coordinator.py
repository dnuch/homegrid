from sys import stdin, stdout
import binascii
import xbee
import time

# Pi to XBee Functions


def transmit_command_message(command_list):
    if len(command_list) == 2:
        try:
            mac_addr = binascii.unhexlify(command_list[0])  # HEX string to byte array
            action = command_list[1]

            xbee.transmit(mac_addr, action)
        except Exception as e:
            print("Transmission failure: {}".format(str(e)))


def command_message_receiver_handler():
    # Process input line
    line = stdin.buffer.read()

    if line:
        line = line.decode()
        command_list = line.split(",")  # CSV delimiter
        transmit_command_message(command_list)


# XBee to Pi Functions
def sensor_message_receiver_handler():
    received_msg = xbee.receive()

    if received_msg:
        # Create HEX string representation of byte array
        sender_mac_addr = "".join(
            "{:02x}".format(x) for x in received_msg["sender_eui64"]
        )
        payload = received_msg["payload"].decode()
        # Serially printout received message
        stdout.buffer.write("{},{}\r\n".format(sender_mac_addr, payload))


while True:
    command_message_receiver_handler()
    sensor_message_receiver_handler()

    time.sleep(0.1)
