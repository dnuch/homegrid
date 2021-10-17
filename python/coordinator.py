from sys import stdin, stdout
import binascii
import xbee
import time

end_message_character = '!'
command_string = ""

# Pi to XBee Functions

def is_xbee_in_discover_list(mac_addr):
    is_mac_addr_found = False
    xbee_discover_list = xbee.discover()

    for device in xbee_discover_list:
        addr64 = device['sender_eui64']
        if addr64 == mac_addr:
            is_mac_addr_found = True

    return is_mac_addr_found

def transmit_command_message(command_list):
    if len(command_list) == 2:
        try:
            mac_addr = binascii.unhexlify(command_list[0]) # HEX string to byte array
            action = command_list[1]

            if is_xbee_in_discover_list(mac_addr):
                xbee.transmit(mac_addr, action)
        except:
            # HEX string failed to parse due to being uneven
            pass

def command_message_receiver_handler(message):
    # Process input byte over serial communication
    character = stdin.buffer.read(1).decode("utf-8")

    if character == end_message_character: # Process command message
        # stdout.buffer.write(message) # Echo test
        command_list = message.split(",") # CSV delimiter
        transmit_command_message(command_list)
        message = "" # Reset command message for next message
    else: # Build up command message
        message += character

    return message

# XBee to Pi Functions

def sensor_message_receiver_handler():
    received_msg = xbee.receive()

    if received_msg:
        # Create HEX string representation of byte array
        sender_mac_addr = ''.join('{:02x}'.format(x) for x in received_msg['sender_eui64'])
        payload = received_msg['payload']
        # Serially printout received message
        stdout.buffer.write("{},{}".format(sender_mac_addr, payload))
        
while True:
    command_string = command_message_receiver_handler(command_string)
    sensor_message_receiver_handler()

    time.sleep(1 / 1000)
