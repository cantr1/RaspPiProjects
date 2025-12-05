import RPi.GPIO as GPIO
import ADC0834
from time import sleep

GPIO.setmode(GPIO.BCM)
ADC0834.setup()

# Setup GPIO Pin for LEDs
rPin=16
GPIO.setup(rPin,GPIO.OUT)
rPWM=GPIO.PWM(rPin,100)

gPin=20
GPIO.setup(gPin,GPIO.OUT)
gPWM=GPIO.PWM(gPin,100)

bPin=21
GPIO.setup(bPin,GPIO.OUT)
bPWM=GPIO.PWM(bPin,100)

# Starting Cycle - Set's default brightness and value to be modified
brightness = 0
rPWM.start(brightness)
gPWM.start(brightness)
bPWM.start(brightness)

try:
    while True:
        rVal=ADC0834.getResult(0)
        gVal=ADC0834.getResult(1)
        bVal=ADC0834.getResult(2)
        #print(analogVal)
        sleep(.1)
        rPWM.ChangeDutyCycle((rVal * (100/255)))
        gPWM.ChangeDutyCycle((gVal * (100/255)))
        bPWM.ChangeDutyCycle((bVal * (100/255)))
except KeyboardInterrupt:
    GPIO.cleanup()
    print("\nGPIO exited cleanly...")