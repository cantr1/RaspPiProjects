import RPi.GPIO as GPIO
import ADC0834
from time import sleep

GPIO.setmode(GPIO.BCM)
ADC0834.setup()

# Setup GPIO Pin for LED
outPin=20
GPIO.setup(outPin,GPIO.OUT)
myPWM=GPIO.PWM(outPin,100)

# Starting Cycle - Set's default brightness and value to be modified
brightness = 0
myPWM.start(brightness)

try:
    while True:
        analogVal=ADC0834.getResult(0)
        #print(analogVal)
        sleep(.2)
        myPWM.ChangeDutyCycle((analogVal * (100/255)))
except KeyboardInterrupt:
    GPIO.cleanup()
    print("\nGPIO exited cleanly...")