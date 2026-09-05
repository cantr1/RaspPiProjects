#!/usr/bin/python3
"""
Simple program to take user input and blink an LED the requested times
"""
import RPi.GPIO as gp
from time import sleep

# Setup pin for output
gpio_pin = 21
gp.setmode(gp.BCM)
gp.setup(gpio_pin, gp.OUT)


print("blink.py\n'x' to exit...\n")
try:
    while True:
        x = input("Number of blinks: ").lower().strip()
        if x == "x":
            break
        for i in range(int(x)):
            gp.output(gpio_pin,1)
            sleep(0.3)
            gp.output(gpio_pin,0)
            sleep(0.3)
except KeyboardInterrupt:
    print("\nctrl+c - bye!")
finally:
    gp.cleanup()
