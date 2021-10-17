import xbee
import time
from machine import I2C, Pin

ON_STATE = 0
OFF_STATE = 1

STATE = ON_STATE

red_pin = Pin("D2", mode=Pin.OUT, value = 0)
blue_pin = Pin("D4", mode=Pin.OUT, value = 0)
green_pin = Pin("D3", mode=Pin.OUT, value = 0)
relay_pin = Pin("D14", mode=Pin.OUT, value = 1) # 1 Relay on, 0 Relay off

def i2c_init():
    i2c = I2C(1, freq=400000)       # create I2C peripheral at frequency of 400kHz

    # print(i2c.scan())

def periodic_run(state):
    if state == ON_STATE:
        red_pin.value(0)
        blue_pin.value(0)
        green_pin.value(0)
        relay_pin.value(1)
        print("on")
    elif state == OFF_STATE:
        red_pin.value(1)
        blue_pin.value(0)
        green_pin.value(0)
        relay_pin.value(0)
        print("off")

def command_message_receiver_handler(state):
    next_state = state

    received_msg = xbee.receive()
    if received_msg:
        # Get the sender's 64-bit address and payload from the received message.
        sender_mac_addr = ''.join('{:02x}'.format(x) for x in received_msg['sender_eui64'])
        payload = received_msg['payload'].decode()
        print("Data received from {}: {}".format(sender_mac_addr, payload.decode()))
        
        if payload == "on":
            next_state = ON_STATE
        elif payload == "off":
            next_state = OFF_STATE

    return next_state

i2c_init()

while True:
    periodic_run(STATE)
    STATE = command_message_receiver_handler(STATE)
            
    time.sleep(1)
