#!/usr/bin/python3
"""
Project that implements PWM to dim an LED
with button switches to increase / decrease brightness
"""
import RPi.GPIO as gp
from time import sleep

gp.setmode(gp.BCM)

# Setup gp Pin for LED
out_pin=16
gp.setup(out_pin,gp.OUT)
pwm_pin=gp.PWM(out_pin,100)

# Setup pins for brightness
dim_pin=26
gp.setup(dim_pin,gp.IN,pull_up_down=gp.PUD_UP)
bright_pin=13
gp.setup(bright_pin,gp.IN,pull_up_down=gp.PUD_UP)

# Starting Cycle - Set's default brightness and value to be modified
duty_cycle = 0
pwm_pin.start(duty_cycle)

try:
    while True:
        # read button presses - 0 = press
        dim_val = gp.input(dim_pin)
        bright_val = gp.input(bright_pin)

        if dim_val == 0 and bright_val == 0:
            sleep(0.2)
            print("BOTH BUTTONS PRESSED --- NO CHANGE")
        elif dim_val == 0:
            sleep(0.2)
            if duty_cycle == 0:
                pass
            else:
                duty_cycle -= 20
            print(duty_cycle)
        elif bright_val == 0:
            sleep(0.2)
            if duty_cycle == 100:
                pass
            else:
                duty_cycle += 20
            print(duty_cycle)

        pwm_pin.ChangeDutyCycle(duty_cycle)
except KeyboardInterrupt:
    print("\n")
finally:
    gp.cleanup()