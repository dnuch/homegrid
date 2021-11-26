DIO1

Button click
DIO13 (controls button)

if DIO14 is unactive then activate on single button click
if DIO14 is active then deactivate on single button click

long press -> soft reset the XBee

coordinator send
"plug on"
Relay on; GPIO 14 active
DIO2 unactive RED 
DIO3 unactive GREEN
DIO4 unactive BLUE


"plug off"
Relay off; GPIO 14 deactived
DIO2 active RED 
DIO3 unactive GREEN
DIO4 unactive BLUE

test xbee
0013a20041dae125,off
0013a20041dae125,on

plug on bench
0013a20041cc5773,off
0013a20041cc5773,on
