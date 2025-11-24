import RPi.GPIO as GPIO
from time import sleep

GPIO.setmode(GPIO.BOARD)

inPin=32
outPin=38
GPIO.setup(inPin,GPIO.IN,pull_up_down=GPIO.PUD_UP)
GPIO.setup(outPin,GPIO.OUT)
delay=0.4
LED=False
try:
    while True:
        readVal=GPIO.input(inPin)
        print(f"Read Value: {readVal}")
        if readVal == 0:
            if LED:
                GPIO.output(outPin,1)
                LED = False
            else:
                GPIO.output(outPin,0)
                LED = True
        sleep(delay)

except KeyboardInterrupt:
    GPIO.cleanup()