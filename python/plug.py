import xbee
import time
from machine import I2C, Pin

ON_STATE = 0
OFF_STATE = 1

STATE = ON_STATE

coordinator_mac_addr64 = None

red_pin = Pin("D2", mode=Pin.OUT, value=0)
blue_pin = Pin("D4", mode=Pin.OUT, value=0)
green_pin = Pin("D3", mode=Pin.OUT, value=0)
relay_pin = Pin("D8", mode=Pin.OUT, value=1) # 1 Relay on, 0 Relay off
button_pin = Pin("D10", mode=Pin.IN, pull=Pin.PULL_DOWN)

def button_handler(state):
    next_state = state

    if button_pin.value():
        if state == ON_STATE:
            next_state = OFF_STATE
        elif state == OFF_STATE:
            next_state = ON_STATE
        print("Button Pressed")
    
    return next_state


def i2c_init():
    i2c = I2C(1, freq=400000)       # create I2C peripheral at frequency of 400kHz


def discover_coordinator(coordinator_mac_addr64):
    mac_addr64 = coordinator_mac_addr64
    if mac_addr64 == None:
        try:
            xbee_discover_list = xbee.discover()

            for device in xbee_discover_list:
                if 'coordinator' == device['node_id']:
                    mac_addr64 = device['sender_eui64']
                    print("Coordinator discovered: {}".format(mac_addr64))
        except Exception as e:
            print("Discover Failure: {}".format(str(e)))
    
    return mac_addr64


def get_sensor_payload():
    return 'Sensor Payload'


def transmit_sensor_payload(coordinator_mac_addr64):
    if coordinator_mac_addr64:
        sensor_payload = None
        sensor_payload = get_sensor_payload()
        if sensor_payload:
            try:
                xbee.transmit(coordinator_mac_addr64, sensor_payload)
            except Exception as e:
                print("Transmission failure: {}".format(str(e)))


def periodic_run(state, coordinator_mac_addr64):
    if state == ON_STATE:
        red_pin.value(0)
        blue_pin.value(0)
        green_pin.value(0)
        relay_pin.value(1)
        transmit_sensor_payload(coordinator_mac_addr64)
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
        print("Data received from {}: {}".format(sender_mac_addr, payload))
        
        if payload == "on":
            next_state = ON_STATE
        elif payload == "off":
            next_state = OFF_STATE

    return next_state


i2c_init()

while True:
    coordinator_mac_addr64 = discover_coordinator(coordinator_mac_addr64)
    periodic_run(STATE, coordinator_mac_addr64)
    STATE = command_message_receiver_handler(STATE)
    STATE = button_handler(STATE)
            
    time.sleep(1)
