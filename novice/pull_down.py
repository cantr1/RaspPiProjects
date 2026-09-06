#!/usr/bin/python3
"""
Use of on board pull down resistor to use a push button switch
to turn off and on an LED.

If inPin reads 1, no connection to ground. 0, circuit is complete
i.e. button is pressed -> activate LED
"""
import RPi.GPIO as gp
from time import sleep

gp.setmode(gp.BCM)

# inPin reads vals, outpin controls V to LED
inPin=21
outPin=16

gp.setup(inPin,gp.IN,pull_up_down=gp.PUD_UP)
gp.setup(outPin,gp.OUT)

delay=0.4
try:
    while True:
        readVal=gp.input(inPin)
        print(readVal)
        if readVal == 1:
            gp.output(outPin,0)
        else:
            gp.output(outPin,1)
        sleep(delay)
except KeyboardInterrupt:
    print("\nctrl+c - bye")
finally:
    gp.cleanup()