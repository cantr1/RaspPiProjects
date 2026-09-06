#!/usr/bin/python3
"""
Extension of the pull_down.py that creates a toggle switch
"""
import RPi.GPIO as gp
from time import sleep

gp.setmode(gp.BCM)

# inPin reads vals, outpin controls V to LED
inPin=26
outPin=16

gp.setup(inPin,gp.IN,pull_up_down=gp.PUD_UP)
gp.setup(outPin,gp.OUT)

try:
    led_on = False
    read_delay = 0.25
    while True:
        read_val = gp.input(inPin)
        if read_val == 0:
            if led_on:
                gp.output(outPin,0)
                led_on = False
            else:
                gp.output(outPin, 1)
                led_on = True
            sleep(read_delay)
except KeyboardInterrupt:
    print("\nctrl+c - bye")
finally:
    gp.cleanup()