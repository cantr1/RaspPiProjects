import RPi.GPIO as GPIO
from time import sleep

GPIO.setmode(GPIO.BOARD)

inPin=40
outPin=11
GPIO.setup(inPin,GPIO.IN)
GPIO.setup(outPin,GPIO.OUT)
try:
    while True:
        readVal=GPIO.input(inPin)
        if readVal == 1:
            GPIO.output(outPin,0)
        else:
            GPIO.output(outPin,1)
        sleep(0.1)
except KeyboardInterrupt:
    GPIO.cleanup()