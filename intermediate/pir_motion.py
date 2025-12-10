"""
This script uses a thermal sensor to detect motion
"""
import RPi.GPIO as GPIO
import time
GPIO.setmode(GPIO.BCM)

# Set vars for pins
motionPin=18
ledPin=21

# Setup pins
GPIO.setup(motionPin,GPIO.IN)
GPIO.setup(ledPin,GPIO.OUT)

time.sleep(10)

try:
    while True:
        motion=GPIO.input(motionPin)
        print(motion)
        time.sleep(0.01)
        if motion == 1:
            GPIO.output(ledPin,1)
        else:
            GPIO.output(ledPin,0)

except KeyboardInterrupt:
    GPIO.cleanup()
    print("\nGPIO Released...")