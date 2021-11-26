import xbee
import time
from machine import Pin

print("plug walk")

red_pin = Pin("D2", mode=Pin.OUT, value = 1)
blue_pin = Pin("D4", mode=Pin.OUT, value = 1)
green_pin = Pin("D3", mode=Pin.OUT, value = 1)

while True:
    red_pin.value(not red_pin.value())
    time.sleep(1)
    blue_pin.value(not blue_pin.value())
    time.sleep(1)
    green_pin.value(not green_pin.value())
    time.sleep(1)
