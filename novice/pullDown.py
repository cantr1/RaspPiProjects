import RPi.GPIO as GPIO
from time import sleep

GPIO.setmode(GPIO.BOARD)

inPin=32
outPin=38
GPIO.setup(inPin,GPIO.IN,pull_up_down=GPIO.PUD_UP)
GPIO.setup(outPin,GPIO.OUT)
delay=0.4
try:
    while True:
        readVal=GPIO.input(inPin)
        print(readVal)
        if readVal == 1:
            GPIO.output(outPin,0)
        else:
            GPIO.output(outPin,1)
        sleep(delay)
except KeyboardInterrupt:
    GPIO.cleanup()
