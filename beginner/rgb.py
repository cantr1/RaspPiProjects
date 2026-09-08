#!/usr/bin/python3
"""
Project to control the colors of an LED
with three button switches
"""
import RPi.GPIO as gp
from time import sleep

gp.setmode(gp.BCM)

# === Output ===
# Setup gp Pins for RGB LED
red_pin=13
green_pin=19
blue_pin=26
gp.setup(red_pin,gp.OUT)
gp.setup(green_pin,gp.OUT)
gp.setup(blue_pin,gp.OUT)
red_pwm = gp.PWM(red_pin, 100)
green_pwm = gp.PWM(green_pin, 100)
blue_pwm = gp.PWM(blue_pin, 100)

# Set duty cycle trackers for each pin
led_red_duty = 0
led_green_duty = 0
led_blue_duty = 0

# Start each pin
red_pwm.start(led_red_duty)
green_pwm.start(led_green_duty)
blue_pwm.start(led_blue_duty)

# === Input ===
# Setup pins for input
red_input=17
green_input=27
blue_input=22
gp.setup(red_input,gp.IN,pull_up_down=gp.PUD_UP)
gp.setup(green_input,gp.IN,pull_up_down=gp.PUD_UP)
gp.setup(blue_input,gp.IN,pull_up_down=gp.PUD_UP)

try:
    while True:
        red_button = gp.input(red_input)
        green_button = gp.input(green_input)
        blue_button = gp.input(blue_input)

        if red_button == 0 and green_button == 0 and blue_button == 0:
            print("ALL BUTTONS PRESSED --- NO CHANGE")
        if red_button == 0:
            sleep(0.2)
            if led_red_duty == 100:
                led_red_duty = 0
            else:
                led_red_duty += 20
            red_pwm.ChangeDutyCycle(led_red_duty)
            sleep(0.1)
        elif green_button == 0:
            sleep(0.2)
            if led_green_duty >= 100:
                led_green_duty = 0
            else:
                led_green_duty += 20
            green_pwm.ChangeDutyCycle(led_green_duty)
            sleep(0.1)
        elif blue_button == 0:
            sleep(0.2)
            if led_blue_duty >= 100:
                led_blue_duty = 0
            else:
                led_blue_duty += 20
            blue_pwm.ChangeDutyCycle(led_blue_duty)
            sleep(0.1)
except KeyboardInterrupt:
    print("\n")
finally:
    gp.output(red_pin,0)
    gp.output(green_pin,0)
    gp.output(blue_pin,0)
    gp.cleanup()
