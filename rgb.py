import RPi.GPIO as GPIO
from time import sleep

GPIO.setmode(GPIO.BOARD)

# Setup GPIO Pins for RGB LED
rPin=37
gPin=35
bPin=33
GPIO.setup(rPin,GPIO.OUT)
GPIO.setup(gPin,GPIO.OUT)
GPIO.setup(bPin,GPIO.OUT)

# Setup pins for input
rInput=15
gInput=13
bInput=11
GPIO.setup(rInput,GPIO.IN,pull_up_down=GPIO.PUD_UP)
GPIO.setup(gInput,GPIO.IN,pull_up_down=GPIO.PUD_UP)
GPIO.setup(bInput,GPIO.IN,pull_up_down=GPIO.PUD_UP)

try:
    while True:
        rVal = GPIO.input(rInput)
        gVal = GPIO.input(gInput)
        bVal = GPIO.input(bInput)
        if rVal == 0 and gVal == 0 and bVal == 0:
            print("ALL BUTTONS PRESSED --- NO CHANGE")
        if rVal == 0:
            sleep(0.2)
            GPIO.output(gPin, 0)
            GPIO.output(bPin,0)
            sleep(0.1)
            GPIO.output(rPin,1)
        if gVal == 0:
            sleep(0.2)
            GPIO.output(rPin, 0)
            GPIO.output(bPin,0)
            sleep(0.1)
            GPIO.output(gPin,1)
        if bVal == 0:
            sleep(0.2)
            GPIO.output(rPin, 0)
            GPIO.output(gPin,0)
            sleep(0.1)
            GPIO.output(bPin,1)

except KeyboardInterrupt:
    GPIO.output(rPin,0)
    GPIO.output(gPin,0)
    GPIO.output(bPin,0)
    GPIO.cleanup()
