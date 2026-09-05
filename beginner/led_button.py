#!/usr/bin/python3
"""
Allows a person to click a button switch to power an LED
"""
import RPi.GPIO as gp
from time import sleep

gp.setmode(gp.BCM)

inPin=21
outPin=16
gp.setup(inPin,gp.IN)
gp.setup(outPin,gp.OUT)
try:
    while True:
        readVal=gp.input(inPin)
        if readVal == 1:
            gp.output(outPin,0)
        else:
            gp.output(outPin,1)
        sleep(0.1)
except KeyboardInterrupt:
    print("\nkeyboard interrupt - cleaning up")
finally:
    gp.cleanup()