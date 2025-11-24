import RPi.GPIO as GPIO
from time import sleep

GPIO.setmode(GPIO.BOARD)

# Setup GPIO Pin for LED
outPin=38
GPIO.setup(outPin,GPIO.OUT)
myPWM=GPIO.PWM(outPin,100)

# Setup pins for brightness
dimmer=11
GPIO.setup(dimmer,GPIO.IN,pull_up_down=GPIO.PUD_UP)
upper=16
GPIO.setup(upper,GPIO.IN,pull_up_down=GPIO.PUD_UP)

# Starting Cycle - Set's default brightness and value to be modified
brightness = 0
myPWM.start(brightness)

try:
    while True:
        dimVal = GPIO.input(dimmer)
        upVal = GPIO.input(upper)
        if dimVal == 0 and upVal == 0:
            sleep(0.2)
            print("BOTH BUTTONS PRESSED --- NO CHANGE")
        if dimVal == 0:
            sleep(0.2)
            if brightness == 0:
                pass
            else:
                brightness -= 20
            print("DOWN")
        if upVal == 0:
            sleep(0.2)
            if brightness == 100:
                pass
            else:
                brightness += 20
            print("UP")

        myPWM.ChangeDutyCycle(brightness)

except KeyboardInterrupt:
    GPIO.cleanup()