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
relay_pin = Pin("D12", mode=Pin.OUT, value=1)  # 1 Relay on, 0 Relay off
button_pin = Pin("D10", mode=Pin.IN, pull=Pin.PULL_DOWN)


def button_handler(state, time_tracker):
    next_state = state

    if time_tracker.is_button_debounce_timer_expired() and button_pin.value():
        time_tracker.set_button_debounce_timer()
        if state == ON_STATE:
            next_state = OFF_STATE
        elif state == OFF_STATE:
            next_state = ON_STATE
        print("Button Pressed")

    return next_state


i2c = I2C(1, freq=400000)  # create I2C peripheral at frequency of 400kHz

def config_calc_number_of_averages():
    global coordinator_mac_addr64
    global i2c
    access_code_reg = 0x2F
    customer_access_code = 0x4F70656E
    customer_reg = 0x30
    rms_avg_len_reg_shadow = 0x1C
    rms_calc_number_of_averages = (100) <<7 | (126)
    

    slaveAddr = 96
    try:
        i2c.writeto_mem(slaveAddr,access_code_reg,customer_access_code.to_bytes(4, 'little'))
        i2c.writeto_mem(slaveAddr,rms_avg_len_reg_shadow,rms_calc_number_of_averages.to_bytes(4,'little'))
        i2c.writeto_mem(slaveAddr,customer_reg,b'\x00')
        
        try:
            xbee.transmit(coordinator_mac_addr64,'Config Success')
        except:
            pass
        pass        
    except:
        try:
            xbee.transmit(coordinator_mac_addr64,'Failed to config')
        except:
            pass        
        pass

def discover_coordinator(coordinator_mac_addr64, time_tracker):
    mac_addr64 = coordinator_mac_addr64
    if time_tracker.is_discover_coordinator_timer_expired() and mac_addr64 == None:
        time_tracker.set_discover_coordinator_timer()
        try:
            xbee_discover_list = xbee.discover()

            for device in xbee_discover_list:
                if "coordinator" == device["node_id"]:
                    mac_addr64 = device["sender_eui64"]
                    print("Coordinator discovered: {}".format(mac_addr64))
        except Exception as e:
            print("Discover Failure: {}".format(str(e)))

    return mac_addr64

def read_from_current_monitor(address_to_read):
    global coordinator_mac_addr64
    global i2c
    bytearrayIn = bytearray(4)
    slaveAddr = 96
    bytesValue ='\x00\x00\x00\x00'
        
    try:
        bytesValue = i2c.readfrom_mem(slaveAddr, address_to_read, 4)
        i2c.readfrom_mem_into(slaveAddr,address_to_read,bytearrayIn)
        
    except:
        try:
            xbee.transmit(coordinator_mac_addr64,'Failed to Read From reg {}'.format(address_to_read))
        except:
            pass        
        pass
    return bytearrayIn

def read_vrms_irms_avg():
    global coordinator_mac_addr64
    vrms = 122
    rms_reg = 0x26
    bytesValue = read_from_current_monitor(rms_reg)    
    testValueConvert = float(int(bytesValue[0]) + (int(bytesValue[1]) * 256))
    valueConvert =  ((testValueConvert / float(16880.0)) * float(vrms)) #normalized
    if valueConvert < 20.0:
        valueConvert = 0.0
    return valueConvert

def read_power_avg():
    average_reg = 0x28
    vrms = 120
    irms = 30

    bytesValue = read_from_current_monitor(average_reg)

    bytesString = ""
    for byte in bytesValue:
        bytesString += hex(byte)
    testValueConvert = float(int(bytesValue[0]) + (int(bytesValue[1]) * 256) ) 
    if(bytesValue[2] == 0x01):
        testValueConvert = testValueConvert * -1.0

    testValueConvert = testValueConvert * .2167 #normalized and offset
    if testValueConvert < 2.0 :
        testValueConvert = 0.0
    return testValueConvert

def get_sensor_payload():

    return '{},{}'.format(read_power_avg(),read_vrms_irms_avg())


def transmit_sensor_payload(state, coordinator_mac_addr64, time_tracker):
    if (
        time_tracker.is_transmit_sensor_payload_timer_expired()
        and coordinator_mac_addr64
    ):
        time_tracker.set_transmit_sensor_payload_timer()
        sensor_payload = None
        sensor_payload = get_sensor_payload()
        if sensor_payload:
            try:
                xbee.transmit(
                    coordinator_mac_addr64, "{},{}".format(state, sensor_payload)
                )
            except Exception as e:
                print("Transmission failure: {}".format(str(e)))


def periodic_run(state, coordinator_mac_addr64, time_tracker):
    if state == ON_STATE:
        red_pin.value(0)
        blue_pin.value(0)
        green_pin.value(0)
        relay_pin.value(1)
    elif state == OFF_STATE:
        red_pin.value(1)
        blue_pin.value(0)
        green_pin.value(0)
        relay_pin.value(0)

    transmit_sensor_payload(state, coordinator_mac_addr64, time_tracker)


def command_message_receiver_handler(state):
    next_state = state

    received_msg = xbee.receive()
    if received_msg:
        # Get the sender's 64-bit address and payload from the received message.
        sender_mac_addr = "".join(
            "{:02x}".format(x) for x in received_msg["sender_eui64"]
        )
        payload = received_msg["payload"].decode()
        print("Data received from {}: {}".format(sender_mac_addr, payload))

        if payload == "on":
            next_state = ON_STATE
        elif payload == "off":
            next_state = OFF_STATE

    return next_state




def is_timer_expired(current_time_ms, previous_time_ms, timeout):
    return (current_time_ms - previous_time_ms) > timeout


class TimeTracker:
    def __init__(self):
        self.current_time_ms = 0

        self.discover_coordinator_timer_ms = 0
        self.transmit_sensor_payload_timer_ms = 0
        self.button_debounce_timer_ms = 0

        self.discover_coordinator_timeout_ms = 10000
        self.transmit_sensor_payload_timeout_ms = 1000
        self.button_debounce_timeout_ms = 1000

    def set_current_time_ms(self):
        self.current_time_ms = time.ticks_ms()

    def set_discover_coordinator_timer(self):
        self.discover_coordinator_timer_ms = time.ticks_ms()

    def set_transmit_sensor_payload_timer(self):
        self.transmit_sensor_payload_timer_ms = time.ticks_ms()

    def set_button_debounce_timer(self):
        self.button_debounce_timer_ms = time.ticks_ms()

    def is_discover_coordinator_timer_expired(self):
        return is_timer_expired(
            self.current_time_ms,
            self.discover_coordinator_timer_ms,
            self.discover_coordinator_timeout_ms,
        )

    def is_transmit_sensor_payload_timer_expired(self):
        return is_timer_expired(
            self.current_time_ms,
            self.transmit_sensor_payload_timer_ms,
            self.transmit_sensor_payload_timeout_ms,
        )

    def is_button_debounce_timer_expired(self):
        return is_timer_expired(
            self.current_time_ms,
            self.button_debounce_timer_ms,
            self.button_debounce_timeout_ms,
        )


time_tracker = TimeTracker()
runOnce = True

while True:
    time_tracker.set_current_time_ms()
    coordinator_mac_addr64 = discover_coordinator(coordinator_mac_addr64, time_tracker)
    if(coordinator_mac_addr64 != None and runOnce == True):
        config_calc_number_of_averages()
        runOnce = False
    periodic_run(STATE, coordinator_mac_addr64, time_tracker)
    STATE = command_message_receiver_handler(STATE)
    STATE = button_handler(STATE, time_tracker)