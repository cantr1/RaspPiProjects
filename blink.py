#!/usr/bin/python3
import RPi.GPIO as GPIO
from time import sleep

GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.OUT)


print("blink.py\n'EXIT' to exit...\n")

while True:
    x = input("Number of blinks: ")
    if x == "EXIT":
        GPIO.cleanup()
        exit(0)
    for i in range(int(x)):
        GPIO.output(11,1)
        sleep(0.3)
        GPIO.output(11,0)
        sleep(0.3)
